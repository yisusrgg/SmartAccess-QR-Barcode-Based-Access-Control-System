from django.db import models
from usuarios.models import Usuario

class Acceso(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='accesos'
    )

    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_movimiento = models.CharField(max_length=20)
    resultado = models.CharField(max_length=20)
    dispositivo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.usuario} - {self.fecha_hora}"