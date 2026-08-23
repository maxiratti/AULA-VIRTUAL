from django.urls import path

from . import views


urlpatterns = [
    path(
        "notificaciones/",
        views.lista_notificaciones,
        name="lista_notificaciones",
    ),
    path(
        "notificaciones/<int:pk>/abrir/",
        views.abrir_notificacion,
        name="abrir_notificacion",
    ),
    path(
        "notificaciones/marcar-todas-leidas/",
        views.marcar_todas_leidas,
        name="marcar_todas_leidas",
    ),
]