from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.signals import Signal
from django.db.models import Sum
from .models import Product

# Custom signal for product updates
product_updated = Signal()

@receiver(product_updated)
def handle_product_updated(sender, **kwargs):
    """
    Handler for product_updated signal TBD
    """
    #product = kwargs.get('product')