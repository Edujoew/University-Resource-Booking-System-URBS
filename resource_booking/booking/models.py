from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum, Q


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
    
    quantity = models.PositiveIntegerField(
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
        permissions = [
            ("can_create_resource", "Can create new resources"),
            ("can_delete_resource", "Can delete existing resources"),
        ]


    def __str__(self):
        return f"{self.name} ({self.get_type_display()})" 

    def get_currently_booked_quantity(self, start_time, end_time, exclude_booking_pk=None):
        
        conflicts = self.resource_bookings.filter(
            Q(status=BookingRequest.STATUS_APPROVED) | Q(status=BookingRequest.STATUS_PENDING),
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if exclude_booking_pk:
            conflicts = conflicts.exclude(pk=exclude_booking_pk)
            
        return conflicts.count()

    def get_available_quantity_at_time(self, start_time, end_time):
        booked_count = self.get_currently_booked_quantity(start_time, end_time)
        return self.quantity - booked_count

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

    purpose = models.TextField()
    
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
        permissions = [
            ("can_review_booking", "Can approve or reject pending bookings"),
        ]

    def __str__(self):
        return f"{self.resource.name} booked by {self.user.username} ({self.status})"


class UserMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}: {self.subject}"