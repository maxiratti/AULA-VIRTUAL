from django.conf import settings
from django.db import models


class Curso(models.Model):

    ESTADO_BORRADOR = "BORRADOR"
    ESTADO_ACTIVO = "ACTIVO"
    ESTADO_FINALIZADO = "FINALIZADO"

    ESTADOS = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_FINALIZADO, "Finalizado"),
    ]

    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.PROTECT,
        related_name="cursos",
    )

    nombre = models.CharField(
        max_length=200,
    )

    descripcion = models.TextField(
        blank=True,
    )

    docentes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="cursos_como_docente",
        blank=True,
    )

    fecha_inicio = models.DateField(
        null=True,
        blank=True,
    )

    fecha_fin = models.DateField(
        null=True,
        blank=True,
    )

    carga_horaria = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    cupo = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_BORRADOR,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "curso"
        verbose_name_plural = "cursos"

    def __str__(self):
        return self.nombre