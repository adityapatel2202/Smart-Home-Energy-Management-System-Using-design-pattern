from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Dashboards
    path('homeowner/', views.homeowner_dashboard, name='homeowner_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('technician/', views.technician_dashboard, name='technician_dashboard'),
    
    # Actions
    path('add_appliance/', views.add_appliance, name='add_appliance'),
    path('toggle_appliance/<int:appliance_id>/', views.toggle_appliance, name='toggle_appliance'),
    path('schedule_appliance/', views.schedule_appliance, name='schedule_appliance'),
    path('report_fault/', views.report_fault, name='report_fault'),
    path('assign_fault/<int:fault_id>/', views.assign_fault, name='assign_fault'),
    path('resolve_fault/<int:fault_id>/', views.resolve_fault, name='resolve_fault'),

]
