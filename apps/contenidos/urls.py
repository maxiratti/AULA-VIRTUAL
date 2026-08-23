from django.urls import path

from . import views


urlpatterns = [
    path(
        "cursos/<int:curso_id>/modulos/",
        views.lista_modulos,
        name="lista_modulos",
    ),
    path(
        "cursos/<int:curso_id>/modulos/nuevo/",
        views.nuevo_modulo,
        name="nuevo_modulo",
    ),
    path(
        "modulos/<int:pk>/editar/",
        views.editar_modulo,
        name="editar_modulo",
    ),

    path(
        "modulos/<int:modulo_id>/clases/",
        views.lista_clases,
        name="lista_clases",
    ),
    path(
        "modulos/<int:modulo_id>/clases/nueva/",
        views.nueva_clase,
        name="nueva_clase",
    ),
    path(
        "clases/<int:pk>/",
        views.detalle_clase,
        name="detalle_clase",
    ),
    path(
        "clases/<int:pk>/editar/",
        views.editar_clase,
        name="editar_clase",
    ),

    path(
        "clases/<int:clase_id>/contenidos/nuevo/",
        views.nuevo_contenido,
        name="nuevo_contenido",
    ),
    path(
        "contenidos/<int:pk>/editar/",
        views.editar_contenido,
        name="editar_contenido",
    ),

    path(
        "mis-cursos/clases/<int:pk>/",
        views.detalle_clase_alumno,
        name="detalle_clase_alumno",
    ),
]