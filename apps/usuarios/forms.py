from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from apps.instituciones.models import Institucion

from .models import MembresiaInstitucional, Usuario


class UsuarioForm(forms.ModelForm):

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ingresá una contraseña",
            }
        ),
        required=False,
    )

    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repetí la contraseña",
            }
        ),
        required=False,
    )

    class Meta:
        model = Usuario

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "is_active",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Apellido",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre de usuario",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@ejemplo.com",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get(
            "confirmar_password"
        )

        if not self.instance.pk and not password:
            self.add_error(
                "password",
                "La contraseña es obligatoria.",
            )

        if password != confirmar_password:
            raise ValidationError(
                "Las contraseñas no coinciden."
            )

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)

        password = self.cleaned_data.get("password")

        if password:
            usuario.set_password(password)

        if commit:
            usuario.save()

        return usuario


class MembresiaInstitucionalForm(forms.ModelForm):

    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.none(),
        label="Institución",
        empty_label="Seleccioná una institución",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        label="Roles",
        required=True,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = MembresiaInstitucional

        fields = [
            "institucion",
            "roles",
            "activa",
        ]

        widgets = {
            "activa": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(
        self,
        *args,
        usuario=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.usuario = usuario

        instituciones = Institucion.objects.filter(
            activa=True
        )

        if usuario:
            instituciones_usadas = (
                MembresiaInstitucional.objects
                .filter(usuario=usuario)
                .exclude(pk=self.instance.pk)
                .values_list(
                    "institucion_id",
                    flat=True,
                )
            )

            instituciones = instituciones.exclude(
                pk__in=instituciones_usadas
            )

        self.fields["institucion"].queryset = (
            instituciones.order_by("nombre")
        )

        self.fields["roles"].queryset = (
            Group.objects
            .filter(
                name__in=[
                    "Administrador institucional",
                    "Coordinador",
                    "Docente",
                    "Alumno",
                ]
            )
            .order_by("name")
        )

    def clean_institucion(self):
        institucion = self.cleaned_data["institucion"]

        if not self.usuario:
            return institucion

        existe = (
            MembresiaInstitucional.objects
            .filter(
                usuario=self.usuario,
                institucion=institucion,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if existe:
            raise forms.ValidationError(
                "El usuario ya pertenece a esta institución."
            )

        return institucion


class CambioPasswordObligatorioForm(forms.Form):

    password_nueva = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ingresá una nueva contraseña",
                "autocomplete": "new-password",
            }
        ),
    )

    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Repetí la nueva contraseña",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        password_nueva = cleaned_data.get(
            "password_nueva"
        )

        confirmar_password = cleaned_data.get(
            "confirmar_password"
        )

        if (
            password_nueva
            and confirmar_password
            and password_nueva != confirmar_password
        ):
            raise forms.ValidationError(
                "Las contraseñas no coinciden."
            )

        return cleaned_data