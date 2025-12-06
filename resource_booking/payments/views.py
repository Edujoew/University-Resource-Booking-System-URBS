from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from django_daraja.mpesa.core import MpesaClient
from django_daraja.mpesa.exceptions import MpesaInvalidParameterException, MpesaConnectionError

from booking.models import BookingRequest
import json

CALLBACK_URL = 'https://mydomain.com/mpesa-express-simulate/' 
ACCOUNT_REFERENCE = 'UREBS-BOOKING'
TRANSACTION_DESC = 'Resource Booking Payment'


def home(request):
    context = {}
    return render(request, 'home.html', context)


def index(request):
    return redirect('payments')


def mpesaPayment(request):
    if request.method == 'POST':
        phone_number_str = request.POST.get('phoneNumber')
        amount_str = request.POST.get('amount')
        booking_pk = request.POST.get('booking_pk')
        
        error_message = None
        context = {}
        
        try:
            if not phone_number_str or not amount_str or not booking_pk:
                raise ValueError("Missing phone number, amount, or booking ID.")

            phone_number = phone_number_str.replace(' ', '').replace('+', '')
            
            if not phone_number.startswith('254') or len(phone_number) != 12:
                raise ValueError('Invalid phone number format. Must be 12 digits starting with 254.')
            
            try:
                amount = int(float(amount_str))
                if amount < 1:
                    raise ValueError("Amount must be at least 1.")
            except (ValueError, TypeError):
                raise ValueError("Invalid amount format.")

            booking = get_object_or_404(BookingRequest, pk=booking_pk) 

            required_cost = booking.resource.cost
            if amount != required_cost:
                 amount = required_cost 
            
            cl = MpesaClient()

            response = cl.stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=ACCOUNT_REFERENCE,
                transaction_desc=TRANSACTION_DESC,
                callback_url='https://mydomain.com/mpesa-express-simulate/'
            )
            
            context = {
                "status": "success",
                "message": f"STK push successfully sent to {phone_number}. Please enter your PIN to complete the transaction.",
                "response_data": response.text,
                "booking_pk": booking_pk,
            }
            
            return render(request, 'payments/stk_push.html', context)
            
        except (ValueError, MpesaInvalidParameterException, MpesaConnectionError) as e:
            error_message = str(e)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"

        context = {
            "status": "error",
            "message": error_message,
        }
        return render(request, 'payments/stk_push.html', context, status=400)

    else:
        return render(request, 'payments/stk_push.html')