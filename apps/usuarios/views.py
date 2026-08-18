from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UsuarioForm
from .models import Usuario


def es_superadministrador(usuario):
    return usuario.is_authenticated and usuario.is_superuser


@user_passes_test(es_superadministrador)
def lista_usuarios(request):
    usuarios = (
        Usuario.objects
        .select_related("institucion")
        .prefetch_related("groups")
        .filter(is_superuser=False)
        .order_by("last_name", "first_name", "username")
    )

    return render(
        request,
        "usuarios/lista.html",
        {
            "usuarios": usuarios,
        },
    )


@user_passes_test(es_superadministrador)
def nuevo_usuario(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Usuario creado correctamente.",
            )

            return redirect("lista_usuarios")

    else:
        form = UsuarioForm()

    return render(
        request,
        "usuarios/form.html",
        {
            "form": form,
            "titulo": "Nuevo usuario",
            "subtitulo": (
                "Creá un usuario y asignalo "
                "a una institución y un rol."
            ),
        },
    )


@user_passes_test(es_superadministrador)
def editar_usuario(request, pk):
    usuario = get_object_or_404(
        Usuario,
        pk=pk,
        is_superuser=False,
    )

    if request.method == "POST":
        form = UsuarioForm(
            request.POST,
            instance=usuario,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Usuario actualizado correctamente.",
            )

            return redirect("lista_usuarios")

    else:
        form = UsuarioForm(
            instance=usuario,
        )

    return render(
        request,
        "usuarios/form.html",
        {
            "form": form,
            "titulo": "Editar usuario",
            "subtitulo": (
                "Actualizá los datos, institución "
                "o rol del usuario."
            ),
        },
    )


@user_passes_test(es_superadministrador)
def cambiar_estado_usuario(request, pk):
    if request.method != "POST":
        return redirect("lista_usuarios")

    usuario = get_object_or_404(
        Usuario,
        pk=pk,
        is_superuser=False,
    )

    usuario.is_active = not usuario.is_active
    usuario.save(
        update_fields=["is_active"]
    )

    estado = (
        "activado"
        if usuario.is_active
        else "desactivado"
    )

    messages.success(
        request,
        f"Usuario {estado} correctamente.",
    )

    return redirect("lista_usuarios")