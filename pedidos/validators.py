from rest_framework.exceptions import ValidationError

def validar_creacion_pedido(negocio, detalles):
    """
    Reglas de Negocio Críticas:
    1. No se puede crear un pedido si el negocio está cerrado.
    2. El producto debe pertenecer al negocio donde se está comprando.
    3. La cantidad solicitada no puede superar el stock actual.
    """
    
    # 1. Validación de Horario
    if not negocio.esta_abierto:
        raise ValidationError(
            "No se puede crear el pedido: El negocio se encuentra cerrado en este momento."
        )

    # 2 y 3. Validación de Pertenencia y Stock exacto
    for item in detalles: # CORRECCIÓN: Usamos 'detalles' que es el parámetro que recibe
        producto = item['producto']
        cantidad_pedida = item['cantidad']

        # Regla Anti-Hacking: ¿El producto es de este negocio?
        if producto.negocio != negocio:
            raise ValidationError(
                f"El producto '{producto.nombre}' no pertenece al negocio '{negocio.nombre}'."
            )

        # Regla de Cantidad Exacta
        if cantidad_pedida > producto.stock_disponible:
            raise ValidationError(
                f"No hay stock suficiente para '{producto.nombre}'. "
                f"Solicitaste {cantidad_pedida}, pero solo quedan {producto.stock_disponible} disponibles."
            )