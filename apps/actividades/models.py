from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Actividad(models.Model):

    clase = models.ForeignKey(
        "contenidos.Clase",
        on_delete=models.CASCADE,
        related_name="actividades",
    )

    titulo = models.CharField(
        max_length=200,
    )

    consigna = models.TextField()

    archivo_adjunto = models.FileField(
        upload_to="actividades/adjuntos/",
        null=True,
        blank=True,
    )

    fecha_apertura = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_limite = models.DateTimeField(
        null=True,
        blank=True,
    )

    puntaje_maximo = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        validators=[
            MinValueValidator(0),
        ],
    )

    permite_texto = models.BooleanField(
        default=True,
    )

    permite_archivo = models.BooleanField(
        default=True,
    )

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
        ordering = [
            "fecha_limite",
            "id",
        ]

        verbose_name = "actividad"
        verbose_name_plural = "actividades"

    def __str__(self):
        return f"{self.clase} - {self.titulo}"


class Entrega(models.Model):

    ESTADO_ENTREGADA = "ENTREGADA"
    ESTADO_CORREGIDA = "CORREGIDA"
    ESTADO_REHACER = "REHACER"

    ESTADOS = [
        (
            ESTADO_ENTREGADA,
            "Entregada",
        ),
        (
            ESTADO_CORREGIDA,
            "Corregida",
        ),
        (
            ESTADO_REHACER,
            "Requiere nueva entrega",
        ),
    ]

    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name="entregas",
    )

    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="entregas_actividades",
    )

    texto = models.TextField(
        blank=True,
    )

    archivo = models.FileField(
        upload_to="actividades/entregas/",
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_ENTREGADA,
    )

    fecha_entrega = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    calificacion = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
        ],
    )

    devolucion = models.TextField(
        blank=True,
    )

    fecha_correccion = models.DateTimeField(
        null=True,
        blank=True,
    )

    corregido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="entregas_corregidas",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-fecha_entrega",
        ]

        verbose_name = "entrega"
        verbose_name_plural = "entregas"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "actividad",
                    "alumno",
                ],
                name="entrega_unica_por_actividad_alumno",
            )
        ]

    def __str__(self):
        return (
            f"{self.actividad.titulo} - "
            f"{self.alumno}"
        )

class IntentoEntrega(models.Model):

    ESTADO_ENTREGADO = "ENTREGADO"
    ESTADO_REHACER = "REHACER"
    ESTADO_CORREGIDO = "CORREGIDO"

    ESTADOS = [
        (ESTADO_ENTREGADO, "Entregado"),
        (ESTADO_REHACER, "Rehacer"),
        (ESTADO_CORREGIDO, "Corregido"),
    ]

    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.CASCADE,
        related_name="intentos",
    )

    numero = models.PositiveIntegerField()

    texto = models.TextField(blank=True)

    archivo = models.FileField(
        upload_to="actividades/intentos/",
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_ENTREGADO,
    )

    fecha_entrega = models.DateTimeField()

    calificacion = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    devolucion = models.TextField(blank=True)

    fecha_correccion = models.DateTimeField(
        null=True,
        blank=True,
    )

    corregido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="intentos_corregidos",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["entrega", "numero"],
                name="intento_unico_por_entrega_numero",
            )
        ]

    def __str__(self):
        return f"{self.entrega} - intento {self.numero}"
