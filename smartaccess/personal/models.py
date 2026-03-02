class Personal(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    codigo_profesor = models.CharField(max_length=20, unique=True)
    departamento = models.CharField(max_length=100)
    tipo_contrato = models.CharField(max_length=50)

    def __str__(self):
        return self.codigo_profesor