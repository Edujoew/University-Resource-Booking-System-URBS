from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('index/', views.index, name='index'),
    # Friendly entry point used by booking flow to initiate payment for a booking
    path('initiate/<int:booking_id>/', views.STKPushView.as_view(), name='initiate_mpesa_payment'),
    path('stk-push/', views.STKPushView.as_view(), name='stk_push'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]
