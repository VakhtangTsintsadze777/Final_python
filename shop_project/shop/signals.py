from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Signal to send welcome email when a new user is created
    """
    if created:
        subject = 'Welcome to Our Pottery Shop!'
        message = f'Hi {instance.username},\n\nWelcome to our pottery shop! We are excited to have you join our community.\n\nBest regards,\nThe Pottery Shop Team'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            # Log the error but don't prevent user creation
            print(f"Failed to send welcome email: {e}") 