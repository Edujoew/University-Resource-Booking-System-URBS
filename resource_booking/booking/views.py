# booking/views.py

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
import json
from django.views.generic import ListView  # <-- Add ListView import


from .models import BookingRequest, Resource
from .forms import BookingRequestForm, UserRegistrationForm

# --- NEW: Public Landing Page View (accessible without login) ---
class LandingView(TemplateView):
    """
    Publicly accessible view for the site's landing page.
    It introduces the system and prompts users to log in or register.
    """
    template_name = 'booking/landing.html'

# --- Issue 2: Homepage View ---
class HomeView(LoginRequiredMixin, TemplateView):
    """
    Simple view to display the main application landing page (home.html).
    Requires a user to be logged in to access the page.
    """
    template_name = 'booking/home.html'

# --- Issue 3: User Registration View ---
class RegisterView(FormView):
    """
    Handles user registration. Allows new users to create an account.
    """
    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        """
        Create the user and redirect to login page.
        """
        form.save()
        messages.success(
            self.request,
            'Account created successfully! Please log in with your credentials.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        If form is invalid, re-render with error messages.
        """
        return self.render_to_response(self.get_context_data(form=form))

# --- Issue 5/7: Booking Creation View (FIXED) ---
class BookingCreateView(LoginRequiredMixin, CreateView):
    """
    Handles form submission for new BookingRequests. Requires user to be logged in.
    If the resource requires payment, redirects to the M-Pesa payment page.
    """
    model = BookingRequest
    form_class = BookingRequestForm
    template_name = 'booking/booking_form.html'
    # After creating a booking, redirect users to their bookings dashboard
    success_url = reverse_lazy('booking:my_bookings_dashboard')

    def form_valid(self, form):
        """
        Overrides form_valid to automatically set the user, initial status,
        and handle payment redirection.
        """
        # 1. Prepare to save: Attach the current user to the booking object
        booking = form.save(commit=False)
        booking.user = self.request.user   
        
        # 2. Set Initial Status: All new bookings requiring payment start as PENDING
        # (Status is PENDING by default in the model, but explicitly set here for clarity)
        booking.status = 'PENDING'
        
        # 3. Check for Payment Requirement
        resource = booking.resource # Access resource object directly
        
        if resource and resource.cost > 0:
            # Payment Required: save as PENDING and send user to their dashboard
            booking.save()  # Save the PENDING booking to generate the PK (ID)

            messages.info(self.request, "Booking successfully reserved. Complete payment from your bookings dashboard.")

            # Redirect user to their bookings dashboard where they can see the PENDING booking
            return redirect('booking:my_bookings_dashboard')
            
        else:
            # No Payment Required (Cost is 0):
            booking.status = 'APPROVED' # Immediately approve free bookings
            booking.save()
            messages.success(self.request, "Booking successfully created (no payment required).")
            return super().form_valid(form) # Uses the default success_url ('booking:home')

    def get_context_data(self, **kwargs):
        """Add resource costs to context for display"""
        context = super().get_context_data(**kwargs)
        context['resources'] = Resource.objects.filter(is_available=True)
        return context

        # booking/views.py
# ... (existing imports)




# --- Issue 7: Student Booking Dashboard View ---
class MyBookingsView(LoginRequiredMixin, ListView):
    """
    Displays a list of all BookingRequest objects belonging 
    to the currently logged-in user.
    """
    model = BookingRequest
    template_name = 'booking/my_bookings_dashboard.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        """
        Filters the queryset to only show bookings made by the current user.
        """
        # self.request.user refers to the logged-in user (provided by LoginRequiredMixin)
        return BookingRequest.objects.filter(user=self.request.user).order_by('-start_time')
    
    def get_context_data(self, **kwargs):
        """Adds filtering context for the template"""
        context = super().get_context_data(**kwargs)
        #  categorize bookings for the template if needed
        context['pending_bookings'] = context['bookings'].filter(status='PENDING')
        context['past_bookings'] = context['bookings'].exclude(status='PENDING')
        return context
        

