# booking/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
# Import ValidationError explicitly from forms
from django.forms import DateTimeInput, ValidationError 
from .models import BookingRequest, Resource


# --- FORM TITLE: Resource Booking Request Form (Issue 5 & 6) ---
class BookingRequestForm(forms.ModelForm):
    """
    Form used for users to submit a new booking request.
    
    This form handles:
    1. Displaying available resources with cost information (Issue 5).
    2. Implementing the core validation logic to prevent time conflicts 
       with PENDING or APPROVED bookings (Issue 6).
    """
    class Meta:
        model = BookingRequest
        fields = ['resource', 'start_time', 'end_time']
       
        
        widgets = {
            'resource': forms.Select(
                attrs={'class': 'form-control', 'id': 'resourceSelect'}
            ),
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',
                    'placeholder': 'YYYY-MM-DD HH:MM'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',
                    'placeholder': 'YYYY-MM-DD HH:MM'
                },
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter resources to show only available ones (Issue 5)
        resource_field = self.fields['resource']
        resource_field.queryset = Resource.objects.filter(is_available=True)
        
        # Customize the choices to include cost (Issue 5 enhancement)
        choices = []
        for resource in Resource.objects.filter(is_available=True):
            choices.append((resource.id, f"{resource.name} - KES {resource.cost}" if resource.cost > 0 else resource.name))
        resource_field.choices = choices

    
    def clean(self):
        """
        Implements validation for time slot conflicts (Issue 6) and basic time order checks.
        """
        cleaned_data = super().clean()
        
        resource = cleaned_data.get('resource')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # 1. Sanity Check: Ensure all required fields are available for validation
        if not all([resource, start_time, end_time]):
            return cleaned_data # Let individual field errors handle missing data

        # 2. Time Order Check: Ensure start_time is before end_time
        if start_time >= end_time:
            raise ValidationError(
                "The end time must be later than the start time."
            )

        # 3. Conflict Check (Core Overlap Logic for Issue 6)
        
        # Define the statuses that indicate a resource is currently occupied
        OCCUPIED_STATUSES = ['APPROVED', 'PENDING']
        
        # Query the database for any booking that conflicts with the new request:
        conflicting_bookings = BookingRequest.objects.filter(
            # A. Filter by the same resource
            resource=resource,
            
            # B. Filter by occupied status (Approved or Pending)
            status__in=OCCUPIED_STATUSES,
            
            # C. Filter by temporal overlap (The key logic):
            # The new start time is before the existing end time, AND
            # The new end time is after the existing start time.
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if conflicting_bookings.exists():
            # Conflict detected! Stop submission and inform the user.
            conflict_id = conflicting_bookings.first().pk 
            
            raise ValidationError(
                f"Conflict detected! The resource '{resource.name}' is already booked during this time. "
                f"See existing booking #{conflict_id}."
            )
            
        return cleaned_data


# --- FORM TITLE: User Registration Form (Issue 3) ---
class UserRegistrationForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm to include the 'email' field,
    and ensures the email is unique upon registration (Issue 3).
    """
    email = forms.EmailField(
        required=True,
        help_text='A valid email address is required.',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    
    class Meta(UserCreationForm.Meta):
        # Adds the email field to the list of fields from UserCreationForm
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        """Ensure email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def save(self, commit=True):
        """Save the user with the email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user