from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .models import ConfettiGlobalSetting
from . import services


class ConfettiSettingsPageView(LoginRequiredMixin, TemplateView):
    template_name = "confetti/panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["effective_settings"] = services.get_effective_settings_for_user(
            self.request.user
        )
        context["global_settings"] = ConfettiGlobalSetting.objects.order_by("key")
        return context
