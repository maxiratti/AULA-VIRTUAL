from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InstitucionForm
from .models import Institucion


def es_superadministrador(usuario):
    return usuario.is_authenticated and usuario.is_superuser


@user_passes_test(es_superadministrador)
def lista_instituciones(request):
    instituciones = Institucion.objects.all()

    return render(
        request,
        "instituciones/lista.html",
        {
            "instituciones": instituciones,
        },
    )


@user_passes_test(es_superadministrador)
def nueva_institucion(request):
    if request.method == "POST":
        form = InstitucionForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Institución creada correctamente.",
            )

            return redirect("lista_instituciones")

    else:
        form = InstitucionForm()

    return render(
        request,
        "instituciones/form.html",
        {
            "form": form,
            "titulo": "Nueva institución",
            "subtitulo": "Registrá una nueva institución en la plataforma.",
        },
    )


@user_passes_test(es_superadministrador)
def editar_institucion(request, pk):
    institucion = get_object_or_404(
        Institucion,
        pk=pk,
    )

    if request.method == "POST":
        form = InstitucionForm(
            request.POST,
            instance=institucion,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Institución actualizada correctamente.",
            )

            return redirect("lista_instituciones")

    else:
        form = InstitucionForm(
            instance=institucion,
        )

    return render(
        request,
        "instituciones/form.html",
        {
            "form": form,
            "titulo": "Editar institución",
            "subtitulo": "Actualizá los datos de la institución.",
        },
    )


@user_passes_test(es_superadministrador)
def cambiar_estado_institucion(request, pk):
    if request.method != "POST":
        return redirect("lista_instituciones")

    institucion = get_object_or_404(
        Institucion,
        pk=pk,
    )

    institucion.activa = not institucion.activa
    institucion.save(
        update_fields=["activa"]
    )

    estado = (
        "activada"
        if institucion.activa
        else "desactivada"
    )

    messages.success(
        request,
        f"Institución {estado} correctamente.",
    )

    return redirect("lista_instituciones")