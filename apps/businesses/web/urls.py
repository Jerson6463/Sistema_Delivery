from django.urls import path

from apps.businesses.web import views

urlpatterns = [
    path("", views.lista_negocios, name="lista_negocios"),
    path("configuracion/", views.configuracion_negocio, name="configuracion_negocio"),
    path("<int:negocio_id>/", views.detalle_negocio, name="detalle_negocio"),
]