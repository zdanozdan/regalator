from django.conf import settings
from django.db import models


class ConfettiGlobalSetting(models.Model):
    """Stores default key/value settings."""

    key = models.CharField(max_length=150, unique=True)
    value = models.JSONField(default=dict, blank=True)
    value_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional hint for clients about the expected JSON type.",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Confetti global setting"
        verbose_name_plural = "Confetti global settings"

    def __str__(self) -> str:
        return f"{self.key}"


class ConfettiUserSetting(models.Model):
    """Per-user overrides for Confetti settings."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="confetti_settings",
    )
    key = models.CharField(max_length=150)
    value = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id", "key"]
        unique_together = ("user", "key")
        verbose_name = "Confetti user setting"
        verbose_name_plural = "Confetti user settings"
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["user", "key"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.key}"
