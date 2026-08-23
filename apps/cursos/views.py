from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.contenidos.models import Clase, Modulo
from apps.inscripciones.models import Inscripcion
from apps.roles.utils import tiene_rol_en_institucion

from .forms import CursoForm
from .models import Curso


def instituciones_coordinadas(usuario):
    if usuario.is_superuser:
        return None

    return (
        usuario.membresias
        .filter(
            activa=True,
            institucion__activa=True,
            roles__name="Coordinador",
        )
        .values_list(
            "institucion_id",
            flat=True,
        )
        .distinct()
    )


@login_required
def lista_cursos(request):
    if request.user.is_superuser:
        cursos = Curso.objects.all()

    else:
        instituciones_ids = instituciones_coordinadas(
            request.user
        )

        if not instituciones_ids:
            raise PermissionDenied

        cursos = Curso.objects.filter(
            institucion_id__in=instituciones_ids
        )

    cursos = (
        cursos
        .select_related("institucion")
        .prefetch_related("docentes")
        .order_by(
            "institucion__nombre",
            "nombre",
        )
    )

    return render(
        request,
        "cursos/lista.html",
        {
            "cursos": cursos,
        },
    )


@login_required
def nuevo_curso(request):
    if request.user.is_superuser:
        instituciones_permitidas = None

    else:
        instituciones_permitidas = (
            request.user.membresias
            .filter(
                activa=True,
                institucion__activa=True,
                roles__name="Coordinador",
            )
            .values_list(
                "institucion_id",
                flat=True,
            )
            .distinct()
        )

        if not instituciones_permitidas:
            raise PermissionDenied

    if request.method == "POST":
        form = CursoForm(request.POST)

        if instituciones_permitidas is not None:
            form.fields["institucion"].queryset = (
                form.fields["institucion"]
                .queryset
                .filter(
                    pk__in=instituciones_permitidas
                )
            )

        if form.is_valid():
            curso = form.save(commit=False)

            if (
                not request.user.is_superuser
                and not tiene_rol_en_institucion(
                    request.user,
                    "Coordinador",
                    curso.institucion,
                )
            ):
                raise PermissionDenied

            curso.save()
            form.save_m2m()

            messages.success(
                request,
                "Curso creado correctamente.",
            )

            return redirect("lista_cursos")

    else:
        form = CursoForm()

        if instituciones_permitidas is not None:
            form.fields["institucion"].queryset = (
                form.fields["institucion"]
                .queryset
                .filter(
                    pk__in=instituciones_permitidas
                )
            )

    return render(
        request,
        "cursos/form.html",
        {
            "form": form,
            "titulo": "Nuevo curso",
            "subtitulo": (
                "Creá un nuevo curso y asigná "
                "sus docentes."
            ),
        },
    )


@login_required
def editar_curso(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=pk,
    )

    if not request.user.is_superuser:
        if not tiene_rol_en_institucion(
            request.user,
            "Coordinador",
            curso.institucion,
        ):
            raise PermissionDenied

    if request.method == "POST":
        form = CursoForm(
            request.POST,
            instance=curso,
        )

        if not request.user.is_superuser:
            instituciones_permitidas = (
                request.user.membresias
                .filter(
                    activa=True,
                    institucion__activa=True,
                    roles__name="Coordinador",
                )
                .values_list(
                    "institucion_id",
                    flat=True,
                )
                .distinct()
            )

            form.fields["institucion"].queryset = (
                form.fields["institucion"]
                .queryset
                .filter(
                    pk__in=instituciones_permitidas
                )
            )

        if form.is_valid():
            curso_editado = form.save(commit=False)

            if (
                not request.user.is_superuser
                and not tiene_rol_en_institucion(
                    request.user,
                    "Coordinador",
                    curso_editado.institucion,
                )
            ):
                raise PermissionDenied

            curso_editado.save()
            form.save_m2m()

            messages.success(
                request,
                "Curso actualizado correctamente.",
            )

            return redirect("lista_cursos")

    else:
        form = CursoForm(
            instance=curso,
        )

        if not request.user.is_superuser:
            instituciones_permitidas = (
                request.user.membresias
                .filter(
                    activa=True,
                    institucion__activa=True,
                    roles__name="Coordinador",
                )
                .values_list(
                    "institucion_id",
                    flat=True,
                )
                .distinct()
            )

            form.fields["institucion"].queryset = (
                form.fields["institucion"]
                .queryset
                .filter(
                    pk__in=instituciones_permitidas
                )
            )

    return render(
        request,
        "cursos/form.html",
        {
            "form": form,
            "titulo": "Editar curso",
            "subtitulo": (
                "Actualizá los datos del curso."
            ),
        },
    )


@login_required
def mis_cursos(request):
    inscripciones = (
        request.user.inscripciones
        .select_related(
            "curso",
            "curso__institucion",
        )
        .filter(
            estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ]
        )
        .order_by(
            "curso__institucion__nombre",
            "curso__nombre",
        )
    )

    return render(
        request,
        "cursos/mis_cursos.html",
        {
            "inscripciones": inscripciones,
        },
    )


@login_required
def detalle_curso_alumno(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related(
            "institucion"
        ),
        pk=pk,
    )

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

    clases_visibles = (
        Clase.objects
        .filter(
            visible=True,
        )
        .filter(
            Q(fecha_publicacion__isnull=True)
            | Q(
                fecha_publicacion__lte=timezone.now()
            )
        )
        .order_by(
            "orden",
            "id",
        )
    )

    modulos = (
        Modulo.objects
        .filter(
            curso=curso,
            visible=True,
        )
        .prefetch_related(
            Prefetch(
                "clases",
                queryset=clases_visibles,
                to_attr="clases_publicadas",
            )
        )
        .order_by(
            "orden",
            "id",
        )
    )

    return render(
        request,
        "cursos/detalle_alumno.html",
        {
            "curso": curso,
            "inscripcion": inscripcion,
            "modulos": modulos,
        },
    )