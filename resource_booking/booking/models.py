from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model() 

class Resource(models.Model):
    
    ROOM = 'ROOM'
    EQUIP = 'EQUIP'
    LAB = 'LAB'
    VEH = 'VEH'
    OTHER = 'OTHER'
    
    RESOURCE_CHOICES = [
        (ROOM, 'Room/Lecture Hall'),
        (EQUIP, 'Equipment (e.g., Projector, Camera)'),
        (LAB, 'Laboratory/Specialized Space'),
        (VEH, 'Vehicle'),
        (OTHER, 'Other'),
    ]

    name = models.CharField(
        max_length=100, 
        unique=True, 
    )
    type = models.CharField(
        max_length=5,
        choices=RESOURCE_CHOICES,
        default=OTHER,
    )
    description = models.TextField(blank=True)
    
    image_url = models.URLField( 
        max_length=500, 
        blank=True, 
        null=True, 
    )
    
    quantity_available = models.PositiveIntegerField(
        default=1, 
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )
    is_available = models.BooleanField(
        default=True, 
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Bookable Resource"
        verbose_name_plural = "Bookable Resources"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})" 

class BookingRequest(models.Model):
    
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_ARCHIVED = 'ARCHIVED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    PAYMENT_NOT_REQUIRED = 'NOT_REQUIRED'
    PAYMENT_PENDING = 'PENDING'
    PAYMENT_PAID = 'PAID'
    PAYMENT_FAILED = 'FAILED'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_NOT_REQUIRED, 'No Payment Required'),
        (PAYMENT_PENDING, 'Payment Pending'),
        (PAYMENT_PAID, 'Payment Completed'),
        (PAYMENT_FAILED, 'Payment Failed'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_bookings', 
    )
    
    resource = models.ForeignKey(
        Resource, 
        on_delete=models.CASCADE,
        related_name='resource_bookings', 
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    purpose = models.TextField(
        blank=True, 
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING, 
    )
    
    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_NOT_REQUIRED,
    )
    
    requested_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        verbose_name = "Booking Request"
        verbose_name_plural = "Booking Requests"

    def __str__(self):
        return f"{self.resource.name} booked by {self.user.username} ({self.status})"