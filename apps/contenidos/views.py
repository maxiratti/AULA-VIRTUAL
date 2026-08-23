from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone

from apps.inscripciones.models import Inscripcion
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.cursos.models import Curso
from apps.roles.utils import tiene_rol_en_institucion

from .forms import (
    ClaseForm,
    ContenidoClaseForm,
    ModuloForm,
)

from .models import (
    Clase,
    ContenidoClase,
    Modulo,
)



def puede_gestionar_contenido(usuario, curso):
    if usuario.is_superuser:
        return True

    if tiene_rol_en_institucion(
        usuario,
        "Coordinador",
        curso.institucion,
    ):
        return True

    if (
        tiene_rol_en_institucion(
            usuario,
            "Docente",
            curso.institucion,
        )
        and curso.docentes.filter(
            pk=usuario.pk
        ).exists()
    ):
        return True

    return False


@login_required
def lista_modulos(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related(
            "institucion"
        ).prefetch_related(
            "docentes"
        ),
        pk=curso_id,
    )

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    modulos = (
        Modulo.objects
        .filter(curso=curso)
        .prefetch_related("clases")
        .order_by("orden", "id")
    )

    return render(
        request,
        "contenidos/modulos/lista.html",
        {
            "curso": curso,
            "modulos": modulos,
        },
    )


@login_required
def nuevo_modulo(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related(
            "institucion"
        ).prefetch_related(
            "docentes"
        ),
        pk=curso_id,
    )

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ModuloForm(
            request.POST,
            curso=curso,
        )

        if form.is_valid():
            modulo = form.save(commit=False)
            modulo.curso = curso
            modulo.save()

            messages.success(
                request,
                "Módulo creado correctamente.",
            )

            return redirect(
                "lista_modulos",
                curso_id=curso.pk,
            )

    else:
        form = ModuloForm(
            curso=curso,
        )

    return render(
        request,
        "contenidos/modulos/form.html",
        {
            "curso": curso,
            "form": form,
            "titulo": "Nuevo módulo",
        },
    )


@login_required
def editar_modulo(request, pk):
    modulo = get_object_or_404(
        Modulo.objects.select_related(
            "curso",
            "curso__institucion",
        ),
        pk=pk,
    )

    curso = modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ModuloForm(
            request.POST,
            instance=modulo,
            curso=curso,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Módulo actualizado correctamente.",
            )

            return redirect(
                "lista_modulos",
                curso_id=curso.pk,
            )

    else:
        form = ModuloForm(
            instance=modulo,
            curso=curso,
        )

    return render(
        request,
        "contenidos/modulos/form.html",
        {
            "curso": curso,
            "modulo": modulo,
            "form": form,
            "titulo": "Editar módulo",
        },
    )


@login_required
def lista_clases(request, modulo_id):
    modulo = get_object_or_404(
        Modulo.objects.select_related(
            "curso",
            "curso__institucion",
        ),
        pk=modulo_id,
    )

    curso = modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    clases = (
        Clase.objects
        .filter(modulo=modulo)
        .order_by("orden", "id")
    )

    return render(
        request,
        "contenidos/clases/lista.html",
        {
            "curso": curso,
            "modulo": modulo,
            "clases": clases,
        },
    )


@login_required
def nueva_clase(request, modulo_id):
    modulo = get_object_or_404(
        Modulo.objects.select_related(
            "curso",
            "curso__institucion",
        ),
        pk=modulo_id,
    )

    curso = modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ClaseForm(
            request.POST,
            modulo=modulo,
        )

        if form.is_valid():
            clase = form.save(commit=False)
            clase.modulo = modulo
            clase.save()

            messages.success(
                request,
                "Clase creada correctamente.",
            )

            return redirect(
                "lista_clases",
                modulo_id=modulo.pk,
            )

    else:
        form = ClaseForm(
            modulo=modulo,
        )

    return render(
        request,
        "contenidos/clases/form.html",
        {
            "curso": curso,
            "modulo": modulo,
            "form": form,
            "titulo": "Nueva clase",
        },
    )


