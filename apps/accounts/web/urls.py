from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.accounts.web import views
from apps.accounts.web.forms import LoginConAprobacionForm

urlpatterns = [
    path("registro/cliente/", views.registro_cliente, name="registro_cliente"),
    path("registro/negocio/", views.registro_negocio, name="registro_negocio"),
    path("registro/repartidor/", views.registro_repartidor, name="registro_repartidor"),
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),
    path(
        "login/",
        views.LoginConRedireccionView.as_view(
            authentication_form=LoginConAprobacionForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
