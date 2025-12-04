from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('index/', views.index, name='index'),
    path('stk-push/', views.STKPushView.as_view(), name='stk_push'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]
