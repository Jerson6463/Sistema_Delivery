from rest_framework.exceptions import ValidationError

def validar_creacion_pedido(negocio, detalles):
    
    """
    Reglas de Negocio Críticas:
    1. No se puede crear un pedido si el negocio está cerrado.
    2. No se puede pedir un producto con stock = 0.
    """
    
    # 1. Validación de Horario usando el nuevo @property
    if not negocio.esta_abierto:
        raise ValidationError(
            "No se puede crear el pedido: El negocio se encuentra cerrado en este momento."
        )

    # 2. Validación de Stock usando el nuevo @property
    for item in detalles_data:
        producto = item['producto']
        if not producto.disponible:
            raise ValidationError(
                f"No se puede pedir el producto '{producto.nombre}': No hay stock disponible."
            )