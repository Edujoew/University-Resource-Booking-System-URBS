
from django.urls import path
from .views import HomeView, BookingCreateView, RegisterView

app_name = 'booking'

urlpatterns = [
    # Issue 2: Homepage
    path('', HomeView.as_view(), name='home'),
    
    # Issue 3: User Registration
    path('register/', RegisterView.as_view(), name='register'),
    
    # Issue 5: Booking Submission
    path('new/', BookingCreateView.as_view(), name='new_booking'),
]