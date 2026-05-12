from rest_framework.exceptions import PermissionDenied, ValidationError
from core.choices import Estados
from .models import Pedido

class MaquinaEstadosPedido:
    def __init__(self, pedido, usuario_accion):
        self.pedido = pedido
        self.usuario = usuario_accion

    def transicionar_a(self, nuevo_estado):
        estado_actual = self.pedido.estado

        #Regla 1: validar cancelacion po parte del cliente
        if nuevo_estado == Estados.CANCELADO:
            self._validar_cancelacion()
        
        elif nuevo_estado == Estados.CONFIRMADO:
            self._requerir_estado(estado_actual, Estados.RECIBIDO)
        
        elif nuevo_estado == Estados.EN_PREPARACION:
            self._requerir_estado(estado_actual, Estados.CONFIRMADO)
        
        elif nuevo_estado == Estados.LISTO_PARA_RECOJO:
            self._requerir_estado(estado_actual, Estados.EN_PREPARACION)
        
        elif nuevo_estado == Estados.EN_CAMINO:
            self._requerir_estado(estado_actual, Estados.LISTO_PARA_RECOJO)
            self._validar_repartidor_asignado()
            self._validar_limite_pedidos_repartidor()

        elif nuevo_estado == Estados.ENTREGADO:
            self._requerir_estado(estado_actual,Estados.EN_CAMINO)
            self._validar_repartidor_asignado()
        
        else:
            raise ValidationError(
                f"Transicion al estado {nuevo_estado} no esta soportada o es invalida"
            )
        
        #Si todas las validaciones pasa, actualizamos
        self.pedido.estado = nuevo_estado
        self.pedido.save(update_fields = ['estado', 'actualizado_en'])
        return self.pedido
    
    def _requerir_estado(self, actual, requerido):
        if actual != requerido:
            raise ValidationError(
                f"No se puede pasar a este estado desde {actual}."
            )
    
    def _validar_cancelacion(self, estado_actual):
        if estado_actual not in [Estados.RECIBIDO, Estados.CONFIRMADO]:
            raise ValidationError(
                "Es muy tarde para cancelar, el pedido ya esta en preparacion."
            )
        if self.usuario.rol == 'Cliente' and self.pedido.cliente.usuario != self.usuario:
            raise PermissionDenied(
                "No puedes cancelar el pedido de otra persona."
            )
    
    def _validar_repartidor_asignado(self):
        if not hasattr(self.usuario, 'perfil_repartidor'):
            raise PermissionDenied("Solo un repartidor puede hacer estp.")
        if self.pedido.repartidor != self.usuario.perfil_repartidor:
            raise PermissionDenied("Este pedido esta asignado a otro repartidor.")
        
    def _validar_limite_pedidos_repartidor(self):
        pedidos_activos = Pedido.objects.filter(
            repartidor = self.usuario.perfil_repartidor,
            estado = Estados.EN_CAMINO
        ).exists()
        if pedidos_activos:
            raise ValidationError("Ya tienes un pedido 'EN CAMINO'. Entregalo antes de iniciar otro")