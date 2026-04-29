from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accesos.models import Acceso


@login_required
def alumno_dashboard(request):
    usuario = request.user
    credencial_activa = usuario.credenciales.filter(estado=True).first()
    
    # Verificar si ya hay una entrada activa sin salida
    ingresado = False
    if credencial_activa:
        ultimo_acceso = Acceso.objects.filter(
            credencial=credencial_activa,
            tipo_movimiento="entrada",
            resultado="permitido"
        ).order_by('-fecha_hora').first()

        if ultimo_acceso:
            hay_salida = Acceso.objects.filter(
                credencial=credencial_activa,
                tipo_movimiento="salida",
                fecha_hora__gt=ultimo_acceso.fecha_hora,
                resultado="permitido"
            ).exists()
            ingresado = not hay_salida
    
    # datos para mandarlos al HTML
    contexto = {
        'alumno': usuario.alumno,  
        'credencial': credencial_activa,
        'ingresado': ingresado
    }

    # Aquí el alumno solo verá su código QR
    return render(request, 'credencial-alumno.html', contexto)