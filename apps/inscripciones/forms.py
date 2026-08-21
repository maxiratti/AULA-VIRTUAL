from django import forms

from apps.usuarios.models import Usuario

from .models import Inscripcion


class InscripcionForm(forms.ModelForm):

    class Meta:
        model = Inscripcion

        fields = [
            "alumno",
            "estado",
        ]

        widgets = {
            "alumno": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-select",
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

        if not curso:
            self.fields["alumno"].queryset = (
                Usuario.objects.none()
            )
            return

        alumnos = (
            Usuario.objects
            .filter(
                is_active=True,
                membresias__institucion=curso.institucion,
                membresias__activa=True,
                membresias__roles__name="Alumno",
            )
            .order_by(
                "last_name",
                "first_name",
                "username",
            )
            .distinct()
        )

        alumnos_inscriptos = (
            Inscripcion.objects
            .filter(curso=curso)
            .exclude(pk=self.instance.pk)
            .values_list(
                "alumno_id",
                flat=True,
            )
        )

        self.fields["alumno"].queryset = (
            alumnos.exclude(
                pk__in=alumnos_inscriptos
            )
        )

    def clean_alumno(self):
        alumno = self.cleaned_data["alumno"]

        if not self.curso:
            return alumno

        tiene_rol_alumno = (
            alumno.membresias
            .filter(
                institucion=self.curso.institucion,
                activa=True,
                roles__name="Alumno",
            )
            .exists()
        )

        if not tiene_rol_alumno:
            raise forms.ValidationError(
                "El usuario no tiene el rol Alumno "
                "en la institución de este curso."
            )

        return alumno


class CargaMasivaAlumnosForm(forms.Form):

    archivo = forms.FileField(
        label="Archivo Excel",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".xlsx",
            }
        ),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]

        if not archivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError(
                "El archivo debe tener formato .xlsx."
            )

        return archivo