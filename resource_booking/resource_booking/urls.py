"""
URL configuration for resource_booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
# resource_booking/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Built-in Auth URLs (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')), 
    
    # --- CRITICAL FIX ---
    # The 'payments' app contains the user-facing redirect (initiate_mpesa_payment)
    # and the system-facing callback (mpesa_callback). 
    # Use a simple prefix for easier redirection.
    path('payments/', include('payments.urls')), # <-- CHANGED FROM 'api/payments/'
    
    # Booking app URLs (should be last, as it includes the root path '')
    path('', include('booking.urls')),
]