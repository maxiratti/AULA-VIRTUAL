from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import Usuario


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

    rol = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=True,
        empty_label="Seleccioná un rol",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    class Meta:
        model = Usuario

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "institucion",
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
            "institucion": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            grupo = self.instance.groups.first()

            if grupo:
                self.fields["rol"].initial = grupo

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

            usuario.groups.clear()

            rol = self.cleaned_data.get("rol")

            if rol:
                usuario.groups.add(rol)

        return usuario