from django.urls import path

from . import views


urlpatterns = [
    path(
        "cursos/<int:curso_id>/inscripciones/",
        views.lista_inscripciones,
        name="lista_inscripciones",
    ),
    path(
        "cursos/<int:curso_id>/inscripciones/nueva/",
        views.nueva_inscripcion,
        name="nueva_inscripcion",
    ),
    path(
        "cursos/<int:curso_id>/inscripciones/nuevo-alumno/",
        views.nuevo_alumno_curso,
        name="nuevo_alumno_curso",
    ),
    path(
        "cursos/<int:curso_id>/inscripciones/carga-masiva/",
        views.carga_masiva_alumnos,
        name="carga_masiva_alumnos",
    ),
    path(
        "cursos/<int:curso_id>/inscripciones/plantilla/",
        views.descargar_plantilla_alumnos,
        name="descargar_plantilla_alumnos",
    ),
    path(
        "inscripciones/<int:pk>/editar/",
        views.editar_inscripcion,
        name="editar_inscripcion",
    ),
]