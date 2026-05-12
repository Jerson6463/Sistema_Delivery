from rest_framework.exceptions import ValidationError
import re

def validar_formato_horario(horario_json):
    
    dias_validos = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    
    # Expresión regular para obligar el formato 24h (HH:MM)
    formato_hora = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$') 

    if not isinstance(horario_json, dict):
        raise ValidationError("El horario debe ser un objeto JSON válido.")

    for dia, horas in horario_json.items():
        # 1. Validar que los días existan
        if dia.lower() not in dias_validos:
            raise ValidationError(f"Día no reconocido: '{dia}'. Use días válidos en español.")
        
        # 2. Validar que sea una lista de exactamente 2 elementos (Apertura y Cierre)
        if not isinstance(horas, list) or len(horas) != 2:
            raise ValidationError(
                f"El horario de '{dia}' debe contener exactamente hora de apertura y cierre. Ej: ['08:00', '20:00']"
            )
        
        hora_apertura, hora_cierre = horas[0], horas[1]
        
        # 3. Validar el formato de texto HH:MM
        if not formato_hora.match(hora_apertura) or not formato_hora.match(hora_cierre):
            raise ValidationError(
                f"Formato de hora inválido en '{dia}'. Debe ser HH:MM en 24 horas (ej. '14:30')."
            )
        
        # 4. Validar la lógica del tiempo (No puedes cerrar antes de abrir)
        if hora_apertura >= hora_cierre:
            raise ValidationError(
                f"Incoherencia temporal en '{dia}': La hora de apertura ({hora_apertura}) no puede ser mayor o igual a la de cierre ({hora_cierre})."
            )
            
    return horario_json