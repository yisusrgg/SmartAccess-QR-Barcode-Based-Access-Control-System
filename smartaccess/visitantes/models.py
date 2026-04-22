from django.db import models

class Visitante(models.Model):
    nombre = models.CharField(max_length=200)
    curp = models.CharField(max_length=18, unique=True)
    motivo = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)