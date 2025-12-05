
from django.urls import path
from .views import (
    LandingView,
    HomeView,
    BookingCreateView,
    RegisterView,
    MyBookingsView,
)

app_name = 'booking'

urlpatterns = [
    # 1. NEW: Root URL now points to the public LandingView
    path('', LandingView.as_view(), name='landing'),

    # Issue 2: Homepage
    path('home/', HomeView.as_view(), name='home'),
    
    # Issue 3: User Registration
    path('register/', RegisterView.as_view(), name='register'),
    
    # Issue 5: Booking Submission
    path('new/', BookingCreateView.as_view(), name='new_booking'),

    # issue7: View User's Bookings
    path('my_bookings_dashboard/', MyBookingsView.as_view(), name='my_bookings_dashboard'),
]