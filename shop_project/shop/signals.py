from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Signal to send welcome email when a new user is created
    """
    if created:
        subject = 'Welcome to Our Pottery Shop!'
        message = f'''
        Dear {instance.username},

        Welcome to our pottery shop! We're excited to have you join our community.

        You can now:
        - Browse our collection of handcrafted pottery
        - Add items to your cart
        - Place orders
        - Track your order status

        Thank you for choosing our shop!

        Best regards,
        The Pottery Shop Team
        '''
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't prevent user creation
            print(f"Failed to send welcome email: {e}") 