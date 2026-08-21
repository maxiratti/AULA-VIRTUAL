from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="usuarios/login.html",
        ),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "usuarios/",
        views.lista_usuarios,
        name="lista_usuarios",
    ),

    path(
        "usuarios/nuevo/",
        views.nuevo_usuario,
        name="nuevo_usuario",
    ),

    path(
        "usuarios/<int:pk>/editar/",
        views.editar_usuario,
        name="editar_usuario",
    ),

    path(
        "usuarios/<int:pk>/estado/",
        views.cambiar_estado_usuario,
        name="cambiar_estado_usuario",
    ),

    path(
        "usuarios/<int:usuario_id>/membresias/nueva/",
        views.nueva_membresia,
        name="nueva_membresia",
    ),

    path(
        "membresias/<int:pk>/editar/",
        views.editar_membresia,
        name="editar_membresia",
    ),

    path(
        "cambiar-password/",
        views.cambiar_password_obligatorio,
        name="cambiar_password_obligatorio",
    ),
]