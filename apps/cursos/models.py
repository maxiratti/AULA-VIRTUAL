import uuid

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

class AvisoCurso(models.Model):

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="avisos",
    )

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="avisos_curso_creados",
    )

    titulo = models.CharField(
        max_length=200,
    )

    mensaje = models.TextField()

    visible = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "aviso del curso"
        verbose_name_plural = "avisos del curso"

    def __str__(self):
        return f"{self.curso} - {self.titulo}"


class Certificado(models.Model):

    ESTADO_VALIDO = "VALIDO"
    ESTADO_ANULADO = "ANULADO"

    ESTADOS = [
        (ESTADO_VALIDO, "Válido"),
        (ESTADO_ANULADO, "Anulado"),
    ]

    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name="certificados",
    )

    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="certificados",
    )

    codigo = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default=ESTADO_VALIDO,
    )

    fecha_emision = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-fecha_emision"]
        constraints = [
            models.UniqueConstraint(
                fields=["curso", "alumno"],
                name="certificado_unico_curso_alumno",
            ),
        ]
        verbose_name = "certificado"
        verbose_name_plural = "certificados"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = (
                "AV-"
                + uuid.uuid4().hex[:16].upper()
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.alumno}"


class ConversacionCurso(models.Model):

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="conversaciones",
    )

    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversaciones_curso",
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-fecha_actualizacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["curso", "alumno"],
                name="conversacion_unica_curso_alumno",
            ),
        ]
        verbose_name = "conversación del curso"
        verbose_name_plural = "conversaciones del curso"

    def __str__(self):
        return f"{self.curso} - {self.alumno}"


class MensajeCurso(models.Model):

    conversacion = models.ForeignKey(
        ConversacionCurso,
        on_delete=models.CASCADE,
        related_name="mensajes",
    )

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mensajes_curso_enviados",
    )

    mensaje = models.TextField()

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["fecha_creacion", "id"]
        verbose_name = "mensaje del curso"
        verbose_name_plural = "mensajes del curso"

    def __str__(self):
        return f"{self.autor} - {self.fecha_creacion:%d/%m/%Y %H:%M}"
