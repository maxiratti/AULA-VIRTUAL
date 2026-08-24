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

class NuevoAlumnoCursoForm(forms.Form):

    nombre = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    apellido = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    password = forms.CharField(
        label="Contraseña provisoria",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if Usuario.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "Ya existe un usuario con ese nombre de usuario."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()

        if email and Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe un usuario con ese email."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")

        if (
            password
            and confirmar_password
            and password != confirmar_password
        ):
            self.add_error(
                "confirmar_password",
                "Las contraseñas no coinciden.",
            )

        return cleaned_data
