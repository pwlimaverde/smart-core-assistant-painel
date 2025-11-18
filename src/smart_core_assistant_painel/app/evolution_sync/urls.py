from django.urls import path

from .views import webhook

urlpatterns = [
    path("sync/evolution/webhook/", webhook, name="evolution_webhook"),
    path("sync/evolution/webhook", webhook),
]
