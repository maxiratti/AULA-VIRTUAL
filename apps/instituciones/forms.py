from django import forms

from .models import Institucion


class InstitucionForm(forms.ModelForm):

    class Meta:
        model = Institucion

        fields = [
            "nombre",
            "identificacion",
            "email",
            "telefono",
            "autoridad_nombre",
            "autoridad_cargo",
            "activa",
        ]

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre de la institución",
                }
            ),
            "identificacion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "CUIT, código o identificación",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "correo@institucion.com",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Teléfono",
                }
            ),
            "autoridad_nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre y apellido de la autoridad",
                }
            ),
            "autoridad_cargo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej.: Director/a, Rector/a, Responsable institucional",
                }
            ),
            "activa": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }