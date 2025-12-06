from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json

from .models import BookingRequest, Resource
from .forms import BookingRequestForm, UserRegistrationForm


def landing_view(request):
    return render(request, 'booking/landing.html')

@login_required
def home_view(request):
    return render(request, 'booking/home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Account created successfully! Please log in with your credentials.'
            )
            return redirect(reverse_lazy('login'))
    else:
        form = UserRegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)

@login_required
def booking_create_view(request):
    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            
            booking = form.save(commit=False)
            booking.user = request.user 
            
            resource = booking.resource
            
            if resource and resource.cost > 0:
                # Resource costs money: Set to PENDING and require payment
                booking.status = 'PENDING'
                booking.save() 
                messages.info(request, "Booking successfully reserved. Please complete payment to confirm.")
                # Redirect to payment/success page path
                return redirect('booking:booking_success', pk=booking.pk)
                
            else:
                # Resource is FREE (cost <= 0): Approve immediately
                booking.status = 'APPROVED'
                booking.save()
                messages.success(request, "Booking successfully created (no payment required).")
                # Redirect to success page path
                return redirect('booking:booking_success', pk=booking.pk)
    else:
        form = BookingRequestForm()

    resources = Resource.objects.filter(is_available=True)
    
    context = {
        'form': form,
        'resources': resources
    }
    return render(request, 'booking/booking_form.html', context)

@login_required
def booking_success_view(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk, user=request.user)
    
    context = {
        'booking': booking,
        'booking_status': booking.status
    }
    return render(request, 'booking/booking_success.html', context)


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

@login_required
def admin_pending_requests(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Access denied. You must be staff or a superuser.")

    pending_bookings = BookingRequest.objects.filter(status='PENDING').order_by('start_time')
    
    context = {
        'pending_bookings': pending_bookings
    }

    return render(request, 'booking/admin_pending_list.html', context)


@login_required
def modify_booking(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk)
    is_owner = booking.user == request.user
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if not (is_owner or is_admin):
        return HttpResponseForbidden("You do not have permission to view this booking.")

    if request.method == 'POST':
        form = BookingRequestForm(request.POST, instance=booking, is_admin=is_admin, is_owner=is_owner)

        if form.is_valid():
            
            if is_owner:
                
                if booking.status != 'PENDING':
                    messages.error(request, "Only pending bookings can be modified by the owner.")
                    return redirect('booking:modify_booking', pk=pk)
                
                
                updated_booking = form.save(commit=False)
                updated_booking.status = 'PENDING'
                updated_booking.save()
                messages.success(request, "Booking time/date successfully updated and reset to PENDING status for review.")
                return redirect('booking:my_bookings_dashboard') 
            
            elif is_admin:
                
                form.save()
                messages.success(request, f"Booking ID {pk} status successfully updated to {booking.status}.")
                return redirect('booking:admin_pending_dashboard') 
        else:
            messages.error(request, "There was an error with your submission. Please check the form. Errors shown below.")
            
    else:
        form = BookingRequestForm(instance=booking, is_admin=is_admin, is_owner=is_owner)
    
    context = {
        'form': form,
        'booking': booking,
        'is_admin': is_admin,
        'is_owner': is_owner,
    }

    return render(request, 'booking/booking_update_form.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_booking(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk)
    
    if booking.user != request.user:
        messages.error(request, "You do not have permission to cancel this booking.")
        return redirect('booking:my_bookings_dashboard')
    
    
    if booking.status in ['APPROVED', 'PENDING']:
        booking.status = 'CANCELLED'
        booking.save()
        messages.success(request, f"Booking ID {pk} for {booking.resource.name} has been successfully cancelled.")
    elif booking.status == 'CANCELLED':
        messages.info(request, "This booking is already cancelled.")
    else:
        messages.error(request, f"Booking ID {pk} cannot be cancelled in {booking.status} status.")

    return redirect('booking:my_bookings_dashboard')


def resource_list(request):
    return render(request, 'booking/resource_list.html', {})