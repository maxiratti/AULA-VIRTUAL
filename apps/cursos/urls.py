from django.urls import path

from . import views


urlpatterns = [
    path(
        "cursos/",
        views.lista_cursos,
        name="lista_cursos",
    ),
    path(
        "cursos/nuevo/",
        views.nuevo_curso,
        name="nuevo_curso",
    ),
    path(
        "cursos/<int:pk>/editar/",
        views.editar_curso,
        name="editar_curso",
    ),
    path(
        "cursos/<int:pk>/seguimiento/",
        views.seguimiento_curso,
        name="seguimiento_curso",
    ),
    path(
        "cursos/<int:pk>/avisos/",
        views.avisos_curso,
        name="avisos_curso",
    ),
    path(
        "cursos/<int:curso_pk>/avisos/<int:aviso_pk>/editar/",
        views.editar_aviso_curso,
        name="editar_aviso_curso",
    ),
    path(
        "cursos/<int:curso_pk>/avisos/<int:aviso_pk>/eliminar/",
        views.eliminar_aviso_curso,
        name="eliminar_aviso_curso",
    ),
    path(
        "cursos/<int:curso_pk>/alumnos/<int:alumno_pk>/certificado/",
        views.certificado_alumno,
        name="certificado_alumno",
    ),
    path(
        "cursos/<int:pk>/finalizar/",
        views.finalizar_curso,
        name="finalizar_curso",
    ),
    path(
        "cursos/<int:curso_pk>/seguimiento/<int:alumno_pk>/",
        views.seguimiento_alumno,
        name="seguimiento_alumno",
    ),

    path(
        "mis-cursos/",
        views.mis_cursos,
        name="mis_cursos",
    ),
    path(
        "mis-cursos/<int:pk>/",
        views.detalle_curso_alumno,
        name="detalle_curso_alumno",
    ),
]