from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('accounts/', include('django.contrib.auth.urls')), 
    path('logged_out_page/', include('booking.urls')),
    
    path('payments/', include('payments.urls')), 
    
    path('', include('booking.urls')),

    
    
]