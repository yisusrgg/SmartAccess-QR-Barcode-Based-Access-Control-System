"""
URL configuration for smartaccess project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.contrib.auth import views as auth_views 
from usuarios import views as usuarios_views
from alumno import views as alumno_views
from personal import views as personal_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # MUNDO WEB (Para ti y el personal administrativo) ======================
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Usuarios
    path('', usuarios_views.dashboard, name='dashboard'), 
    path('panel-admin/', usuarios_views.admin_dashboard, name='admin_dashboard'),
    
    # Alumnos y Personal
    path('alumno-credencial/', alumno_views.alumno_dashboard, name='alumno_dashboard'),
    path('personal-credencial/', personal_views.personal_dashboard, name='personal_dashboard'),

    # MUNDO API REST (Para la App Android y el ESP32) =======================
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/access/', include('accesos.urls')), <-- Esta la descomentaremos cuando programemos el ESP32
]




# urlpatterns = [
#     # El panel de Django y tu Login se quedan aquí porque son globales
#     path('admin/', admin.site.urls),
#     path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
#     # Delegamos las rutas a los "recepcionistas" de cada app:
#     # Si la ruta está vacía (''), manda a preguntar al urls.py de usuarios
#     path('', include('usuarios.urls')),
    
#     # Si la ruta empieza con 'alumno/', manda a preguntar al urls.py de alumno
#     path('alumno/', include('alumno.urls')),
    
#     # Si la ruta empieza con 'personal/', manda a preguntar al urls.py de personal
#     path('personal/', include('personal.urls')),
    
#     # La ruta para tu ESP32
#     path('api/access/', include('accesos.urls')),
# ]