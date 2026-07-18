from django.urls import path

from apps.catalog.api import views

urlpatterns = [
    path("", views.crear_producto, name="api_crear_producto"),
    path("<int:producto_id>/", views.producto_detalle, name="api_producto_detalle"),
]