"""
Service helpers for Confetti settings.

The services provide:
- registry/validation hooks for known keys
- helper APIs to read/write global and per-user settings with fallback
- lightweight caching for global defaults
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ConfettiGlobalSetting, ConfettiUserSetting

SettingValidator = Callable[[Any], Any]

_GLOBAL_CACHE: MutableMapping[str, tuple[bool, Any]] = {}
_registry: Dict[str, "SettingDefinition"] = {}


@dataclass(slots=True)
class SettingDefinition:
    key: str
    description: str = ""
    value_type: str = ""
    validator: Optional[SettingValidator] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self, value: Any) -> Any:
        if self.validator:
            return self.validator(value)
        return value


def register_setting(
    key: str,
    *,
    description: str = "",
    value_type: str = "",
    validator: Optional[SettingValidator] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> None:
    """Register an optional definition for a setting key."""

    _registry[key] = SettingDefinition(
        key=key,
        description=description,
        value_type=value_type,
        validator=validator,
        metadata=metadata or {},
    )


def get_registered_setting(key: str) -> Optional[SettingDefinition]:
    return _registry.get(key)


def list_registered_settings() -> Dict[str, SettingDefinition]:
    return dict(_registry)


def _validate_value(key: str, value: Any) -> Any:
    definition = get_registered_setting(key)
    if definition:
        return definition.validate(value)
    return value


def _get_cached_global_value(key: str) -> tuple[bool, Any]:
    cached = _GLOBAL_CACHE.get(key)
    if cached is not None:
        return cached

    record = (
        ConfettiGlobalSetting.objects.filter(key=key)
        .values("value")
        .first()
    )
    if not record:
        _GLOBAL_CACHE[key] = (False, None)
        return _GLOBAL_CACHE[key]

    _GLOBAL_CACHE[key] = (True, record["value"])
    return _GLOBAL_CACHE[key]


def _invalidate_global_cache(keys: Optional[Iterable[str]] = None) -> None:
    if keys is None:
        _GLOBAL_CACHE.clear()
        return
    for key in keys:
        _GLOBAL_CACHE.pop(key, None)


def invalidate_confetti_cache(keys: Optional[Iterable[str]] = None) -> None:
    """Public helper to clear cached global values."""

    _invalidate_global_cache(keys)


def get_effective_setting(
    key: str, *, user=None, default: Any = None
) -> Any:
    """
    Return the effective setting for `key`, preferring the user override.
    """

    if user is not None:
        user_value = (
            ConfettiUserSetting.objects.filter(user=user, key=key)
            .values_list("value", flat=True)
            .first()
        )
        if user_value is not None:
            return user_value

    exists, value = _get_cached_global_value(key)
    if exists:
        return value
    return default


def get_effective_settings_for_user(user) -> Dict[str, Any]:
    """Return dict of keys -> values, merging global defaults and overrides."""

    result: Dict[str, Any] = {}
    for key, value in ConfettiGlobalSetting.objects.values_list("key", "value"):
        result[key] = value

    overrides = ConfettiUserSetting.objects.filter(user=user).values_list(
        "key", "value"
    )
    for key, value in overrides:
        result[key] = value
    return result


@transaction.atomic
def set_global_setting(
    key: str,
    value: Any,
    *,
    value_type: str = "",
    description: str = "",
) -> ConfettiGlobalSetting:
    value = _validate_value(key, value)
    obj, _ = ConfettiGlobalSetting.objects.update_or_create(
        key=key,
        defaults={
            "value": value,
            "value_type": value_type,
            "description": description,
        },
    )
    _invalidate_global_cache([key])
    return obj


@transaction.atomic
def set_user_setting(user, key: str, value: Any) -> ConfettiUserSetting:
    value = _validate_value(key, value)
    obj, _ = ConfettiUserSetting.objects.update_or_create(
        user=user,
        key=key,
        defaults={"value": value},
    )
    return obj


@transaction.atomic
def reset_user_setting(user, key: str) -> None:
    ConfettiUserSetting.objects.filter(user=user, key=key).delete()


def ensure_registered_keys_exist() -> None:
    """
    Optional helper that creates empty globals for all registered keys.
    """

    if not _registry:
        return

    existing = set(
        ConfettiGlobalSetting.objects.filter(key__in=_registry.keys()).values_list(
            "key", flat=True
        )
    )
    for key in set(_registry).difference(existing):
        set_global_setting(key, value={})


def assert_setting_registered(key: str) -> None:
    if key not in _registry:
        raise ValidationError(f"Setting '{key}' is not registered in Confetti.")


def get_user_model_class():
    return get_user_model()

