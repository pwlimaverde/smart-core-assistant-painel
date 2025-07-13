from django.urls import path

from . import views

urlpatterns = [
    path('treinar_ia', views.treinar_ia, name="treinar_ia"),
    path(
        'pre-processamento/<int:id>/',
        views.pre_processamento,
        name="pre_processamento"),
]
