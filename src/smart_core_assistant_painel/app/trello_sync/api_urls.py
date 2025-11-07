from django.urls import path

from . import views_api

app_name = "trello_sync_api"

urlpatterns = [
    path("webhook/", views_api.webhook, name="webhook"),
]