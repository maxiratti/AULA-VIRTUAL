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
            "activa": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }