from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def personal_dashboard(request):
    user = request.user
    credencial_activa = user.credenciales.filter(estado=True).first()
    context = {
        'personal': user.personal, 
        'credencial': credencial_activa # Pasamos la credencial (para sacar el UUID)
    }

    # Aquí el personal verá su QR y su departamento, por ejemplo
    return render(request, 'credencial-personal.html', context)