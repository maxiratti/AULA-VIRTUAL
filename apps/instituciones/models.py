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
    autoridad_nombre = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre de la autoridad",
    )
    autoridad_cargo = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Cargo de la autoridad",
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