from __future__ import annotations

from confetti import services as confetti_services

AUTO_SAVE_REGALACJE_KEY = "auto_save_regalacje"


def user_settings(request):
    """
    Provide commonly-used Confetti settings to templates.
    Currently exposes the auto-save toggle state for regalacje.
    """

    if not request.user.is_authenticated:
        return {"auto_save_regalacje_enabled": False}

    value = confetti_services.get_effective_setting(
        AUTO_SAVE_REGALACJE_KEY, user=request.user, default=False
    )
    return {"auto_save_regalacje_enabled": bool(value)}

