from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.landing_view, name='landing'),

    path('home/', views.home_view, name='home'),
    
    path('register/', views.register_view, name='register'),
    
    path('new/', views.booking_create_view, name='new_booking'),
    
    
    path('success/<int:pk>/', views.booking_success_view, name='booking_success'),

    path('my_bookings_dashboard/', views.my_bookings_dashboard, name='my_bookings_dashboard'),

    path('requests/pending/', views.admin_pending_requests, name='admin_pending_dashboard'),
    path('resources/', views.resource_list, name='resource_list'),

    
    path('requests/<int:pk>/update/', views.modify_booking, name='admin_booking_update'), 
    path('booking/<int:pk>/modify/', views.modify_booking, name='modify_booking'),

    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]