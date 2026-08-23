from urllib.parse import parse_qs, urlparse

from django import forms

from .models import Clase, ContenidoClase, Modulo


class ModuloForm(forms.ModelForm):

    class Meta:
        model = Modulo
        fields = [
            "titulo",
            "descripcion",
            "orden",
            "visible",
        ]

        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Introducción",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Descripción breve del módulo",
                }
            ),
            "orden": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "visible": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(
        self,
        *args,
        curso=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.curso = curso

        if (
            curso
            and not self.instance.pk
            and not self.is_bound
        ):
            ultimo = (
                Modulo.objects
                .filter(curso=curso)
                .order_by("-orden")
                .first()
            )

            self.fields["orden"].initial = (
                ultimo.orden + 1
                if ultimo
                else 1
            )

    def clean_orden(self):
        orden = self.cleaned_data["orden"]

        if not self.curso:
            return orden

        existe = (
            Modulo.objects
            .filter(
                curso=self.curso,
                orden=orden,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Ya existe un módulo con este orden."
            )

        return orden


class ClaseForm(forms.ModelForm):

    class Meta:
        model = Clase
        fields = [
            "titulo",
            "descripcion",
            "orden",
            "visible",
            "fecha_publicacion",
        ]

        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Presentación del tema",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Descripción breve de la clase",
                }
            ),
            "orden": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "visible": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "fecha_publicacion": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(
        self,
        *args,
        modulo=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.modulo = modulo

        self.fields["fecha_publicacion"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]

        if (
            modulo
            and not self.instance.pk
            and not self.is_bound
        ):
            ultima = (
                Clase.objects
                .filter(modulo=modulo)
                .order_by("-orden")
                .first()
            )

            self.fields["orden"].initial = (
                ultima.orden + 1
                if ultima
                else 1
            )

    def clean_orden(self):
        orden = self.cleaned_data["orden"]

        if not self.modulo:
            return orden

        existe = (
            Clase.objects
            .filter(
                modulo=self.modulo,
                orden=orden,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Ya existe una clase con este orden."
            )

        return orden


class ContenidoClaseForm(forms.ModelForm):

    class Meta:
        model = ContenidoClase
        fields = [
            "tipo",
            "titulo",
            "texto",
            "archivo",
            "url",
            "orden",
            "visible",
        ]

        widgets = {
            "tipo": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_tipo",
                }
            ),
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Título opcional",
                }
            ),
            "texto": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": "Escribí el contenido de texto",
                }
            ),
            "archivo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://...",
                }
            ),
            "orden": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "visible": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(
        self,
        *args,
        clase=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.clase = clase

        if (
            clase
            and not self.instance.pk
            and not self.is_bound
        ):
            ultimo = (
                ContenidoClase.objects
                .filter(clase=clase)
                .order_by("-orden")
                .first()
            )

            self.fields["orden"].initial = (
                ultimo.orden + 1
                if ultimo
                else 1
            )

    def clean_orden(self):
        orden = self.cleaned_data["orden"]

        if not self.clase:
            return orden

        existe = (
            ContenidoClase.objects
            .filter(
                clase=self.clase,
                orden=orden,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "Ya existe un contenido con este orden."
            )

        return orden

    def clean(self):
        cleaned_data = super().clean()

        tipo = cleaned_data.get("tipo")
        texto = cleaned_data.get("texto")
        archivo = cleaned_data.get("archivo")
        url = cleaned_data.get("url")

        if tipo == ContenidoClase.TIPO_TEXTO and not texto:
            self.add_error(
                "texto",
                "Ingresá el contenido de texto.",
            )

        if tipo == ContenidoClase.TIPO_ARCHIVO and not archivo:
            if not self.instance.pk or not self.instance.archivo:
                self.add_error(
                    "archivo",
                    "Seleccioná un archivo.",
                )

        if tipo in [
            ContenidoClase.TIPO_ENLACE,
            ContenidoClase.TIPO_VIDEO,
            ContenidoClase.TIPO_EMBEBIDO,
        ] and not url:
            self.add_error(
                "url",
                "Ingresá una URL.",
            )

        if (
            tipo == ContenidoClase.TIPO_EMBEBIDO
            and url
        ):
            dominio = (
                urlparse(url)
                .netloc
                .lower()
                .split(":")[0]
            )

            dominios_permitidos = {
                "view.genially.com",
            }

            if dominio not in dominios_permitidos:
                self.add_error(
                    "url",
                    (
                        "Actualmente solo se permiten "
                        "recursos embebidos de Genially."
                    ),
                )

        if (
            tipo == ContenidoClase.TIPO_VIDEO
            and url
        ):
            if not obtener_id_youtube(url):
                self.add_error(
                    "url",
                    "Ingresá una URL válida de YouTube.",
                )

        return cleaned_data


def obtener_id_youtube(url):
    try:
        parsed = urlparse(url)
        dominio = parsed.netloc.lower()

        if dominio in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
        }:
            if parsed.path == "/watch":
                return parse_qs(
                    parsed.query
                ).get(
                    "v",
                    [None],
                )[0]

            if parsed.path.startswith("/shorts/"):
                return parsed.path.split("/")[2]

            if parsed.path.startswith("/embed/"):
                return parsed.path.split("/")[2]

        if dominio == "youtu.be":
            return parsed.path.strip("/")

    except (ValueError, IndexError):
        return None

    return None