from django.contrib.auth.models import AbstractUser, Group
from django.db import models


class Usuario(AbstractUser):
    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
    )

    debe_cambiar_password = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return self.get_full_name() or self.username


class MembresiaInstitucional(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="membresias",
    )

    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.CASCADE,
        related_name="membresias",
    )

    roles = models.ManyToManyField(
        Group,
        related_name="membresias_institucionales",
        blank=True,
    )

    activa = models.BooleanField(
        default=True,
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "membresía institucional"
        verbose_name_plural = "membresías institucionales"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "usuario",
                    "institucion",
                ],
                name="membresia_unica_usuario_institucion",
            )
        ]

        ordering = [
            "institucion__nombre",
            "usuario__last_name",
            "usuario__first_name",
        ]

    def __str__(self):
        return f"{self.usuario} - {self.institucion}"