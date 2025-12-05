from django.urls import path
from .views import (
    LandingView,
    HomeView,
    BookingCreateView,
    RegisterView,
    my_bookings_dashboard,
)
from .views import admin_pending_requests, resource_list

app_name = 'booking'

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),

    path('home/', HomeView.as_view(), name='home'),
    
    path('register/', RegisterView.as_view(), name='register'),
    
    path('new/', BookingCreateView.as_view(), name='new_booking'),

    path('my_bookings_dashboard/', my_bookings_dashboard, name='my_bookings_dashboard'),

    path('admin/pending/', admin_pending_requests, name='admin_pending_dashboard'),
    path('resources/', resource_list, name='resource_list'),
]