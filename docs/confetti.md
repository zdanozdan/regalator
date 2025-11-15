# Confetti Settings Module

Confetti provides reusable key/value settings with global defaults and per-user overrides. It can be dropped into any Django project.

## Installation

1. Add `confetti` to `INSTALLED_APPS`.
2. Include the URLs (e.g. `path("confetti/", include("confetti.urls", namespace="confetti"))`).
3. Run `python manage.py migrate confetti`.

## Models

| Model | Purpose |
| --- | --- |
| `ConfettiGlobalSetting` | Stores default JSON values per key plus optional type/description metadata. |
| `ConfettiUserSetting` | Stores per-user overrides keyed by `(user, key)` with automatic fallback to global. |

## Service Helpers (`confetti.services`)

```python
from confetti import services

# Optional registry metadata/validators
services.register_setting(
    "ui.theme",
    description="Preferred UI color theme",
    value_type="str",
    validator=lambda value: value if value in {"light", "dark"} else "light",
)

# Global defaults
services.set_global_setting("ui.theme", "light", value_type="str")

# Per-user overrides
services.set_user_setting(request.user, "ui.theme", "dark")
services.reset_user_setting(request.user, "ui.theme")

# Reading with fallback
theme = services.get_effective_setting("ui.theme", user=request.user, default="light")
```

`services.get_effective_settings_for_user(user)` returns a merged dict suitable for exposing to clients.

## Management Options

At the moment there is no public HTTP API shipped with Confetti. Default values and per-user overrides can be managed directly through the Django admin using the Confetti models. The helper services described above remain available for custom integration points.

## Admin & UI

The Django admin exposes both models with search/filter helpers. A lightweight view is available at `/confetti/panel/`, enabling authenticated users to inspect the current effective settings snapshot.

