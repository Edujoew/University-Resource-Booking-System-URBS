from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserMessage
from django.utils import timezone

User = get_user_model()

@receiver(post_save, sender=User)
def notify_admin_new_user(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        
        subject = f"🔔 NEW USER JOINED: {instance.username}"
        body = f"A new standard user has registered:\n\nUsername: {instance.username}\nEmail: {instance.email}\nJoined: {instance.date_joined.strftime('%Y-%m-%d %H:%M')}"
        
        
        admins = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
        
        messages_to_create = []
        for admin in admins.exclude(pk=instance.pk): 
            messages_to_create.append(
                UserMessage(
                    sender=instance, 
                    recipient=admin,
                    subject=subject,
                    body=body,
                    is_read=False,
                )
            )
        
        if messages_to_create:
            UserMessage.objects.bulk_create(messages_to_create)


@receiver(post_delete, sender=User)
def notify_admin_user_deleted(sender, instance, **kwargs):
    
    
    if instance.is_superuser or instance.is_staff:
        deleted_role = 'ADMIN/STAFF'
    else:
        deleted_role = 'STANDARD USER'

     
    
    try:
        system_sender = User.objects.filter(is_superuser=True).first()
    except:
        return

    subject = f"🗑️ ACCOUNT DELETED: {instance.username}"
    body = f"A user account has been permanently deleted from the system.\n\nDetails:\nUsername: {instance.username}\nRole: {deleted_role}\nDeletion Time: {timezone.now().strftime('%Y-%m-%d %H:%M')}"
    
    
    admins = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
    
    messages_to_create = []
    for admin in admins.exclude(pk=instance.pk): 
        messages_to_create.append(
            UserMessage(
                sender=system_sender,
                recipient=admin,
                subject=subject,
                body=body,
                is_read=False,
            )
        )
    
    if messages_to_create:
        UserMessage.objects.bulk_create(messages_to_create)