from django.db import models
from credenciales.models import Credencial

class Acceso(models.Model):
    credencial = models.ForeignKey(
        Credencial,
        on_delete=models.CASCADE,
        related_name='accesos'
    )

    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_movimiento = models.CharField(max_length=20)
    resultado = models.CharField(max_length=20)
    dispositivo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.credencial.usuario.nombre} - {self.fecha_hora}"