from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Sum
from .models import BookingRequest, Resource, UserMessage

class BookingRequestForm(forms.ModelForm):
    
    class Meta:
        model = BookingRequest
        fields = ['resource', 'start_time', 'end_time', 'purpose', 'status']
        
        labels = {
            'resource': 'Resource',
            'purpose': 'Purpose of Booking',
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
            'purpose': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
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

        # Set purpose as required by default for new bookings
        self.fields['purpose'].required = True
        
        if is_admin:
            self.fields['resource'].disabled = True
            self.fields['start_time'].disabled = True
            self.fields['end_time'].disabled = True
            self.fields['purpose'].disabled = True
            self.fields['status'].required = True
            # Admin doesn't need to provide purpose when reviewing
            self.fields['purpose'].required = False
            
        elif is_owner:
            self.fields['status'].disabled = True
            self.fields['status'].required = False
            
            if self.instance and self.instance.status != 'PENDING':
                self.fields['resource'].disabled = True
                self.fields['start_time'].disabled = True
                self.fields['end_time'].disabled = True
                self.fields['purpose'].disabled = True
                self.fields['purpose'].required = False
        
        # Cleanup requirements for all disabled fields
        if self.fields.get('resource') and self.fields['resource'].disabled:
            self.fields['resource'].required = False
        if self.fields.get('start_time') and self.fields['start_time'].disabled:
            self.fields['start_time'].required = False
        if self.fields.get('end_time') and self.fields['end_time'].disabled:
            self.fields['end_time'].required = False
        if self.fields.get('purpose') and self.fields['purpose'].disabled:
            self.fields['purpose'].required = False

    
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

        
        booked_quantity = conflicting_bookings.count()
        
        available_quantity = resource.quantity if resource else 0

        if booked_quantity >= available_quantity:
            
            raise ValidationError(
                f"The resource '{resource.name}' is fully booked ({booked_quantity} of {available_quantity} units reserved) "
                f"between {start_time.strftime('%Y-%m-%d %H:%M')} and {end_time.strftime('%Y-%m-%d %H:%M')}."
            )
            
        return cleaned_data


class ResourceCreationForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'type', 'description', 'image_url', 'cost', 'quantity', 'is_available']
        labels = {
            'quantity': 'Quantity',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unique Resource Name'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed description and use case'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste Image URL (optional)'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    is_staff = forms.BooleanField(
        required=False, 
        label='Register as Staff?',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email', 'is_staff',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = self.cleaned_data.get('is_staff', False) 
        if commit:
            user.save()
        return user


class UserMessageForm(forms.ModelForm):
    
    class Meta:
        model = UserMessage
        
        fields = ['subject', 'body']
        
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Message Subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your message content here...'}),
        }