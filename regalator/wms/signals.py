from decimal import Decimal

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.signals import Signal
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Product,
    UserProfile,
    PickingOrder,
    PickingItem,
    OrderItem,
    SupplierOrder,
    ReceivingOrder,
    ReceivingItem,
    PickingHistory,
    ReceivingHistory,
    StockMovement,
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
    has_in_progress = 'in_progress' in statuses
    all_created_status = statuses and all(status == 'created' for status in statuses)
    all_completed_status = statuses and all(status == 'completed' for status in statuses)

    new_status = customer_order.status

    if statuses:
        if has_in_progress:
            new_status = 'in_progress'
        elif all_created_status:
            new_status = 'created'
        elif all_completed_status:
            if total_quantity > 0:
                if completed_quantity >= total_quantity:
                    new_status = 'completed'
                elif completed_quantity > 0:
                    new_status = 'partially_completed'
                else:
                    new_status = 'partially_completed'
            else:
                new_status = 'completed'
        else:
            if total_quantity > 0:
                if completed_quantity >= total_quantity:
                    new_status = 'completed'
                elif completed_quantity > 0:
                    new_status = 'partially_completed'
                else:
                    new_status = 'pending'
            else:
                new_status = 'pending'
    else:
        if total_quantity > 0:
            if completed_quantity >= total_quantity:
                new_status = 'completed'
            elif completed_quantity > 0:
                new_status = 'partially_completed'
            else:
                new_status = 'pending'
        else:
            new_status = 'pending'

    if new_status != customer_order.status:
        customer_order.status = new_status
        customer_order.save(update_fields=['status'])


def _sync_supplier_order_status(supplier_order):
    if not supplier_order:
        return

    receiving_orders = supplier_order.receiving_orders.all()
    items = supplier_order.items.all()

    if receiving_orders.exists():
        active_exists = receiving_orders.filter(status__in=['pending', 'in_progress']).exists()
        completed_exists = receiving_orders.filter(status='completed').exists()

        total_items = items.aggregate(total=Count('id'))['total'] or 0
        completed_items = items.filter(quantity_received__gte=1).count()

        new_status = supplier_order.status

        if active_exists:
            new_status = 'in_receiving'
        elif total_items > 0 and completed_items >= total_items:
            new_status = 'received'
        elif completed_items > 0:
            new_status = 'partially_received'
        elif completed_exists:
            new_status = 'partially_received'
        else:
            new_status = supplier_order.status

        if new_status != supplier_order.status:
            supplier_order.status = new_status
            supplier_order.save(update_fields=['status'])

        if new_status in ['received', 'partially_received'] and not supplier_order.actual_delivery_date:
            supplier_order.actual_delivery_date = timezone.now().date()
            supplier_order.save(update_fields=['actual_delivery_date'])
    else:
        if supplier_order.status in ['received', 'partially_received']:
            supplier_order.status = 'confirmed'
            supplier_order.actual_delivery_date = None
            supplier_order.save(update_fields=['status', 'actual_delivery_date'])


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


@receiver(post_save, sender=ReceivingOrder)
def sync_supplier_on_receiving_order_save(sender, instance, created, update_fields=None, **kwargs):
    if instance.supplier_order_id:
        relevant_fields = {'status', 'completed_at', 'started_at'}
        should_sync = created or update_fields is None or bool(relevant_fields.intersection(update_fields))
        if should_sync:
            _sync_supplier_order_status(instance.supplier_order)


@receiver(post_delete, sender=ReceivingOrder)
def sync_supplier_on_receiving_order_delete(sender, instance, **kwargs):
    if instance.supplier_order_id:
        _sync_supplier_order_status(instance.supplier_order)


@receiver(post_save, sender=ReceivingItem)
def sync_supplier_on_receiving_item_save(sender, instance, created, update_fields=None, **kwargs):
    receiving_order = instance.receiving_order
    if receiving_order and receiving_order.supplier_order_id:
        relevant_fields = {'quantity_received'}
        should_sync = created or update_fields is None or bool(relevant_fields.intersection(update_fields))
        if should_sync:
            _sync_supplier_order_status(receiving_order.supplier_order)


@receiver(post_delete, sender=ReceivingItem)
def sync_supplier_on_receiving_item_delete(sender, instance, **kwargs):
    receiving_order = getattr(instance, 'receiving_order', None)
    if receiving_order and receiving_order.supplier_order_id:
        _sync_supplier_order_status(receiving_order.supplier_order)


@receiver(post_save, sender=ReceivingHistory)
def create_movement_on_receiving_history(sender, instance, created, **kwargs):
    if not created:
        return

    quantity = instance.quantity_received or Decimal('0')
    if quantity <= 0:
        return

    StockMovement.objects.create(
        product=instance.product,
        source_location=None,
        target_location=instance.location,
        quantity=quantity,
        movement_type='inbound',
        performed_by=instance.scanned_by,
        note=f"Regalacja {instance.receiving_order.order_number}" if instance.receiving_order_id else ''
    )


@receiver(post_save, sender=PickingHistory)
def create_movement_on_picking_history(sender, instance, created, **kwargs):
    if not created:
        return

    quantity = instance.quantity_picked or Decimal('0')
    if quantity <= 0:
        return

    StockMovement.objects.create(
        product=instance.product_scanned,
        source_location=instance.location_scanned,
        target_location=None,
        quantity=quantity,
        movement_type='outbound',
        performed_by=instance.user,
        note=f"Terminacja {instance.picking_item.picking_order.order_number}" if instance.picking_item_id else ''
    )

