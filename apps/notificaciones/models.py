from django.conf import settings
from django.db import models


class Notificacion(models.Model):

    TIPO_ACTIVIDAD = "ACTIVIDAD"
    TIPO_ENTREGA = "ENTREGA"
    TIPO_CORRECCION = "CORRECCION"
    TIPO_VENCIMIENTO = "VENCIMIENTO"
    TIPO_SISTEMA = "SISTEMA"

    TIPOS = [
        (
            TIPO_ACTIVIDAD,
            "Actividad",
        ),
        (
            TIPO_ENTREGA,
            "Entrega",
        ),
        (
            TIPO_CORRECCION,
            "Corrección",
        ),
        (
            TIPO_VENCIMIENTO,
            "Vencimiento",
        ),
        (
            TIPO_SISTEMA,
            "Sistema",
        ),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default=TIPO_SISTEMA,
    )

    titulo = models.CharField(
        max_length=200,
    )

    mensaje = models.TextField(
        blank=True,
    )

    url = models.CharField(
        max_length=500,
        blank=True,
    )

    clave = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    leida = models.BooleanField(
        default=False,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_lectura = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-fecha_creacion",
        ]

        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "usuario",
                    "clave",
                ],
                condition=models.Q(
                    clave__isnull=False,
                ),
                name="notificacion_clave_unica_por_usuario",
            )
        ]

    def __str__(self):
        return (
            f"{self.usuario} - "
            f"{self.titulo}"
        )