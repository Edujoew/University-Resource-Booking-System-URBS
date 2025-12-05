from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.conf import settings
from django_daraja.mpesa.core import MpesaClient
from django_daraja.mpesa.exceptions import MpesaInvalidParameterException, MpesaConnectionError
import json
import logging

logger = logging.getLogger(__name__)


class STKPushView(View):
    """Initiate STK push for M-Pesa payment."""

    def get(self, request, *args, **kwargs):
        """Display STK push payment form for bookings.

        Accepts `booking_id` either as a URL kwarg (preferred) or a GET parameter.
        """
        # Prefer booking_id from URL kwargs, fall back to GET param
        booking_id = kwargs.get('booking_id') or request.GET.get('booking_id')
        amount = request.GET.get('amount')

        context = {
            'booking_id': booking_id,
            'amount': amount,
        }

        # If booking_id provided, fetch booking details
        if booking_id:
            try:
                from booking.models import BookingRequest
                booking = BookingRequest.objects.get(id=booking_id, user=request.user)
                context['booking'] = booking
                # Use resource cost if available
                try:
                    context['amount'] = int(booking.resource.cost)
                except Exception:
                    context['amount'] = amount
            except Exception as e:
                logger.error(f"Error fetching booking: {str(e)}")

        return render(request, 'payments/stk_push.html', context)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number', '').strip()
            amount = data.get('amount', 1)
            
            logger.info(f"STK Push Request - Phone: {phone_number}, Amount: {amount}")
            
            if not phone_number:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Phone number is required'
                }, status=400)
            
            # Normalize phone number - remove spaces and +
            phone_number = phone_number.replace(' ', '').replace('+', '')
            
            # Validate phone number format
            if not phone_number.startswith('254'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Phone number must start with 254'
                }, status=400)
                
            if len(phone_number) != 12:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid phone number length. Expected 12 digits, got {len(phone_number)}'
                }, status=400)
            
            # Validate amount
            try:
                amount = int(amount)
                if amount < 1 or amount > 150000:
                    raise ValueError("Amount must be between 1 and 150000")
            except (ValueError, TypeError) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Amount error: {str(e)}'
                }, status=400)
            
            # Initialize M-Pesa client
            try:
                client = MpesaClient()
                
                # Build callback URL - use your domain instead of localhost
                callback_url = 'https://mydomain.com/mpesa-express-simulate/'
                
                logger.info(f"Calling STK push with phone={phone_number}, amount={amount}, callback={callback_url}")
                
                # Send STK push
                response = client.stk_push(
                    phone_number=phone_number,
                    amount=amount,
                    account_reference='URBS-BOOKING',
                    transaction_desc='Resource Booking',
                    callback_url=callback_url
                )
                
                # Log full response object
                logger.info(f"Full Response object: {response}")
                logger.info(f"Response attributes: {vars(response)}")
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response content: {response.text}")
                
                # Extract response details
                response_code = getattr(response, 'response_code', None) or getattr(response, 'ResponseCode', None)
                response_desc = getattr(response, 'response_description', None) or getattr(response, 'ResponseDescription', None)
                checkout_request_id = getattr(response, 'checkout_request_id', None) or getattr(response, 'CheckoutRequestID', None)
                error_code = getattr(response, 'error_code', None)
                error_message = getattr(response, 'error_message', None)
                
                logger.info(f"Extracted - Code: {response_code}, Desc: {response_desc}, Error Code: {error_code}, Error Msg: {error_message}")
                
                # Check for errors first
                if error_code or error_message:
                    logger.error(f"STK Push API Error: {error_code} - {error_message}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'M-Pesa API Error: {error_message or error_code or "Unknown error"}',
                        'data': {
                            'ErrorCode': error_code,
                            'ErrorMessage': error_message
                        }
                    }, status=400)
                
                # Check response code
                if response_code == '0':
                    return JsonResponse({
                        'status': 'success',
                        'message': f'STK push sent to {phone_number}. Check your phone for the prompt.',
                        'data': {
                            'CheckoutRequestID': checkout_request_id or 'N/A',
                            'ResponseCode': response_code,
                            'ResponseDescription': response_desc or 'Request accepted for processing'
                        }
                    })
                else:
                    logger.error(f"STK Push failed with code {response_code}: {response_desc}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'STK Push failed: {response_desc or f"Code {response_code}"}',
                        'data': {
                            'ResponseCode': response_code,
                            'ResponseDescription': response_desc
                        }
                    }, status=400)
                    
            except MpesaInvalidParameterException as e:
                logger.error(f"Invalid parameter: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid parameter: {str(e)}'
                }, status=400)
            except MpesaConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Connection error: {str(e)}'
                }, status=400)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON payload'
            }, status=400)
        except Exception as e:
            logger.exception(f"Unexpected error in STK Push: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }, status=400)


def index(request):
    """Redirect to STK push view."""
    from django.shortcuts import redirect
    booking_id = request.GET.get('booking_id')
    if booking_id:
        return redirect(f'/api/payments/stk-push/?booking_id={booking_id}')
    return redirect('/api/payments/stk-push/')


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """Handle M-Pesa payment callbacks."""
    try:
        data = json.loads(request.body)
        logger.info(f"M-Pesa Callback received: {data}")
        
        # TODO: Process callback and update payment status in database
        # Extract result code and save transaction details
        
        return JsonResponse({
            'status': 'success',
            'message': 'Callback received and processed'
        })
    except Exception as e:
        logger.exception(f"Error processing callback: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
