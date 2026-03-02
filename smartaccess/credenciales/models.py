import uuid
from django.db import models
from usuarios.models import Usuario
from django.utils import timezone

class Credencial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_unico = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_emision = models.DateField(default=timezone.now)
    fecha_expiracion = models.DateField()
    estado = models.BooleanField(default=True)

    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='credenciales'
    )

    def __str__(self):
        return str(self.codigo_unico)