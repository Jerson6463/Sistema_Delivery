from django.urls import path

from apps.businesses.api import views

urlpatterns = [
    path("", views.listar_negocios, name="api_negocios"),
    path("<int:negocio_id>/", views.detalle_negocio, name="api_negocio_detalle"),
    path("<int:negocio_id>/productos/", views.productos_negocio, name="api_negocio_productos"),
]