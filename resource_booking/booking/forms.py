from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import BookingRequest, Resource
from django.forms import DateTimeInput


class BookingRequestForm(forms.ModelForm):
    """
    Form used for users to submit a new booking request.
    It links directly to the BookingRequest model for easy data handling.
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
        # Add cost data to resource options for client-side display
        resource_field = self.fields['resource']
        resource_field.queryset = Resource.objects.filter(is_available=True)
        
        # Customize the choices to include cost as data attribute
        choices = []
        for resource in Resource.objects.filter(is_available=True):
            choices.append((resource.id, f"{resource.name} - KES {resource.cost}" if resource.cost > 0 else resource.name))
        resource_field.choices = choices


class UserRegistrationForm(UserCreationForm):
    """
    Custom user registration form extending Django's UserCreationForm.
    Adds email field for more complete user registration.
    """
    email = forms.EmailField(
        required=True,
        help_text='A valid email address is required.',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

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
