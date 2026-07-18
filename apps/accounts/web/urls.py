from django.contrib.auth.views import LoginView, LogoutView
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
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginConAprobacionForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
