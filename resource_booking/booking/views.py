from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
import json
from decimal import Decimal
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import BookingRequest, Resource, UserMessage
from .forms import BookingRequestForm, UserRegistrationForm, ResourceCreationForm, UserMessageForm
from django_daraja.mpesa.core import MpesaClient
import google.generativeai as genai
from django.conf import settings

User = get_user_model()


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

        
        unread_messages_count = UserMessage.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
        
        context.update({
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'upcoming_bookings': upcoming_bookings,
            'unread_messages_count': unread_messages_count, 
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
            pass
    else:
        form = UserRegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)


def login_success_handler(request):
    messages.success(request, 'Login successful!')
    return redirect('booking:home')

@login_required
def booking_create_view(request):
    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            
            booking = form.save(commit=False)
            booking.user = request.user 
            
            resource = booking.resource
            
            booking.status = 'PENDING'
            booking.save() 

            if resource and resource.cost > 0:
                messages.info(request, "Booking successfully reserved. Please complete payment to confirm.")
                return redirect('booking:initiate_payment', pk=booking.pk)
                
            else:
                messages.success(request, "Booking request submitted successfully. Waiting for admin approval.")
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
    
    is_free = booking.resource.cost <= 0
    
    context = {
        'booking': booking,
        'booking_status': booking.status,
        'is_free': is_free
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
    
    now = timezone.now()
    
    BookingRequest.objects.filter(
        user=request.user,
        status='APPROVED',
        end_time__lt=now 
    ).update(status='COMPLETED')
    
    all_bookings = BookingRequest.objects.filter(user=request.user).order_by('-start_time')
    pending_bookings = all_bookings.filter(status='PENDING')
    past_bookings = all_bookings.exclude(status='PENDING').order_by('-start_time')

    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    context = {
        'bookings': all_bookings,
        'pending_bookings': pending_bookings,
        'past_bookings': past_bookings,
        'unread_messages_count': unread_messages_count, 
    }
    
    return render(request, 'booking/my_bookings_dashboard.html', context)

@login_required
@permission_required('booking.can_review_booking', raise_exception=True)
def admin_pending_requests(request):
    pending_bookings = BookingRequest.objects.filter(status='PENDING').order_by('start_time')
    
    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    context = {
        'pending_bookings': pending_bookings,
        'unread_messages_count': unread_messages_count, 
        'can_review': request.user.has_perm('booking.can_review_booking'),
    }

    return render(request, 'booking/admin_pending_list.html', context)


@login_required
@permission_required('booking.can_review_booking', raise_exception=True) 
@require_http_methods(["GET", "POST"])
def admin_review_booking(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk)
    
    if booking.status != 'PENDING':
        messages.error(request, f"Booking ID {pk} is already {booking.status}.")
        return redirect('booking:admin_pending_dashboard')

    if request.method == "GET":
        return render(request, 'booking/approve.html', {'booking': booking})

    action = request.POST.get('action') 
    subject = ""
    body = ""

    if action == 'approve':
        booking.status = 'APPROVED'
        subject = f"✅ Booking Approved: {booking.resource.name}"
        body = f"Your booking for {booking.resource.name} from {booking.start_time.strftime('%Y-%m-%d %H:%M')} to {booking.end_time.strftime('%Y-%m-%d %H:%M')} has been APPROVED."
        messages.success(request, f"Booking ID {pk} approved.")

    elif action == 'send_payment_warning':
        subject = f"⚠️ Action Required: Payment for {booking.resource.name}"
        body = (f"Your booking request for {booking.resource.name} is awaiting payment. "
                f"Please complete your payment via M-Pesa within 24 hours of this message "
                f"to avoid rejection. Unpaid bookings will be cancelled automatically.")
        
        UserMessage.objects.create(
            sender=request.user, 
            recipient=booking.user, 
            subject=subject,
            body=body,
            is_read=False,
        )
        messages.warning(request, f"Payment warning notification sent to {booking.user.username}.")
        return redirect('booking:admin_pending_dashboard')

    elif action == 'reject':
        return redirect('booking:admin_reject_reason', pk=pk)

    else:
        messages.error(request, "Invalid action specified.")
        return redirect('booking:admin_pending_dashboard')

    booking.save()
    UserMessage.objects.create(
        sender=request.user, 
        recipient=booking.user, 
        subject=subject,
        body=body,
        is_read=False,
    )
    return redirect('booking:admin_pending_dashboard')


@login_required
@permission_required('booking.can_review_booking', raise_exception=True)
def admin_reject_reason_view(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reject_reason')
        
        booking.status = 'REJECTED'
        booking.save()
        
        UserMessage.objects.create(
            sender=request.user,
            recipient=booking.user,
            subject=f"❌ Booking Rejected: {booking.resource.name}",
            body=f"Your booking for {booking.resource.name} has been REJECTED.\n\nReason: {reason}",
            is_read=False,
        )
        
        messages.warning(request, f"Booking #{booking.pk} rejected and user notified.")
        return redirect('booking:admin_pending_dashboard')

    return render(request, 'booking/reject_reason.html', {'booking': booking})


@login_required
def admin_user_list_view(request):
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("Access denied. You must be authorized staff or a superuser.")

    users = User.objects.all().order_by('date_joined')
    
    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    context = {
        'users': users,
        'unread_messages_count': unread_messages_count, 
    }
    return render(request, 'booking/admin_user_list.html', context)


@login_required
def admin_create_staff_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Only superusers can create staff accounts.")
        return redirect('booking:admin_user_list')
    
    messages.info(request, "Staff creation functionality is pending implementation.")
    return redirect('booking:admin_user_list')

@login_required
def admin_delete_user_view(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Access denied. Only superusers can delete user accounts.")

    user_to_delete = get_object_or_404(User, pk=pk)

    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('booking:admin_user_list')
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User account '{username}' successfully deleted.")
        return redirect('booking:admin_user_list')

    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    context = {
        'user_to_delete': user_to_delete,
        'unread_messages_count': unread_messages_count, 
    }
    return render(request, 'booking/admin_user_confirm_delete.html', context)


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
                messages.success(request, "Booking updated and reset to PENDING status.")
                return redirect('booking:my_bookings_dashboard') 
                
            elif is_admin:
                form.save()
                messages.success(request, f"Booking ID {pk} status updated to {booking.status}.")
                
                if booking.status in ['APPROVED', 'REJECTED']:
                    subject = f"Booking Update: {booking.resource.name}"
                    body = f"The administrator has manually updated your booking for **{booking.resource.name}** to **{booking.status}**."
                    UserMessage.objects.create(
                        sender=request.user, 
                        recipient=booking.user,
                        subject=subject,
                        body=body,
                        is_read=False,
                    )
                return redirect('booking:admin_pending_dashboard')
        else:
            messages.error(request, "Form validation failed.")
    else:
        form = BookingRequestForm(instance=booking, is_admin=is_admin, is_owner=is_owner)

    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    context = {
        'form': form,
        'booking': booking,
        'is_admin': is_admin,
        'is_owner': is_owner,
        'unread_messages_count': unread_messages_count, 
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
        if booking.end_time < timezone.now():
            messages.error(request, "Cannot cancel a booking that has already passed.")
            return redirect('booking:my_bookings_dashboard')

        booking.status = 'CANCELLED'
        booking.save()
        messages.success(request, f"Booking ID {pk} successfully cancelled.")
    else:
        messages.error(request, f"Booking cannot be cancelled in {booking.status} status.")

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
@permission_required('booking.can_create_resource', raise_exception=True)
def create_resource_view(request):
    if request.method == 'POST':
        form = ResourceCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"New resource '{form.cleaned_data['name']}' created.")
            return redirect(reverse_lazy('booking:resource_list'))
    else:
        form = ResourceCreationForm()

    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    context = {
        'form': form,
        'unread_messages_count': unread_messages_count, 
    }
    return render(request, 'booking/resource_create_form.html', context)


@login_required
@permission_required('booking.can_create_resource', raise_exception=True) 
def resource_update_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == 'POST':
        form = ResourceCreationForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f"Resource '{resource.name}' updated.")
            return redirect(reverse_lazy('booking:resource_list')) 
    else:
        form = ResourceCreationForm(instance=resource)
        
    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    
    context = {
        'form': form,
        'resource': resource,
        'unread_messages_count': unread_messages_count, 
    }
    return render(request, 'booking/resource_update_form.html', context)


@login_required
@permission_required('booking.can_delete_resource', raise_exception=True)
def resource_delete_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == 'POST':
        resource.delete()
        messages.success(request, f"Resource '{resource.name}' deleted.")
        return redirect(reverse_lazy('booking:resource_list'))

    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    context = {
        'resource': resource,
        'unread_messages_count': unread_messages_count, 
    }
    return render(request, 'booking/resource_confirm_delete.html', context)

def logged_out_view(request):
    return render(request, 'registration/logged_out.html')


@login_required
def message_inbox_view(request):
    messages_list = UserMessage.objects.filter(recipient=request.user).order_by('-sent_at')
    
    unread_messages_count = messages_list.filter(is_read=False).count()
    
    context = {
        'messages': messages_list,
        'unread_messages_count': unread_messages_count, 
    }
    return render(request, 'booking/message_inbox.html', context)


@login_required
@require_http_methods(["POST"])
def mark_message_as_read(request, pk):
    try:
        message = UserMessage.objects.get(pk=pk, recipient=request.user)
        message.is_read = True
        message.save()
        return JsonResponse({'status': 'success'})
    except UserMessage.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


@login_required
def admin_send_message_view(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("Access denied.")

    if request.method == 'POST':
        form = UserMessageForm(request.POST) 
        if form.is_valid():
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            sender = request.user
            target_users = User.objects.filter(is_active=True).exclude(pk=sender.pk)

            messages_to_create = [
                UserMessage(sender=sender, recipient=recipient, subject=subject, body=body)
                for recipient in target_users
            ]
            UserMessage.objects.bulk_create(messages_to_create)
            messages.success(request, f"Broadcast sent to {len(messages_to_create)} users.")
            return redirect('booking:admin_user_list')
    else:
        form = UserMessageForm()

    unread_messages_count = UserMessage.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    context = {
        'form': form,
        'unread_messages_count': unread_messages_count,
        'is_broadcast': True,
    }
    return render(request, 'booking/admin_send_message_form.html', context)

@login_required
@require_http_methods(["POST"])
def chat_assistant(request):
    try:
        data = json.loads(request.body)
        msg = data.get('message', '').lower()

        knowledge = {
            "approve": "Approved bookings are ready for use. Paid resources require M-Pesa completion.",
            "reject": "Rejected bookings are usually explained in your Inbox.",
            "pending": "Pending requests are awaiting admin review.",
            "cancel": "You can cancel bookings from the Dashboard if the time hasn't passed.",
            "mpesa": "Paid resources use M-Pesa STK Push. Enter your PIN when prompted.",
        }

        response = "I'm your UREBS guide! Ask about 'Mpesa', 'cancellations', or 'approvals'."
        
        for key in knowledge:
            if key in msg:
                response = knowledge[key]
                break 
        
        if any(greet in msg for greet in ["hi", "hello", "hey"]):
            response = "Hello! How can I help with your UREBS booking today?"

        return JsonResponse({'reply': response})
    except Exception:
        return JsonResponse({'reply': "I didn't catch that. Try asking about 'payment' or 'status'."})