from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Credencial, Acceso

class ValidarQRView(APIView):
    permission_classes = []  # ESP32 no usará login admin

    def post(self, request):
        codigo = request.data.get("codigo")

        try:
            credencial = Credencial.objects.get(codigo_unico=codigo)
        except Credencial.DoesNotExist:
            return Response({"acceso": "denegado"}, status=404)

        if not credencial.estado:
            resultado = "denegado"
        elif credencial.fecha_expiracion < timezone.now().date():
            resultado = "denegado"
        else:
            resultado = "permitido"

        Acceso.objects.create(
            credencial=credencial,
            resultado=resultado,
            dispositivo="ESP32-Puerta1"
        )

        return Response({"acceso": resultado})