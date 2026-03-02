from django.db import models
from usuarios.models import Usuario

class Personal(models.Model):
    usuario = models.OneToOneField(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='personal'
    )
    codigo_profesor = models.CharField(max_length=20, unique=True)
    departamento = models.CharField(max_length=100)
    tipo_contrato = models.CharField(max_length=50)

    def __str__(self):
        return self.codigo_profesor