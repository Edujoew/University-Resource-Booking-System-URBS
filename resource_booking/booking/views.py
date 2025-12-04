# booking/views.py

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import BookingRequest
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

# --- Issue 5: Booking Creation View ---
class BookingCreateView(LoginRequiredMixin, CreateView):
    """
    Handles form submission for new BookingRequests. Requires user to be logged in.
    """
    model = BookingRequest
    form_class = BookingRequestForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('booking:home') # Redirect back to home on success

    def form_valid(self, form):
        """
        Overrides form_valid to automatically set the user and initial status.
        """
        # Set the user to the currently logged-in user
        form.instance.user = self.request.user
        # Status is automatically set to PENDING by the model default
        return super().form_valid(form)