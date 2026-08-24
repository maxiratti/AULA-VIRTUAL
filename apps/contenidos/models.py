from django.conf import settings
from django.db import models


class Modulo(models.Model):

    curso = models.ForeignKey(
        "cursos.Curso",
        on_delete=models.CASCADE,
        related_name="modulos",
    )

    titulo = models.CharField(
        max_length=200,
    )

    descripcion = models.TextField(
        blank=True,
    )

    orden = models.PositiveIntegerField(
        default=1,
    )

    visible = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "orden",
            "id",
        ]

        verbose_name = "módulo"
        verbose_name_plural = "módulos"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "curso",
                    "orden",
                ],
                name="orden_modulo_unico_por_curso",
            )
        ]

    def __str__(self):
        return f"{self.curso} - {self.titulo}"


class Clase(models.Model):

    modulo = models.ForeignKey(
        Modulo,
        on_delete=models.CASCADE,
        related_name="clases",
    )

    titulo = models.CharField(
        max_length=200,
    )

    descripcion = models.TextField(
        blank=True,
    )

    orden = models.PositiveIntegerField(
        default=1,
    )

    visible = models.BooleanField(
        default=True,
    )

    fecha_publicacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "orden",
            "id",
        ]

        verbose_name = "clase"
        verbose_name_plural = "clases"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "modulo",
                    "orden",
                ],
                name="orden_clase_unico_por_modulo",
            )
        ]

    def __str__(self):
        return f"{self.modulo} - {self.titulo}"


class ContenidoClase(models.Model):

    TIPO_TEXTO = "TEXTO"
    TIPO_ARCHIVO = "ARCHIVO"
    TIPO_ENLACE = "ENLACE"
    TIPO_VIDEO = "VIDEO"
    TIPO_EMBEBIDO = "EMBEBIDO"

    TIPOS = [
        (TIPO_TEXTO, "Texto"),
        (TIPO_ARCHIVO, "Archivo"),
        (TIPO_ENLACE, "Enlace"),
        (TIPO_VIDEO, "Video"),
        (TIPO_EMBEBIDO, "Embebido"),
    ]

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name="contenidos",
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
    )

    titulo = models.CharField(
        max_length=200,
        blank=True,
    )

    texto = models.TextField(
        blank=True,
    )

    archivo = models.FileField(
        upload_to="contenidos/",
        null=True,
        blank=True,
    )

    url = models.URLField(
        max_length=1000,
        blank=True,
    )

    orden = models.PositiveIntegerField(
        default=1,
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
            "orden",
            "id",
        ]

        verbose_name = "contenido de clase"
        verbose_name_plural = "contenidos de clase"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "clase",
                    "orden",
                ],
                name="orden_contenido_unico_por_clase",
            )
        ]

    @property
    def youtube_embed_url(self):
        if self.tipo != self.TIPO_VIDEO:
            return ""

        from urllib.parse import parse_qs, urlparse

        try:
            parsed = urlparse(self.url)
            dominio = parsed.netloc.lower()

            video_id = None

            if dominio in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
            }:
                if parsed.path == "/watch":
                    video_id = parse_qs(
                        parsed.query
                    ).get(
                        "v",
                        [None],
                    )[0]

                elif parsed.path.startswith("/shorts/"):
                    video_id = parsed.path.split("/")[2]

                elif parsed.path.startswith("/embed/"):
                    video_id = parsed.path.split("/")[2]

            elif dominio == "youtu.be":
                video_id = parsed.path.strip("/")

            if video_id:
                return (
                    "https://www.youtube-nocookie.com/embed/"
                    f"{video_id}"
                )

        except (ValueError, IndexError):
            pass

        return ""

    def __str__(self):
        return (
            self.titulo
            or f"{self.get_tipo_display()} - {self.clase}"
        )
    


class ProgresoClase(models.Model):

    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progresos_clases",
    )

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name="progresos_alumnos",
    )

    completada = models.BooleanField(
        default=True,
    )

    fecha_completada = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "progreso de clase"
        verbose_name_plural = "progresos de clases"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "alumno",
                    "clase",
                ],
                name="progreso_clase_unico_por_alumno",
            )
        ]

    def __str__(self):
        return (
            f"{self.alumno} - "
            f"{self.clase}"
        )


