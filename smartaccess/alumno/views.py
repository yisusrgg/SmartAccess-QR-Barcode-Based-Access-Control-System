from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def alumno_dashboard(request):
    usuario = request.user
    credencial_activa = usuario.credenciales.filter(estado=True).first()
    # Preparamos los datos para mandarlos al HTML
    contexto = {
        'alumno': usuario.alumno,  # Pasamos los datos del alumno (matrícula, carrera)
        'credencial': credencial_activa # Pasamos la credencial (para sacar el UUID)
    }

    # Aquí el alumno solo verá su código QR
    return render(request, 'credencial-alumno.html', contexto)