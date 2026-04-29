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
            Acceso.objects.create(
                credencial=credencial,
                tipo_movimiento="entrada",
                resultado=resultado,
                dispositivo=request.data.get("dispositivo", "desconocido")
            )
            return Response({"acceso": resultado})
        
        if credencial.fecha_expiracion < timezone.now().date():
            resultado = "denegado"
            Acceso.objects.create(
                credencial=credencial,
                tipo_movimiento="entrada",
                resultado=resultado,
                dispositivo=request.data.get("dispositivo", "desconocido")
            )
            return Response({"acceso": resultado})

        # Verificar si ya hay una entrada activa (sin salida) para esta credencial
        ultimo_acceso = Acceso.objects.filter(
            credencial=credencial,
            tipo_movimiento="entrada",
            resultado="permitido"
        ).order_by('-fecha_hora').first()

        # Verificar si hay salida registrada después de esa entrada
        if ultimo_acceso:
            hay_salida = Acceso.objects.filter(
                credencial=credencial,
                tipo_movimiento="salida",
                fecha_hora__gt=ultimo_acceso.fecha_hora,
                resultado="permitido"
            ).exists()
            
            if not hay_salida:
                # Ya hay una entrada activa sin salida
                Acceso.objects.create(
                    credencial=credencial,
                    tipo_movimiento="entrada",
                    resultado="denegado",
                    motivo="ya_ingresada",
                    dispositivo=request.data.get("dispositivo", "desconocido")
                )
                return Response({
                    "acceso": "denegado", 
                    "motivo": "ya_ingresada",
                    "mensaje": "Credencial ya ingresada"
                })

        # Permitir acceso - registrar entrada
        Acceso.objects.create(
            credencial=credencial,
            tipo_movimiento="entrada",
            resultado="permitido",
            dispositivo=request.data.get("dispositivo", "desconocido")
        )

        return Response({"acceso": "permitido"})


class RegistrarSalidaView(APIView):
    permission_classes = []

    def post(self, request):
        codigo = request.data.get("codigo")
        
        try:
            uuid.UUID(str(codigo))
            credencial = Credencial.objects.get(codigo_unico=codigo)
        except (ValueError, Credencial.DoesNotExist):
            try:
                alumno = Alumno.objects.get(matricula=codigo)
                credencial = alumno.usuario.credenciales.filter(estado=True).first()
                if not credencial:
                    return Response({"salida": "denegada", "motivo": "sin credencial activa"}, status=404)
            except Alumno.DoesNotExist:
                return Response({"salida": "denegada", "motivo": "no registrado"}, status=404)

        # Buscar la última entrada activa sin salida
        ultimo_acceso = Acceso.objects.filter(
            credencial=credencial,
            tipo_movimiento="entrada",
            resultado="permitido"
        ).order_by('-fecha_hora').first()

        if not ultimo_acceso:
            return Response({"salida": "denegada", "motivo": "sin_entrada"})

        # Verificar si ya hay salida registrada
        hay_salida = Acceso.objects.filter(
            credencial=credencial,
            tipo_movimiento="salida",
            fecha_hora__gt=ultimo_acceso.fecha_hora,
            resultado="permitido"
        ).exists()

        if hay_salida:
            return Response({"salida": "denegada", "motivo": "ya_salio"})

        # Registrar salida
        Acceso.objects.create(
            credencial=credencial,
            tipo_movimiento="salida",
            resultado="permitido",
            dispositivo=request.data.get("dispositivo", "desconocido")
        )

        return Response({"salida": "permitida"})


class EstadoAccesoView(APIView):
    permission_classes = []

    def get(self, request):
        codigo = request.query_params.get('codigo')
        
        if not codigo:
            return Response({"error": "codigo requerido"}, status=400)
        
        try:
            uuid.UUID(str(codigo))
            credencial = Credencial.objects.get(codigo_unico=codigo)
        except (ValueError, Credencial.DoesNotExist):
            try:
                alumno = Alumno.objects.get(matricula=codigo)
                credencial = alumno.usuario.credenciales.filter(estado=True).first()
            except Alumno.DoesNotExist:
                return Response({"ingresado": False})

        if not credencial:
            return Response({"ingresado": False})

        # Verificar si hay entrada activa sin salida
        ultimo_acceso = Acceso.objects.filter(
            credencial=credencial,
            tipo_movimiento="entrada",
            resultado="permitido"
        ).order_by('-fecha_hora').first()

        if ultimo_acceso:
            hay_salida = Acceso.objects.filter(
                credencial=credencial,
                tipo_movimiento="salida",
                fecha_hora__gt=ultimo_acceso.fecha_hora,
                resultado="permitido"
            ).exists()
            
            return Response({"ingresado": not hay_salida})

        return Response({"ingresado": False})