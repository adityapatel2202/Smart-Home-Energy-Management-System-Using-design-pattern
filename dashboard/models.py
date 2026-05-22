from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Extends the default User model to include specific roles and pricing plans.
    """
    ROLE_CHOICES = (
        ('Homeowner', 'Homeowner'),
        ('Admin', 'Admin'),
        ('Technician', 'Technician'),
    )
    PRICING_CHOICES = (
        ('Standard', 'Standard Flat Rate'),
        ('Peak-Hour', 'Peak-Hour Pricing'),
        ('Renewable', 'Renewable Energy Discount'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Homeowner')
    pricing_plan = models.CharField(max_length=20, choices=PRICING_CHOICES, default='Standard')
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class DeviceFault(models.Model):
    """
    Represents a technical issue with an appliance.
    """
    appliance = models.ForeignKey('Appliance', on_delete=models.CASCADE, related_name='faults')
    description = models.TextField()
    reported_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Fault on {self.appliance.name}: {self.description[:20]}..."

class FaultAssignment(models.Model):
    """
    Assigns a fault to a technician for repair.
    """
    fault = models.OneToOneField(DeviceFault, on_delete=models.CASCADE, related_name='assignment')
    technician = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__role': 'Technician'}, related_name='fault_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Assignment: {self.fault} to {self.technician.username}"

class Appliance(models.Model):
    """
    Represents devices that can be monitored and controlled.
    """
    name = models.CharField(max_length=100)
    appliance_type = models.CharField(max_length=50) # e.g., AC, Light, Fridge
    power_rating = models.FloatField(help_text="Power rating in kW")
    is_on = models.BooleanField(default=False)
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appliances')
    created_at = models.DateTimeField(auto_now_add=True)

    def turn_on(self):
        self.is_on = True
        self.save()

    def turn_off(self):
        self.is_on = False
        self.save()

    def __str__(self):
        return f"{self.name} ({self.appliance_type})"

class EnergyUsage(models.Model):
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, related_name='usages')
    timestamp = models.DateTimeField(auto_now_add=True)
    energy_consumed = models.FloatField()
    cost = models.FloatField()

class DeviceSchedule(models.Model):
    ACTION_CHOICES = (('ON', 'Turn On'), ('OFF', 'Turn Off'))
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)
    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    scheduled_time = models.DateTimeField()
    is_executed = models.BooleanField(default=False)

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

