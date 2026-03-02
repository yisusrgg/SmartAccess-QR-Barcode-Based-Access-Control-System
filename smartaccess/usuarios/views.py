from urllib import request
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required 
def dashboard(request):
    # request.user contiene toda la info del usuario que acaba de iniciar sesión
    usuario = request.user

    # Si es Superusuario (Administrador)
    if usuario.is_superuser or usuario.is_staff:
        return redirect('admin_dashboard')
        
    # Si es un Alumno (Django busca la relación OneToOne 'alumno')
    elif hasattr(usuario, 'alumno'):
        return redirect('alumno_dashboard')
        
    # Si es Personal (Django busca la relación OneToOne 'personal')
    elif hasattr(usuario, 'personal'):
        return redirect('personal_dashboard')
        
    # Si es un usuario raro que no tiene perfil asignado aún
    else:
        return render(request, 'error_perfil.html')



@login_required
def admin_dashboard(request):
    # Aquí irá tu HTML con gráficas, listas de alumnos, etc.
    # return render(request, 'admin_dashboard.html')
    return render(request, 'acceso.html')

