from django.urls import path

from apps.delivery.api import views

urlpatterns = [
    path("<int:repartidor_id>/ubicacion/", views.actualizar_ubicacion, name="api_ubicacion"),
]