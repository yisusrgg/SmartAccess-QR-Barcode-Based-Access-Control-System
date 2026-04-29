from django.urls import path
from .views import ValidarQRView, RegistrarSalidaView, EstadoAccesoView

urlpatterns = [
    path('validar/', ValidarQRView.as_view()),
    path('salida/', RegistrarSalidaView.as_view()),
    path('estado/', EstadoAccesoView.as_view()),
]