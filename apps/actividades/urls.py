from django.urls import path

from . import views


urlpatterns = [
    path(
        "clases/<int:clase_id>/actividades/",
        views.lista_actividades,
        name="lista_actividades",
    ),
    path(
        "clases/<int:clase_id>/actividades/nueva/",
        views.nueva_actividad,
        name="nueva_actividad",
    ),
    path(
        "actividades/<int:pk>/editar/",
        views.editar_actividad,
        name="editar_actividad",
    ),

    path(
        "actividades/<int:actividad_id>/entregas/",
        views.lista_entregas,
        name="lista_entregas",
    ),
    path(
        "entregas/<int:pk>/corregir/",
        views.corregir_entrega,
        name="corregir_entrega",
    ),

    path(
        "mis-actividades/<int:pk>/",
        views.detalle_actividad_alumno,
        name="detalle_actividad_alumno",
    ),
    path(
        "mis-actividades/<int:pk>/entregar/",
        views.entregar_actividad,
        name="entregar_actividad",
    ),

    path(
        "mis-calificaciones/",
        views.mis_calificaciones,
        name="mis_calificaciones",
    ),
]