from django.urls import path

from apps.catalog.web import views

urlpatterns = [
    path("", views.panel_productos, name="panel_productos"),
    path("nuevo/", views.crear_producto, name="crear_producto"),
    path("<int:producto_id>/editar/", views.editar_producto, name="editar_producto"),
    path("<int:producto_id>/desactivar/", views.desactivar_producto, name="desactivar_producto"),
    path("<int:producto_id>/activar/", views.activar_producto, name="activar_producto"),
]