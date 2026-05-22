import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shems_project.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Profile

def create_user(username, password, role, is_superuser=False):
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password=password, email=f"{username}@example.com")
        user.is_staff = is_superuser
        user.is_superuser = is_superuser
        user.save()
        
        # Profile is created by signal, just update the role
        profile = user.profile
        profile.role = role
        profile.save()
        print(f"User {username} created as {role}")
    else:
        user = User.objects.get(username=username)
        profile = user.profile
        profile.role = role
        profile.save()
        print(f"User {username} already exists, role updated to {role}")

# Create Admin
create_user('admin', 'admin123', 'Admin', is_superuser=True)

# Create Homeowner
create_user('homeowner', 'home123', 'Homeowner')

# Create Technician
create_user('technician', 'tech123', 'Technician')
