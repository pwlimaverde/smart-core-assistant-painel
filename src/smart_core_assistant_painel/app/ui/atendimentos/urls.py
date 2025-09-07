from django.urls import path

from . import views

app_name = "atendimentos"

urlpatterns = [
    path("webhook_whatsapp/", views.webhook_whatsapp, name="webhook_whatsapp"),
]
