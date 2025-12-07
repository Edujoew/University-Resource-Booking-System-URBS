from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import json
from decimal import Decimal
from django.db.models import Q
from .models import BookingRequest, Resource
from .forms import BookingRequestForm, UserRegistrationForm, ResourceCreationForm
from django.http import HttpResponse
from django_daraja.mpesa.core import MpesaClient



def index(request):
    return HttpResponse("")
    

def landing_view(request):
    return render(request, 'booking/landing.html')

@login_required
def home_view(request):
    context = {}
    
    if request.user.is_authenticated:
        user_bookings = BookingRequest.objects.filter(user=request.user)
        
        total_bookings = user_bookings.count()
        pending_bookings = user_bookings.filter(status='PENDING').count()
        
        upcoming_bookings = user_bookings.filter(
            status='APPROVED', 
            start_time__gte=timezone.now()
        ).count()
        
        context.update({
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'upcoming_bookings': upcoming_bookings,
        })
    
    return render(request, 'booking/home.html', context)

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
                booking.status = 'PENDING'
                booking.save() 
                messages.info(request, "Booking successfully reserved. Please complete payment to confirm.")
                return redirect('booking:initiate_payment', pk=booking.pk)
                
            else:
                booking.status = 'APPROVED'
                booking.save()
                messages.success(request, "Booking successfully created (no payment required).")
                return redirect('booking:booking_success', pk=booking.pk)
        
        else:
            pass
    else:
        initial_data = {}
        resource_pk = request.GET.get('resource')
        if resource_pk:
              try:
                  resource = Resource.objects.get(pk=resource_pk)
                  initial_data['resource'] = resource
              except Resource.DoesNotExist:
                  pass
        
        form = BookingRequestForm(initial=initial_data)

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
def initiate_stk_push_view(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk, user=request.user)
    
    if booking.start_time and booking.end_time:
        duration = booking.end_time - booking.start_time
        duration_in_hours_float = duration.total_seconds() / 3600
        
        
        duration_in_hours_decimal = Decimal(str(duration_in_hours_float))
        
        
        total_cost = round(booking.resource.cost * duration_in_hours_decimal, 2)
    else:
        total_cost = booking.resource.cost
    
    if request.method == 'POST':
        
        phone_number = request.POST.get('phoneNumber')
        try:
            
            amount = int(float(request.POST.get('amount')))
            if amount <= 0:
                  raise ValueError("Amount must be positive.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount provided for M-Pesa.")
            return redirect('booking:initiate_payment', pk=pk)
            
        cl = MpesaClient()
        account_reference = f'BOOKING_{booking.pk}'
        transaction_desc = f'Payment for {booking.resource.name} Booking #{booking.pk}'
        callback_url = 'https://api.darajambili.com/express-payment' 
        
        try:
            response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
            
            messages.success(request, f"M-Pesa prompt sent to {phone_number}. Please check your phone to complete the KES {amount} payment.")
            
            return redirect('booking:my_bookings_dashboard') 
            
        except Exception as e:
            messages.error(request, f"Payment initiation failed. Error: {e}")
            
    context = {
        'booking': booking,
        'cost': total_cost,
    }
    
    
    return render(request, 'booking/stk_push_form.html', context)

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
                return redirect('booking:admin_pending_requests') 
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
    resources = Resource.objects.filter(is_available=True).order_by('name')
    
    query = request.GET.get('q')
    if query:
        resources = resources.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()

    context = {
        'resources': resources
    }
    return render(request, 'booking/resource_list.html', context)


@login_required
def create_resource_view(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied. Only authorized staff can create resources.")

    if request.method == 'POST':
        form = ResourceCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"New resource '{form.cleaned_data['name']}' created successfully.")
            return redirect(reverse_lazy('booking:resource_list'))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResourceCreationForm()

    context = {
        'form': form
    }
    return render(request, 'booking/resource_create_form.html', context)


@login_required
def resource_update_view(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied. Only authorized staff can modify resources.")

    resource = get_object_or_404(Resource, pk=pk)

    if request.method == 'POST':
        form = ResourceCreationForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f"Resource '{resource.name}' updated successfully.")
            return redirect(reverse_lazy('booking:resource_list')) 
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ResourceCreationForm(instance=resource)

    context = {
        'form': form,
        'resource': resource,
    }
    return render(request, 'booking/resource_update_form.html', context)


@login_required
def resource_delete_view(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied. Only authorized staff can delete resources.")

    resource = get_object_or_404(Resource, pk=pk)

    if request.method == 'POST':
        resource.delete()
        messages.success(request, f"Resource '{resource.name}' was successfully deleted.")
        return redirect(reverse_lazy('booking:resource_list'))

    context = {
        'resource': resource
    }
    return render(request, 'booking/resource_confirm_delete.html', context)

def logged_out_view(request):
    return render(request, 'registration/logged_out.html')