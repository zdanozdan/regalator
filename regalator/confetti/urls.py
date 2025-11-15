from django.urls import path

from . import views

app_name = "confetti"

urlpatterns = [
    path("panel/", views.ConfettiSettingsPageView.as_view(), name="panel"),
]

