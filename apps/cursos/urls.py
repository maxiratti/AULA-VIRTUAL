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
]