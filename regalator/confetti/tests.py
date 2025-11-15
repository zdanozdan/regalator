from django.contrib.auth import get_user_model
from django.test import TestCase

from . import services
from .models import ConfettiGlobalSetting, ConfettiUserSetting


class ConfettiServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice", email="alice@example.com", password="test1234"
        )
        ConfettiGlobalSetting.objects.create(key="ui.theme", value="light")

    def tearDown(self):
        services.invalidate_confetti_cache()

    def test_falls_back_to_global(self):
        value = services.get_effective_setting("ui.theme", user=self.user)
        self.assertEqual(value, "light")

    def test_user_override_takes_priority(self):
        services.set_user_setting(self.user, "ui.theme", "dark")
        value = services.get_effective_setting("ui.theme", user=self.user)
        self.assertEqual(value, "dark")

    def test_reset_user_setting(self):
        services.set_user_setting(self.user, "ui.theme", "dark")
        services.reset_user_setting(self.user, "ui.theme")
        self.assertFalse(
            ConfettiUserSetting.objects.filter(user=self.user, key="ui.theme").exists()
        )
        value = services.get_effective_setting("ui.theme", user=self.user)
        self.assertEqual(value, "light")
