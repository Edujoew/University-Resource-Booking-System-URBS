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
    
    # Payment app URLs
    path('payments/', include('payments.urls')), # <-- CHANGED FROM 'api/payments/'
    
    # Booking app URLs
    path('', include('booking.urls')),
    
    
]