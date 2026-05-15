from django.db import transaction
from decimal import Decimal
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Pedido, DetallePedido
from .validators import validar_creacion_pedido
from core.choices import Estados

# ==========================================
# 1. SERVICIO DE CREACIÓN (Nacimiento)
# ==========================================
class PedidoService:
    @staticmethod
    def procesar_nuevo_pedido(datos_pedido: dict, detalles_data: list) -> Pedido:
        """
        Servicio que maneja toda la lógica pesada de la creación de un pedido:
        transacciones, validaciones, cálculos y manejo de stock.
        """
        negocio = datos_pedido['negocio']
        
        # 1. Ejecutamos tu validador externo
        validar_creacion_pedido(negocio, detalles_data)
        
        with transaction.atomic():
            # 2. Definimos el costo de envío (que luego podrá ser dinámico)
            costo_envio_inicial = Decimal('5.00') 
            
            # 3. Creamos la cabecera del Pedido
            pedido = Pedido.objects.create(
                costo_envio=costo_envio_inicial,
                **datos_pedido
            )
            
            subtotal_acumulado = Decimal('0.00')
            
            # 4. Procesamos iterativamente los detalles
            for item in detalles_data:
                producto = item['producto']
                cantidad = item['cantidad']
                precio = producto.precio 
                linea_subtotal = precio * cantidad
                
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=linea_subtotal
                )
                
                # 5. Descontamos el stock con tu excelente optimización
                producto.stock_disponible -= cantidad
                producto.save(update_fields=['stock_disponible'])
                
                subtotal_acumulado += linea_subtotal
            
            # 6. Actualizamos los totales del pedido
            pedido.subtotal = subtotal_acumulado
            pedido.total = subtotal_acumulado + pedido.costo_envio
            pedido.save(update_fields=['subtotal', 'total'])
            
            return pedido
# ==========================================
# 2. MÁQUINA DE ESTADOS (Ciclo de Vida)
# ==========================================
class MaquinaEstadosPedido:
    def __init__(self, pedido, usuario_accion):
        self.pedido = pedido
        self.usuario = usuario_accion

    def transicionar_a(self, nuevo_estado):
        estado_actual = self.pedido.estado

        # Regla 1: Validar cancelación por parte del cliente
        if nuevo_estado == Estados.CANCELADO:
            self._validar_cancelacion(estado_actual) # Corrección: Pasamos la variable
        
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
            self._requerir_estado(estado_actual, Estados.EN_CAMINO)
            self._validar_repartidor_asignado()
        
        else:
            raise ValidationError(
                f"Transición al estado {nuevo_estado} no está soportada o es inválida"
            )
        
        # Si todas las validaciones pasan, actualizamos
        self.pedido.estado = nuevo_estado
        self.pedido.save(update_fields=['estado'])
        return self.pedido
    
    def _requerir_estado(self, actual, requerido):
        if actual != requerido:
            raise ValidationError(
                f"No se puede pasar a este estado desde {actual}."
            )
    
    def _validar_cancelacion(self, estado_actual):
        if estado_actual not in [Estados.RECIBIDO, Estados.CONFIRMADO]:
            raise ValidationError(
                "Es muy tarde para cancelar, el pedido ya está en preparación."
            )
        if self.usuario.rol == 'Cliente' and self.pedido.cliente.usuario != self.usuario:
            raise PermissionDenied(
                "No puedes cancelar el pedido de otra persona."
            )
    
    def _validar_repartidor_asignado(self):
        if not hasattr(self.usuario, 'perfil_repartidor'):
            raise PermissionDenied("Solo un repartidor puede hacer esto.")
        
        if self.pedido.repartidor != self.usuario.perfil_repartidor:
            raise PermissionDenied("Este pedido está asignado a otro repartidor.")
        
    def _validar_limite_pedidos_repartidor(self):
        pedidos_activos = Pedido.objects.filter(
            repartidor=self.usuario.perfil_repartidor,
            estado=Estados.EN_CAMINO
        ).exists()
        if pedidos_activos:
            raise ValidationError("Ya tienes un pedido 'EN CAMINO'. Entrégalo antes de iniciar otro.")