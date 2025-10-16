from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.signals import Signal
from django.db.models import Sum
from django.contrib.auth.models import User
from .models import Product, UserProfile

# Custom signal for product updates
product_updated = Signal()

@receiver(product_updated)
def handle_product_updated(sender, **kwargs):
    """
    Handler for product_updated signal TBD
    """
    #product = kwargs.get('product')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatycznie tworzy profil użytkownika przy tworzeniu nowego użytkownika"""
    if created:
        UserProfile.objects.create(user=instance)