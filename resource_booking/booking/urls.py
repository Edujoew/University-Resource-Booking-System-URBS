from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    
    path('home/', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/create/', views.create_resource_view, name='create_resource'),
    path('resources/<int:pk>/update/', views.resource_update_view, name='resource_update'),
    path('resources/<int:pk>/delete/', views.resource_delete_view, name='resource_delete'),

    path('new/', views.booking_create_view, name='new_booking'),
    
    
    path('payment/initiate/<int:pk>/', views.initiate_stk_push_view, name='initiate_payment'),

    
    path('success/<int:pk>/', views.booking_success_view, name='booking_success'), 

    path('my_bookings_dashboard/', views.my_bookings_dashboard, name='my_bookings_dashboard'),
    path('booking/<int:pk>/modify/', views.modify_booking, name='modify_booking'),
    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),

    path('requests/pending/', views.admin_pending_requests, name='admin_pending_dashboard'),
    path('requests/<int:pk>/update/', views.modify_booking, name='admin_booking_update'), 
    
    
    path('booking/admin/users/', views.admin_user_list_view, name='admin_user_list'),

    path('booking/messages/inbox/', views.message_inbox_view, name='message_inbox'),
    path('booking/admin/send-message/', views.admin_send_message_view, name='admin_send_message'),
]