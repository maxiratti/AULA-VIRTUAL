from django.conf import settings
from django.db import models


class Inscripcion(models.Model):

    ESTADO_INSCRIPTO = "INSCRIPTO"
    ESTADO_CURSANDO = "CURSANDO"
    ESTADO_APROBADO = "APROBADO"
    ESTADO_DESAPROBADO = "DESAPROBADO"
    ESTADO_ABANDONO = "ABANDONO"

    ESTADOS = [
        (ESTADO_INSCRIPTO, "Inscripto"),
        (ESTADO_CURSANDO, "Cursando"),
        (ESTADO_APROBADO, "Aprobado"),
        (ESTADO_DESAPROBADO, "Desaprobado"),
        (ESTADO_ABANDONO, "Abandonó"),
    ]

    curso = models.ForeignKey(
        "cursos.Curso",
        on_delete=models.CASCADE,
        related_name="inscripciones",
    )

    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_INSCRIPTO,
    )

    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_finalizacion = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "alumno__last_name",
            "alumno__first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["curso", "alumno"],
                name="inscripcion_unica_por_curso_alumno",
            )
        ]

    def iniciar_cursado(self):
        """
        Pasa automáticamente de INSCRIPTO a CURSANDO cuando el alumno
        comienza a participar en el curso.

        Los estados CURSANDO, APROBADO, DESAPROBADO y ABANDONO no se
        modifican automáticamente.
        """
        if self.estado != self.ESTADO_INSCRIPTO:
            return False

        self.estado = self.ESTADO_CURSANDO
        self.save(update_fields=["estado"])
        return True

    def __str__(self):
        return f"{self.alumno} - {self.curso}"