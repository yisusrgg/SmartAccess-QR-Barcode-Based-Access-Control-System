from django.db import models
from usuarios.models import Usuario

class Credencial(models.Model):
    codigo_unico = models.CharField(max_length=255, unique=True)
    fecha_emision = models.DateField()
    fecha_expiracion = models.DateField()
    estado = models.BooleanField(default=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='credenciales'
    )

    def __str__(self):
        return self.codigo_unico