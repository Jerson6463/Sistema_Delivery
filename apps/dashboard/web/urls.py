from django.urls import path

from apps.dashboard.web import views

urlpatterns = [
    path("", views.dashboard, name="admin_dashboard"),
    path("negocios/<int:negocio_id>/aprobar/", views.aprobar_negocio, name="aprobar_negocio"),
    path("negocios/<int:negocio_id>/rechazar/", views.rechazar_negocio, name="rechazar_negocio"),
    path("negocios/<int:negocio_id>/tarifas/", views.configurar_tarifas, name="configurar_tarifas"),
    path("negocios/<int:negocio_id>/tarifas/<int:tarifa_id>/eliminar/", views.eliminar_tarifa, name="eliminar_tarifa"),
    path("repartidores/<int:repartidor_id>/aprobar/", views.aprobar_repartidor, name="aprobar_repartidor"),
    path("repartidores/<int:repartidor_id>/rechazar/", views.rechazar_repartidor, name="rechazar_repartidor"),

    # Zonas y distritos
    path("zonas/", views.gestionar_zonas, name="gestionar_zonas"),
    path("zonas/crear/", views.crear_zona, name="crear_zona"),
    path("zonas/<int:zona_id>/editar/", views.editar_zona, name="editar_zona"),
    path("zonas/<int:zona_id>/eliminar/", views.eliminar_zona, name="eliminar_zona"),
    path("distritos/crear/", views.crear_distrito, name="crear_distrito"),
    path("distritos/<int:distrito_id>/editar/", views.editar_distrito, name="editar_distrito"),
    path("distritos/<int:distrito_id>/eliminar/", views.eliminar_distrito, name="eliminar_distrito"),
]