from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import Appliance, EnergyUsage, DeviceSchedule, Alert, DeviceFault, FaultAssignment, Profile
from .forms import HomeownerTechnicianRegistrationForm
from .forms import HomeownerTechnicianRegistrationForm

def is_admin(user):
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'Admin')

def is_technician(user):
    return hasattr(user, 'profile') and user.profile.role == 'Technician'

def home(request):
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_dashboard')
        elif is_technician(request.user):
            return redirect('technician_dashboard')
        return redirect('homeowner_dashboard')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = HomeownerTechnicianRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Get role from form
            role = form.cleaned_data.get('role')
            # Set profile role based on selection
            profile = user.profile
            profile.role = role
            profile.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = HomeownerTechnicianRegistrationForm()
    return render(request, 'dashboard/register.html', {'form': form})

@login_required
def homeowner_dashboard(request):
    from .patterns import EnergyManagementSystem
    from django.db.models import Sum
    from datetime import datetime, timedelta
    
    appliances = request.user.appliances.all()
    alerts = request.user.alerts.filter(is_read=False)
    fault_reports = DeviceFault.objects.filter(appliance__homeowner=request.user).order_by('-reported_at')
    unresolved_faults = fault_reports.filter(is_resolved=False).count()
    resolved_faults = fault_reports.filter(is_resolved=True).count()
    ems = EnergyManagementSystem()
    total_cost = EnergyUsage.objects.filter(appliance__homeowner=request.user).aggregate(Sum('cost'))['cost__sum'] or 0.0
    
    # Get last 7 days of data
    today = datetime.now().date()
    daily_labels = []
    daily_data = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_labels.append(date.strftime('%a'))
        
        # Get total energy consumption for this day
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        day_usage = EnergyUsage.objects.filter(
            appliance__homeowner=request.user,
            timestamp__range=(day_start, day_end)
        ).aggregate(Sum('energy_consumed'))['energy_consumed__sum'] or 0.0
        
        daily_data.append(round(day_usage, 2))
    
    appliance_labels = [app.name for app in appliances]
    appliance_data = []
    for app in appliances:
        total_usage = EnergyUsage.objects.filter(appliance=app).aggregate(Sum('energy_consumed'))['energy_consumed__sum'] or 0.0
        appliance_data.append(round(total_usage, 2))
    
    # If no appliances, provide sample data for demo
    if not appliances:
        appliance_labels = ['No Appliances']
        appliance_data = [0]
    
    context = {
        'appliances': appliances,
        'alerts': alerts,
        'fault_reports': fault_reports,
        'unresolved_faults': unresolved_faults,
        'resolved_faults': resolved_faults,
        'total_cost': round(total_cost, 2),
        'system_status': ems.system_status,
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'appliance_labels': appliance_labels,
        'appliance_data': appliance_data,
    }
    return render(request, 'dashboard/homeowner_dashboard.html', context)

@login_required
@user_passes_test(is_technician)
def technician_dashboard(request):
    # Section 2.2: Technician manages faults
    assigned_faults = FaultAssignment.objects.filter(technician=request.user, fault__is_resolved=False)
    unassigned_faults = DeviceFault.objects.filter(is_resolved=False, assignment__isnull=True)
    resolved_faults = FaultAssignment.objects.filter(technician=request.user, fault__is_resolved=True).order_by('-fault__reported_at')[:10]
    
    context = {
        'assigned_faults': assigned_faults,
        'unassigned_faults': unassigned_faults,
        'resolved_faults': resolved_faults,
    }
    return render(request, 'dashboard/technician_dashboard.html', context)

@login_required
@user_passes_test(is_technician)
def assign_fault(request, fault_id):
    fault = get_object_or_404(DeviceFault, id=fault_id, is_resolved=False)
    if request.method == 'POST':
        assignment, created = FaultAssignment.objects.get_or_create(
            fault=fault,
            defaults={'technician': request.user}
        )
        if not created:
            assignment.technician = request.user
            assignment.save()
        messages.success(request, f"Fault on {fault.appliance.name} assigned to you.")
    return redirect('technician_dashboard')

@login_required
def resolve_fault(request, fault_id):
    fault = get_object_or_404(DeviceFault, id=fault_id)
    if request.method == 'POST':
        notes = request.POST.get('notes')
        fault.is_resolved = True
        fault.save()
        
        # Update assignment if exists
        if hasattr(fault, 'assignment'):
            assignment = fault.assignment
            assignment.resolution_notes = notes
            assignment.save()
            
        messages.success(request, f"Fault on {fault.appliance.name} resolved.")
    return redirect('technician_dashboard')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Separate homeowners and technicians
    homeowners = User.objects.filter(is_superuser=False, profile__role='Homeowner')
    technicians = User.objects.filter(is_superuser=False, profile__role='Technician')
    
    # Add fault counts to technicians
    for technician in technicians:
        technician.assigned_faults_count = technician.fault_assignments.filter(fault__is_resolved=False).count()
        technician.resolved_faults_count = technician.fault_assignments.filter(fault__is_resolved=True).count()
    
    total_system_usage = EnergyUsage.objects.aggregate(Sum('energy_consumed'))['energy_consumed__sum'] or 0.0
    all_faults = DeviceFault.objects.all().order_by('-reported_at')
    
    context = {
        'homeowners': homeowners,
        'technicians': technicians,
        'total_system_usage': round(total_system_usage, 2),
        'all_faults': all_faults,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def add_appliance(request):
    from .patterns import ApplianceFactory
    if request.method == 'POST':
        name = request.POST.get('name')
        app_type = request.POST.get('appliance_type')
        ApplianceFactory.create_appliance(app_type, name, request.user)
        messages.success(request, f"{name} added successfully!")
    return redirect('homeowner_dashboard')

@login_required
def toggle_appliance(request, appliance_id):
    from .patterns import EnergyManagementSystem
    appliance = get_object_or_404(Appliance, id=appliance_id, homeowner=request.user)
    if appliance.is_on:
        appliance.turn_off()
        ems = EnergyManagementSystem()
        ems.record_usage_and_check_threshold(appliance, usage_kwh=6.0)
    else:
        appliance.turn_on()
    return redirect('homeowner_dashboard')

@login_required
def schedule_appliance(request):
    if request.method == 'POST':
        appliance_id = request.POST.get('appliance_id')
        action = request.POST.get('action')
        scheduled_time = request.POST.get('scheduled_time')
        appliance = get_object_or_404(Appliance, id=appliance_id, homeowner=request.user)
        # Parse incoming datetime-local string and store it as UTC time
        dt = None
        if scheduled_time:
            dt = parse_datetime(scheduled_time)
            if dt is None:
                messages.error(request, "Invalid scheduled time format.")
                return redirect('homeowner_dashboard')
            if timezone.is_naive(dt):
                local_tz = datetime.now().astimezone().tzinfo
                dt = dt.replace(tzinfo=local_tz).astimezone(timezone.get_default_timezone())
        DeviceSchedule.objects.create(appliance=appliance, action=action, scheduled_time=dt)
        messages.success(request, f"Schedule set for {appliance.name}!")
    return redirect('homeowner_dashboard')

@login_required
def report_fault(request):
    if request.method == 'POST':
        appliance_id = request.POST.get('appliance_id')
        description = request.POST.get('description')

        appliance = get_object_or_404(
            Appliance,
            id=appliance_id,
            homeowner=request.user
        )

        DeviceFault.objects.create(
            appliance=appliance,
            description=description
        )

        messages.success(request, "Fault reported successfully!")

    return redirect('homeowner_dashboard')
