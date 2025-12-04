# booking/models.py

from django.db import models
from django.contrib.auth import get_user_model # Use get_user_model for flexibility

# Get the active User model (Django's default or a custom one)
User = get_user_model() 

# --- Model 1: Resource ---
class Resource(models.Model):
    """
    Model to represent a bookable resource (room, equipment, etc.).
    """
    
    RESOURCE_CHOICES = [
        ('ROOM', 'Room/Lecture Hall'),
        ('EQUIP', 'Equipment (e.g., Projector, Camera)'),
        ('LAB', 'Laboratory/Specialized Space'),
        ('VEH', 'Vehicle'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="A unique, identifiable name for the resource."
    )
    type = models.CharField(
        max_length=5,
        choices=RESOURCE_CHOICES,
        default='OTHER',
        help_text="The category of the resource (e.g., Room, Equipment)."
    )
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(
        default=1, 
        help_text="Maximum number of people or concurrent uses allowed."
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Cost to book this resource (0 for free)."
    )
    is_available = models.BooleanField(
        default=True, 
        help_text="Indicates if the resource is currently active and bookable."
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Bookable Resource"
        verbose_name_plural = "Bookable Resources"

    def __str__(self):
        # Displays the name and the friendly type (e.g., "Room 305 (Room/Lecture Hall)")
        return f"{self.name} ({self.get_type_display()})" 

# --- Model 2: BookingRequest ---
class BookingRequest(models.Model):
    """
    Model to track individual booking requests made by users.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_bookings', # Changed related_name for clarity
        help_text="The user who submitted this booking request."
    )
    
    resource = models.ForeignKey(
        Resource, 
        on_delete=models.CASCADE,
        related_name='resource_bookings', # Changed related_name for clarity
        help_text="The resource or equipment being requested."
    )
    
    start_time = models.DateTimeField(help_text="The start date and time of the booking.")
    end_time = models.DateTimeField(help_text="The end date and time of the booking.")
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING', 
        help_text="The current approval status of the booking request."
    )
    
    PAYMENT_STATUS = [
        ('NOT_REQUIRED', 'No Payment Required'),
        ('PENDING', 'Payment Pending'),
        ('PAID', 'Payment Completed'),
        ('FAILED', 'Payment Failed'),
    ]
    
    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS,
        default='NOT_REQUIRED',
        help_text="Payment status for this booking."
    )
    
    requested_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        verbose_name = "Booking Request"
        verbose_name_plural = "Booking Requests"

    def __str__(self):
        # Example: "Lecture hall 33 booked by edwardsJohn (PENDING)"
        return f"{self.resource.name} booked by {self.user.username} ({self.status})"