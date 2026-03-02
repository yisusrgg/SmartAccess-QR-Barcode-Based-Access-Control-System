class Alumno(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    matricula = models.CharField(max_length=20, unique=True)
    semestre = models.IntegerField()
    carrera = models.CharField(max_length=100)

    def __str__(self):
        return self.matricula