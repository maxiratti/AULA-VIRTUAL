from django.urls import path

from . import views


urlpatterns = [
    path(
        "instituciones/",
        views.lista_instituciones,
        name="lista_instituciones",
    ),
    path(
        "instituciones/nueva/",
        views.nueva_institucion,
        name="nueva_institucion",
    ),
    path(
        "instituciones/<int:pk>/editar/",
        views.editar_institucion,
        name="editar_institucion",
    ),
    path(
        "instituciones/<int:pk>/estado/",
        views.cambiar_estado_institucion,
        name="cambiar_estado_institucion",
    ),
]