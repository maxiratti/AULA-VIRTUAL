from django.db import models


class Institucion(models.Model):
    nombre = models.CharField(
        max_length=200,
        unique=True,
    )
    identificacion = models.CharField(
        max_length=50,
        blank=True,
    )
    email = models.EmailField(
        blank=True,
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
    )
    activa = models.BooleanField(
        default=True,
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "institución"
        verbose_name_plural = "instituciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre