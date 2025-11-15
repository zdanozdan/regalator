from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.template.loader import render_to_string
from django.urls import reverse

from confetti import services as confetti_services

from .context_processors import AUTO_SAVE_REGALACJE_KEY
from .models import (
    Location,
    Product,
    ReceivingItem,
    ReceivingOrder,
    SupplierOrder,
    SupplierOrderItem,
)


class SettingsMenuPartialTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def render_partial(self, enabled):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        return render_to_string(
            'wms/partials/_settings_toggle_item.html',
            {'auto_save_enabled': enabled},
            request=request,
        )

    def test_partial_shows_toggle_on_state(self):
        html = self.render_partial(True)
        self.assertIn('fa-toggle-on', html)
        self.assertNotIn('fa-toggle-off', html)

    def test_partial_shows_toggle_off_state(self):
        html = self.render_partial(False)
        self.assertIn('fa-toggle-off', html)
        self.assertNotIn('fa-toggle-on', html)


class SettingsToggleViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester', password='pass1234'
        )
        self.client.force_login(self.user)

    def tearDown(self):
        confetti_services.invalidate_confetti_cache()

    def test_toggle_endpoint_flips_setting_and_returns_fragment(self):
        url = reverse('wms:toggle_auto_save_regalacje')

        # Toggle on
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('fa-toggle-on', html)
        self.assertIn('Automatycznie zapisuj regalacje', html)

        current = confetti_services.get_effective_setting(
            AUTO_SAVE_REGALACJE_KEY, user=self.user, default=False
        )
        self.assertTrue(current)
        self.assertIn('toastMessage', response.headers.get('HX-Trigger', ''))

        # Toggle off
        response = self.client.post(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('fa-toggle-off', html)
        current = confetti_services.get_effective_setting(
            AUTO_SAVE_REGALACJE_KEY, user=self.user, default=True
        )
        self.assertFalse(current)


class ReceivingFastAutoSaveTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='worker', password='pass1234'
        )
        self.client.force_login(self.user)

        self.product = Product.objects.create(code='P001', name='Produkt 1')
        self.location = Location.objects.create(
            name='Regal A1', location_type='shelf', barcode='LOC-A1'
        )
        self.supplier_order = SupplierOrder.objects.create(
            order_number='ZD-1',
            supplier_name='Dostawca',
            order_date=date.today(),
            expected_delivery_date=date.today(),
        )
        self.supplier_item = SupplierOrderItem.objects.create(
            supplier_order=self.supplier_order,
            product=self.product,
            quantity_ordered=Decimal('5'),
        )
        self.receiving_order = ReceivingOrder.objects.create(
            order_number='REG-1',
            supplier_order=self.supplier_order,
            status='in_progress',
            assigned_to=self.user,
        )
        self.receiving_item = ReceivingItem.objects.create(
            receiving_order=self.receiving_order,
            supplier_order_item=self.supplier_item,
            product=self.product,
            quantity_ordered=Decimal('5'),
            sequence=1,
        )
        self.submit_url = reverse(
            'wms:htmx_receiving_submit', args=[self.receiving_order.id]
        )

    def tearDown(self):
        confetti_services.invalidate_confetti_cache()

    def enable_auto_save(self):
        confetti_services.set_user_setting(
            self.user, AUTO_SAVE_REGALACJE_KEY, True
        )

    def test_receiving_fast_page_shows_inline_toggle(self):
        self.enable_auto_save()
        url = reverse('wms:receiving_order_fast', args=[self.receiving_order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auto-save-inline-toggle')

    def test_clicking_pending_item_auto_saves_when_enabled(self):
        self.enable_auto_save()

        # Set current location via HTMX request
        self.client.post(
            self.submit_url,
            {'location_code': self.location.barcode},
            HTTP_HX_REQUEST='true',
        )

        response = self.client.post(
            self.submit_url,
            {
                'receiving_item_id': str(self.receiving_item.id),
                'auto_submit_after_select': '1',
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)

        self.receiving_item.refresh_from_db()
        self.assertEqual(self.receiving_item.quantity_received, Decimal('5'))


class SettingsPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='viewer', password='pass1234'
        )
        self.client.force_login(self.user)

    def tearDown(self):
        confetti_services.invalidate_confetti_cache()

    def test_settings_page_contains_toggle_fragment(self):
        url = reverse('wms:settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Automatycznie zapisuj regalacje')
        self.assertContains(response, 'hx-post')
