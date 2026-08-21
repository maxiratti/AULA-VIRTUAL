from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    MembresiaInstitucionalForm,
    UsuarioForm,
)
from .models import (
    MembresiaInstitucional,
    Usuario,
)

from django.contrib.auth import update_session_auth_hash

from .forms import (
    CambioPasswordObligatorioForm,
    MembresiaInstitucionalForm,
    UsuarioForm,
)


def es_superadministrador(usuario):
    return (
        usuario.is_authenticated
        and usuario.is_superuser
    )


@user_passes_test(es_superadministrador)
def lista_usuarios(request):
    usuarios = (
        Usuario.objects
        .filter(is_superuser=False)
        .prefetch_related(
            "membresias__institucion",
            "membresias__roles",
        )
        .order_by(
            "last_name",
            "first_name",
            "username",
        )
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
            usuario = form.save()

            messages.success(
                request,
                "Usuario creado correctamente. "
                "Ahora podés asignarle instituciones y roles.",
            )

            return redirect(
                "editar_usuario",
                pk=usuario.pk,
            )

    else:
        form = UsuarioForm()

    return render(
        request,
        "usuarios/form.html",
        {
            "form": form,
            "titulo": "Nuevo usuario",
            "subtitulo": (
                "Creá la cuenta del usuario. "
                "Después podrás asignarle instituciones y roles."
            ),
            "usuario_editado": None,
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

            return redirect(
                "editar_usuario",
                pk=usuario.pk,
            )

    else:
        form = UsuarioForm(
            instance=usuario,
        )

    membresias = (
        usuario.membresias
        .select_related("institucion")
        .prefetch_related("roles")
        .all()
    )

    return render(
        request,
        "usuarios/form.html",
        {
            "form": form,
            "titulo": "Editar usuario",
            "subtitulo": (
                "Actualizá los datos y administrá "
                "sus instituciones y roles."
            ),
            "usuario_editado": usuario,
            "membresias": membresias,
        },
    )


@user_passes_test(es_superadministrador)
def nueva_membresia(request, usuario_id):
    usuario = get_object_or_404(
        Usuario,
        pk=usuario_id,
        is_superuser=False,
    )

    if request.method == "POST":
        form = MembresiaInstitucionalForm(
            request.POST,
            usuario=usuario,
        )

        if form.is_valid():
            membresia = form.save(commit=False)
            membresia.usuario = usuario
            membresia.save()

            form.save_m2m()

            messages.success(
                request,
                "Institución y roles asignados correctamente.",
            )

            return redirect(
                "editar_usuario",
                pk=usuario.pk,
            )

    else:
        form = MembresiaInstitucionalForm(
            usuario=usuario,
        )

    return render(
        request,
        "usuarios/membresia_form.html",
        {
            "form": form,
            "usuario_editado": usuario,
            "titulo": "Agregar institución",
        },
    )


@user_passes_test(es_superadministrador)
def editar_membresia(request, pk):
    membresia = get_object_or_404(
        MembresiaInstitucional.objects
        .select_related(
            "usuario",
            "institucion",
        ),
        pk=pk,
    )

    usuario = membresia.usuario

    if request.method == "POST":
        form = MembresiaInstitucionalForm(
            request.POST,
            instance=membresia,
            usuario=usuario,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Membresía actualizada correctamente.",
            )

            return redirect(
                "editar_usuario",
                pk=usuario.pk,
            )

    else:
        form = MembresiaInstitucionalForm(
            instance=membresia,
            usuario=usuario,
        )

    return render(
        request,
        "usuarios/membresia_form.html",
        {
            "form": form,
            "usuario_editado": usuario,
            "titulo": "Editar institución y roles",
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

@login_required
def cambiar_password_obligatorio(request):
    usuario = request.user

    if not usuario.debe_cambiar_password:
        return redirect("dashboard")

    if request.method == "POST":
        form = CambioPasswordObligatorioForm(
            request.POST
        )

        if form.is_valid():
            password_nueva = (
                form.cleaned_data["password_nueva"]
            )

            usuario.set_password(
                password_nueva
            )

            usuario.debe_cambiar_password = False

            usuario.save(
                update_fields=[
                    "password",
                    "debe_cambiar_password",
                ]
            )

            update_session_auth_hash(
                request,
                usuario,
            )

            messages.success(
                request,
                "Contraseña actualizada correctamente.",
            )

            return redirect("dashboard")

    else:
        form = CambioPasswordObligatorioForm()

    return render(
        request,
        "usuarios/cambiar_password.html",
        {
            "form": form,
        },
    )