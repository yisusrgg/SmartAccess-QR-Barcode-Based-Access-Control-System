from django.db import models
from usuarios.models import Usuario

class Alumno(models.Model):
    usuario = models.OneToOneField(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='alumno'
    )
    matricula = models.CharField(max_length=20, unique=True)
    semestre = models.IntegerField()
    carrera = models.CharField(max_length=100)

    def __str__(self):
        return self.matricula