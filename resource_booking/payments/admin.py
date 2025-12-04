from django.contrib import admin
from .models import MpesaTransaction


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone_number', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('phone_number', 'mpesa_reference', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'mpesa_reference')
