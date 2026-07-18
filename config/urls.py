"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.businesses.web.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path("cuentas/", include("apps.accounts.web.urls")),
    path("negocios/", include("apps.businesses.web.urls")),
    path("panel/negocio/productos/", include("apps.catalog.web.urls")),
    path("panel/repartidor/", include("apps.delivery.web.urls")),
    path("panel/admin/", include("apps.dashboard.web.urls")),
    path("", include("apps.orders.web.urls")),

    # API REST (Fase 8+)
    path("api/auth/", include("apps.accounts.api.urls")),
    path("api/negocios/", include("apps.businesses.api.urls")),
    path("api/productos/", include("apps.catalog.api.urls")),
    path("api/pedidos/", include("apps.orders.api.urls")),
    path("api/repartidores/", include("apps.delivery.api.urls")),
]

# Servir media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