@login_required
def editar_clase(request, pk):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ),
        pk=pk,
    )

    modulo = clase.modulo
    curso = modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ClaseForm(
            request.POST,
            instance=clase,
            modulo=modulo,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Clase actualizada correctamente.",
            )

            return redirect(
                "lista_clases",
                modulo_id=modulo.pk,
            )

    else:
        form = ClaseForm(
            instance=clase,
            modulo=modulo,
        )

    return render(
        request,
        "contenidos/clases/form.html",
        {
            "curso": curso,
            "modulo": modulo,
            "clase": clase,
            "form": form,
            "titulo": "Editar clase",
        },
    )

@login_required
def detalle_clase(request, pk):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ).prefetch_related(
            "contenidos"
        ),
        pk=pk,
    )

    curso = clase.modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    contenidos = (
        clase.contenidos
        .all()
        .order_by("orden", "id")
    )

    return render(
        request,
        "contenidos/clases/detalle.html",
        {
            "curso": curso,
            "modulo": clase.modulo,
            "clase": clase,
            "contenidos": contenidos,
        },
    )


@login_required
def nuevo_contenido(request, clase_id):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ),
        pk=clase_id,
    )

    curso = clase.modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ContenidoClaseForm(
            request.POST,
            request.FILES,
            clase=clase,
        )

        if form.is_valid():
            contenido = form.save(
                commit=False
            )

            contenido.clase = clase
            contenido.save()

            messages.success(
                request,
                "Contenido agregado correctamente.",
            )

            return redirect(
                "detalle_clase",
                pk=clase.pk,
            )

    else:
        form = ContenidoClaseForm(
            clase=clase,
        )

    return render(
        request,
        "contenidos/contenidos/form.html",
        {
            "curso": curso,
            "modulo": clase.modulo,
            "clase": clase,
            "form": form,
            "titulo": "Agregar contenido",
        },
    )


@login_required
def editar_contenido(request, pk):
    contenido = get_object_or_404(
        ContenidoClase.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        ),
        pk=pk,
    )

    clase = contenido.clase
    curso = clase.modulo.curso

    if not puede_gestionar_contenido(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ContenidoClaseForm(
            request.POST,
            request.FILES,
            instance=contenido,
            clase=clase,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Contenido actualizado correctamente.",
            )

            return redirect(
                "detalle_clase",
                pk=clase.pk,
            )

    else:
        form = ContenidoClaseForm(
            instance=contenido,
            clase=clase,
        )

    return render(
        request,
        "contenidos/contenidos/form.html",
        {
            "curso": curso,
            "modulo": clase.modulo,
            "clase": clase,
            "contenido": contenido,
            "form": form,
            "titulo": "Editar contenido",
        },
    )


@login_required
def detalle_clase_alumno(request, pk):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ),
        pk=pk,
        visible=True,
        modulo__visible=True,
    )

    curso = clase.modulo.curso

    inscripcion = (
        Inscripcion.objects
        .filter(
            curso=curso,
            alumno=request.user,
            estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
        )
        .first()
    )

    if not inscripcion:
        raise PermissionDenied

    if not tiene_rol_en_institucion(
        request.user,
        "Alumno",
        curso.institucion,
    ):
        raise PermissionDenied

    if (
        clase.fecha_publicacion
        and clase.fecha_publicacion > timezone.now()
    ):
        raise PermissionDenied

    contenidos = (
        clase.contenidos
        .filter(
            visible=True,
        )
        .order_by(
            "orden",
            "id",
        )
    )

    return render(
        request,
        "contenidos/clases/detalle_alumno.html",
        {
            "curso": curso,
            "modulo": clase.modulo,
            "clase": clase,
            "contenidos": contenidos,
        },
    )