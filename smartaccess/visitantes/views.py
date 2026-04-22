from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Visitante
from credenciales.models import Credencial

def registrar_visitante(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        curp = request.POST.get('curp')
        motivo = request.POST.get('motivo')

        #Crear el visitante
        nuevo_visitante = Visitante.objects.create(
            nombre=nombre,
            curp=curp,
            motivo=motivo
        )

        #Crear su credencial (expira en 1 día por seguridad)
        fecha_exp = timezone.now().date() + timedelta(days=1)
        credencial = Credencial.objects.create(
            visitante=nuevo_visitante,
            fecha_expiracion=fecha_exp,
            estado=True
        )
        context = {
            'nuevo_visitante': nuevo_visitante,
            'credencial': credencial
        }

        return render(request, 'credencial-visitante.html', context)
    
    return render(request, 'registrar-visitante.html')