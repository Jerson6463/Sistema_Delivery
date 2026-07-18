from django.urls import path

from apps.accounts.api import views

urlpatterns = [
    path("register/<str:rol>/", views.registrar, name="api_registrar"),
    path("register-options/", views.opciones_registro, name="api_opciones_registro"),
    path("login/", views.login_api, name="api_login"),
    path("logout/", views.logout_api, name="api_logout"),
    path("me/", views.me, name="api_me"),
]
