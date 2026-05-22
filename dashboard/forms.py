from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class HomeownerTechnicianRegistrationForm(UserCreationForm):
    """Custom registration form for Homeowners and Technicians only"""
    
    ROLE_CHOICES = (
        ('Homeowner', 'Homeowner'),
        ('Technician', 'Technician'),
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select,
        label='Register as',
        initial='Homeowner'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help text from password fields
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].help_text = None
        
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
        
        # Make email optional but recommended
        self.fields['email'].required = False
