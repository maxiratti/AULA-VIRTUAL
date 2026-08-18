from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.get_full_name() or self.username