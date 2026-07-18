"""
Handler de excepciones para DRF.

Convierte las excepciones de dominio en respuestas JSON uniformes:
    {"error": "<CODIGO>", "detail": "<mensaje>"}

Así las vistas de la API no necesitan try/except: lanzan (o dejan que el
servicio lance) la excepción de dominio y este handler la traduce.
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.shared.domain.exceptions import DomainException, PermisoDominioException


def api_exception_handler(exc, context):
    if isinstance(exc, PermisoDominioException):
        return Response({"error": exc.codigo, "detail": str(exc)}, status=403)
    if isinstance(exc, DomainException):
        return Response({"error": exc.codigo, "detail": str(exc)}, status=400)
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {"error": "NO_ENCONTRADO", "detail": "Recurso no encontrado."},
            status=404,
        )
    # Cualquier otra excepción sigue el manejo estándar de DRF.
    return drf_exception_handler(exc, context)
