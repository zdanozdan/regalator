from decimal import Decimal

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.signals import Signal
from django.contrib.auth.models import User

from .models import (
    Product,
    UserProfile,
    PickingOrder,
    PickingItem,
    OrderItem,
)

# Custom signal for product updates
product_updated = Signal()


def _sync_customer_order_status(customer_order):
    """Synchronizuje status zamówienia klienta na podstawie kompletacji."""
    if not customer_order or customer_order.status == 'cancelled':
        return

    items = list(customer_order.items.all())
    picking_orders = list(customer_order.pickingorder_set.all())

    total_quantity = Decimal('0')
    completed_quantity = Decimal('0')

    for item in items:
        qty = item.quantity or Decimal('0')
        completed = item.completed_quantity or Decimal('0')
        capped_completed = min(completed, qty) if qty else completed

        total_quantity += qty
        completed_quantity += capped_completed

    statuses = [order.status for order in picking_orders if order.status != 'cancelled']
    has_in_progress = any(status == 'in_progress' for status in statuses)
    has_created = any(status == 'created' for status in statuses)
    has_completed = any(status == 'completed' for status in statuses)
    has_non_cancelled = bool(statuses)

    any_picking_items = any(hasattr(order, 'items') and order.items.exists() for order in picking_orders)
    all_pickings_completed = bool(statuses) and all(status == 'completed' for status in statuses)

    new_status = customer_order.status

    if total_quantity > 0:
        if completed_quantity >= total_quantity:
            new_status = 'completed'
        elif completed_quantity >= 0:
            new_status = 'partially_completed'
        elif has_in_progress or has_created:
            new_status = 'in_progress'
        elif has_non_cancelled:
            new_status = 'pending'
        else:
            new_status = 'pending'
    else:
        if has_in_progress or has_created:
            new_status = 'in_progress'
        elif not any_picking_items and all_pickings_completed:
            new_status = 'completed'
        elif has_completed and not has_in_progress and not has_created:
            new_status = 'completed'
        elif has_non_cancelled:
            new_status = 'pending'
        else:
            new_status = 'pending'

    if new_status != customer_order.status:
        customer_order.status = new_status
        customer_order.save(update_fields=['status'])


@receiver(product_updated)
def handle_product_updated(sender, **kwargs):
    """Handler for product_updated signal TBD"""
    # product = kwargs.get('product')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatycznie tworzy profil użytkownika przy tworzeniu nowego użytkownika"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=PickingOrder)
def sync_order_on_picking_order_save(sender, instance, created, update_fields=None, **kwargs):
    if not instance.customer_order_id:
        return

    relevant_fields = {'status', 'completed_at', 'started_at', 'assigned_to'}
    should_sync = created or update_fields is None or bool(relevant_fields.intersection(update_fields))

    if should_sync:
        _sync_customer_order_status(instance.customer_order)


@receiver(post_delete, sender=PickingOrder)
def sync_order_on_picking_order_delete(sender, instance, **kwargs):
    if instance.customer_order_id:
        _sync_customer_order_status(instance.customer_order)


@receiver(post_save, sender=PickingItem)
def sync_order_on_picking_item_save(sender, instance, created, update_fields=None, **kwargs):
    picking_order = instance.picking_order
    if not picking_order or not picking_order.customer_order_id:
        return

    relevant_fields = {'quantity_picked', 'is_completed', 'location', 'order_item', 'picking_order'}
    should_sync = created or update_fields is None or bool(relevant_fields.intersection(update_fields))

    if should_sync:
        _sync_customer_order_status(picking_order.customer_order)


@receiver(post_delete, sender=PickingItem)
def sync_order_on_picking_item_delete(sender, instance, **kwargs):
    picking_order = getattr(instance, 'picking_order', None)
    if picking_order and picking_order.customer_order_id:
        _sync_customer_order_status(picking_order.customer_order)


@receiver(post_save, sender=OrderItem)
def sync_order_on_order_item_save(sender, instance, created, update_fields=None, **kwargs):
    customer_order = instance.order
    if not customer_order:
        return

    relevant_fields = {'completed_quantity', 'quantity'}
    should_sync = created or update_fields is None or bool(relevant_fields.intersection(update_fields))

    if should_sync:
        _sync_customer_order_status(customer_order)