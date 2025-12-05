from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
import json
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required

from .models import BookingRequest, Resource
from .forms import BookingRequestForm, UserRegistrationForm


class LandingView(TemplateView):
    template_name = 'booking/landing.html'

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'booking/home.html'

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            'Account created successfully! Please log in with your credentials.'
        )
        return super().form_valid(form)

    def form_invalid(self):
        return self.render_to_response(self.get_context_data(form=form))

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = BookingRequest
    form_class = BookingRequestForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('booking:my_bookings_dashboard')

    def form_valid(self, form):
        
        booking = form.save(commit=False)
        booking.user = self.request.user 
        booking.status = 'PENDING'
        
        resource = booking.resource
        
        if resource and resource.cost > 0:
            booking.save() 
            messages.info(self.request, "Booking successfully reserved. Please complete payment to confirm.")
            return redirect('payments:stk_push_page', booking_id=booking.pk)
            
        else:
            booking.status = 'APPROVED'
            booking.save()
            messages.success(self.request, "Booking successfully created (no payment required).")
            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context['resources'] = Resource.objects.filter(is_available=True)
        return context

@login_required 
def my_bookings_dashboard(request):
    
    all_bookings = BookingRequest.objects.filter(user=request.user).order_by('-start_time')
    
    pending_bookings = all_bookings.filter(status='PENDING')
    past_bookings = all_bookings.exclude(status='PENDING').order_by('-start_time')
    
    context = {
        'bookings': all_bookings,
        'pending_bookings': pending_bookings,
        'past_bookings': past_bookings,
    }
    
    return render(request, 'booking/my_bookings_dashboard.html', context)