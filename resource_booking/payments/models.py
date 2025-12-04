from django.db import models
from django.contrib.auth.models import User
from booking.models import BookingRequest


class MpesaTransaction(models.Model):
    """Model to store M-Pesa transaction details."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(BookingRequest, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_reference = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} - {self.status}"

    class Meta:
        verbose_name = "M-Pesa Transaction"
        verbose_name_plural = "M-Pesa Transactions"
        ordering = ['-created_at']
