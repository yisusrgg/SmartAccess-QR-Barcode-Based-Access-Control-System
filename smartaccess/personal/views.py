from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accesos.models import Acceso

@login_required
def personal_dashboard(request):
    user = request.user
    credencial_activa = user.credenciales.filter(estado=True).first()
    
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
            ingreso = not hay_salida
    
    context = {
        'personal': user.personal, 
        'credencial': credencial_activa, # Pasamos la credencial (para sacar el UUID)
        'ingresado': ingreso
    }

    # Aquí el personal verá su QR y su departamento, por ejemplo
    return render(request, 'credencial-personal.html', context)