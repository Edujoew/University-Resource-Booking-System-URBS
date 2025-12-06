from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import BookingRequest, Resource

class BookingRequestForm(forms.ModelForm):
    
    class Meta:
        model = BookingRequest
        fields = ['resource', 'start_time', 'end_time', 'status']
        
        labels = {
            'resource': 'Resource'
        }
        
        widgets = {
            'resource': forms.Select(
                attrs={'class': 'form-select', 'id': 'resourceSelect'}
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
            'status': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('is_admin', False)
        is_owner = kwargs.pop('is_owner', False)
        
        super().__init__(*args, **kwargs)
        
        resource_field = self.fields['resource']
        resource_field.queryset = Resource.objects.filter(is_available=True)
        
        choices = []
        for resource in Resource.objects.filter(is_available=True):
            label = f"{resource.name} - KES {resource.cost:.2f}" if resource.cost > 0 else resource.name
            choices.append((resource.id, label))
        
        resource_field.choices = choices
        
        if is_admin:
            self.fields['resource'].disabled = True
            self.fields['start_time'].disabled = True
            self.fields['end_time'].disabled = True
            self.fields['status'].required = True
            
        elif is_owner:
            self.fields['status'].disabled = True
            self.fields['status'].required = False
            
            if self.instance and self.instance.status != 'PENDING':
                self.fields['resource'].disabled = True
                self.fields['start_time'].disabled = True
                self.fields['end_time'].disabled = True
        
        if self.fields['resource'].disabled:
            self.fields['resource'].required = False
        if self.fields['start_time'].disabled:
            self.fields['start_time'].required = False
        if self.fields['end_time'].disabled:
            self.fields['end_time'].required = False

    
    def clean(self):
        
        cleaned_data = super().clean()
        
        resource = cleaned_data.get('resource')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if not resource and self.instance and self.instance.resource:
            resource = self.instance.resource
            cleaned_data['resource'] = resource
            
        if not start_time and self.instance and self.instance.start_time:
            start_time = self.instance.start_time
            cleaned_data['start_time'] = start_time
            
        if not end_time and self.instance and self.instance.end_time:
            end_time = self.instance.end_time
            cleaned_data['end_time'] = end_time

        
        if not all([resource, start_time, end_time]):
            return cleaned_data 

        
        if start_time >= end_time:
            raise ValidationError(
                'End time must be after start time.'
            )

        
        OCCUPIED_STATUSES = ['APPROVED', 'PENDING']
        
        
        conflicting_bookings = BookingRequest.objects.filter(
            
            resource=resource,
            
            status__in=OCCUPIED_STATUSES,
            
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        
        if self.instance and self.instance.pk:
            conflicting_bookings = conflicting_bookings.exclude(pk=self.instance.pk)

        if conflicting_bookings.exists():
            
            conflict_id = conflicting_bookings.first().pk 
            
            raise ValidationError(
                f"Conflict detected! The resource '{resource.name}' is already booked during this time. "
                f"See existing booking #{conflict_id}."
            )
            
        return cleaned_data


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text='A valid email address is required.',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user