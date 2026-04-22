from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Credencial, Acceso
from alumno.models import Alumno
import uuid

class ValidarQRView(APIView):
    permission_classes = []

    def post(self, request):
        codigo = request.data.get("codigo")
        
        try:
            # Intentar tratar el código como UUID (QR digital)
            uuid.UUID(str(codigo))
            credencial = Credencial.objects.get(codigo_unico=codigo)

        except (ValueError, Credencial.DoesNotExist):
            # No es UUID — buscar como matrícula (código de barras físico)
            try:
                alumno = Alumno.objects.get(matricula=codigo)
                credencial = alumno.usuario.credenciales.filter(estado=True).first()
                if not credencial:
                    return Response({"acceso": "denegado", "motivo": "sin credencial activa"}, status=404)
            except Alumno.DoesNotExist:
                return Response({"acceso": "denegado", "motivo": "no registrado"}, status=404)

        # Validar estado y expiración
        if not credencial.estado:
            resultado = "denegado"
        elif credencial.fecha_expiracion < timezone.now().date():
            resultado = "denegado"
        else:
            resultado = "permitido"

        Acceso.objects.create(
            credencial=credencial,
            resultado=resultado,
            dispositivo=request.data.get("dispositivo", "desconocido")
        )

        return Response({"acceso": resultado})