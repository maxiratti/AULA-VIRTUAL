from django import forms

from .models import Actividad, Entrega


class ActividadForm(forms.ModelForm):

    class Meta:
        model = Actividad

        fields = [
            "titulo",
            "consigna",
            "archivo_adjunto",
            "fecha_apertura",
            "fecha_limite",
            "puntaje_maximo",
            "permite_texto",
            "permite_archivo",
            "visible",
        ]

        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Título de la actividad",
                }
            ),
            "consigna": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": "Escribí la consigna de la actividad",
                }
            ),
            "archivo_adjunto": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "fecha_apertura": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "fecha_limite": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "puntaje_maximo": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "permite_texto": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "permite_archivo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "visible": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["fecha_apertura"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]

        self.fields["fecha_limite"].input_formats = [
            "%Y-%m-%dT%H:%M"
        ]

    def clean(self):
        cleaned_data = super().clean()

        fecha_apertura = cleaned_data.get(
            "fecha_apertura"
        )

        fecha_limite = cleaned_data.get(
            "fecha_limite"
        )

        permite_texto = cleaned_data.get(
            "permite_texto"
        )

        permite_archivo = cleaned_data.get(
            "permite_archivo"
        )

        if (
            fecha_apertura
            and fecha_limite
            and fecha_limite < fecha_apertura
        ):
            self.add_error(
                "fecha_limite",
                (
                    "La fecha límite no puede ser "
                    "anterior a la fecha de apertura."
                ),
            )

        if not permite_texto and not permite_archivo:
            raise forms.ValidationError(
                (
                    "La actividad debe permitir al menos "
                    "una forma de entrega: texto o archivo."
                )
            )

        return cleaned_data


class EntregaForm(forms.ModelForm):

    class Meta:
        model = Entrega

        fields = [
            "texto",
            "archivo",
        ]

        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": (
                        "Escribí aquí tu respuesta..."
                    ),
                }
            ),
            "archivo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def __init__(
        self,
        *args,
        actividad=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.actividad = actividad

        if actividad:
            if not actividad.permite_texto:
                self.fields.pop(
                    "texto",
                    None,
                )

            if not actividad.permite_archivo:
                self.fields.pop(
                    "archivo",
                    None,
                )

    def clean(self):
        cleaned_data = super().clean()

        if not self.actividad:
            return cleaned_data

        texto = cleaned_data.get(
            "texto",
            "",
        ).strip()

        archivo = cleaned_data.get(
            "archivo"
        )

        if (
            self.actividad.permite_texto
            and self.actividad.permite_archivo
            and not texto
            and not archivo
        ):
            raise forms.ValidationError(
                (
                    "Escribí una respuesta o "
                    "adjuntá un archivo."
                )
            )

        if (
            self.actividad.permite_texto
            and not self.actividad.permite_archivo
            and not texto
        ):
            self.add_error(
                "texto",
                "Escribí una respuesta.",
            )

        if (
            self.actividad.permite_archivo
            and not self.actividad.permite_texto
            and not archivo
        ):
            self.add_error(
                "archivo",
                "Adjuntá un archivo.",
            )

        return cleaned_data


class CorreccionEntregaForm(forms.ModelForm):

    class Meta:
        model = Entrega

        fields = [
            "calificacion",
            "devolucion",
        ]

        widgets = {
            "calificacion": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "Ej. 8.50",
                }
            ),
            "devolucion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": (
                        "Escribí una devolución para el alumno..."
                    ),
                }
            ),
        }

    def __init__(
        self,
        *args,
        actividad=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.actividad = actividad

        if actividad:
            self.fields["calificacion"].widget.attrs[
                "max"
            ] = actividad.puntaje_maximo

    def clean_calificacion(self):
        calificacion = self.cleaned_data.get(
            "calificacion"
        )

        if (
            calificacion is not None
            and self.actividad
            and calificacion
            > self.actividad.puntaje_maximo
        ):
            raise forms.ValidationError(
                (
                    "La calificación no puede superar "
                    f"{self.actividad.puntaje_maximo} puntos."
                )
            )

        return calificacion