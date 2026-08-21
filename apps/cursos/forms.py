from django import forms

from apps.usuarios.models import Usuario

from .models import Curso


class CursoForm(forms.ModelForm):

    docentes = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.none(),
        required=False,
        label="Docentes",
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Curso

        fields = [
            "institucion",
            "nombre",
            "descripcion",
            "docentes",
            "fecha_inicio",
            "fecha_fin",
            "carga_horaria",
            "cupo",
            "estado",
        ]

        widgets = {
            "institucion": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_institucion",
                }
            ),
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del curso",
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Descripción breve del curso",
                }
            ),
            "fecha_inicio": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "fecha_fin": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "carga_horaria": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "cupo": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        institucion_id = None

        if self.data.get("institucion"):
            institucion_id = self.data.get("institucion")

        elif self.instance.pk:
            institucion_id = self.instance.institucion_id

        if institucion_id:
            docentes = (
                Usuario.objects
                .filter(
                    is_active=True,
                    membresias__institucion_id=institucion_id,
                    membresias__activa=True,
                    membresias__roles__name="Docente",
                )
                .order_by(
                    "last_name",
                    "first_name",
                    "username",
                )
                .distinct()
            )

        else:
            docentes = Usuario.objects.none()

        self.fields["docentes"].queryset = docentes

    def clean(self):
        cleaned_data = super().clean()

        institucion = cleaned_data.get("institucion")
        docentes = cleaned_data.get("docentes")
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                self.add_error(
                    "fecha_fin",
                    (
                        "La fecha de finalización no puede "
                        "ser anterior al inicio."
                    ),
                )

        if institucion and docentes:
            for docente in docentes:

                es_docente_institucion = (
                    docente.membresias
                    .filter(
                        institucion=institucion,
                        activa=True,
                        roles__name="Docente",
                    )
                    .exists()
                )

                if not es_docente_institucion:
                    self.add_error(
                        "docentes",
                        (
                            f"{docente} no tiene el rol Docente "
                            "activo en esta institución."
                        ),
                    )
                    break

        return cleaned_data