from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.actividades.models import Actividad, Entrega
from apps.contenidos.models import (
    Clase,
    Modulo,
    ProgresoClase,
)

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

    modulos = list(
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

    clases_publicadas = []

    for modulo in modulos:
        clases_publicadas.extend(
            modulo.clases_publicadas
        )

    total_clases = len(
        clases_publicadas
    )

    clases_completadas_ids = set(
        ProgresoClase.objects
        .filter(
            alumno=request.user,
            clase__in=clases_publicadas,
            completada=True,
        )
        .values_list(
            "clase_id",
            flat=True,
        )
    )

    clases_completadas = len(
        clases_completadas_ids
    )

    if total_clases > 0:
        porcentaje_progreso = round(
            (
                clases_completadas
                / total_clases
            )
            * 100
        )
    else:
        porcentaje_progreso = 0

    for modulo in modulos:
        for clase in modulo.clases_publicadas:
            clase.completada_alumno = (
                clase.pk
                in clases_completadas_ids
            )

    return render(
        request,
        "cursos/detalle_alumno.html",
        {
            "curso": curso,
            "inscripcion": inscripcion,
            "modulos": modulos,
            "total_clases": total_clases,
            "clases_completadas": clases_completadas,
            "porcentaje_progreso": porcentaje_progreso,
        },
    )

@login_required
def seguimiento_curso(request, pk):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=pk,
    )

    puede_ver = (
        request.user.is_superuser
        or curso.docentes.filter(pk=request.user.pk).exists()
        or tiene_rol_en_institucion(
            request.user,
            "Coordinador",
            curso.institucion,
        )
    )

    if not puede_ver:
        raise PermissionDenied

    ahora = timezone.now()

    clases_disponibles = list(
        Clase.objects
        .filter(
            modulo__curso=curso,
            modulo__visible=True,
            visible=True,
        )
        .filter(
            Q(fecha_publicacion__isnull=True)
            | Q(fecha_publicacion__lte=ahora)
        )
        .order_by(
            "modulo__orden",
            "orden",
            "id",
        )
    )

    total_clases = len(clases_disponibles)

    actividades_disponibles = list(
        Actividad.objects
        .filter(
            clase__in=clases_disponibles,
            visible=True,
        )
        .select_related("clase")
        .distinct()
    )

    total_actividades = len(actividades_disponibles)

    inscripciones = list(
        Inscripcion.objects
        .filter(curso=curso)
        .select_related("alumno")
        .order_by(
            "alumno__last_name",
            "alumno__first_name",
            "alumno__username",
        )
    )

    alumnos_ids = [
        inscripcion.alumno_id
        for inscripcion in inscripciones
    ]

    progresos = (
        ProgresoClase.objects
        .filter(
            alumno_id__in=alumnos_ids,
            clase__in=clases_disponibles,
            completada=True,
        )
        .values_list("alumno_id", "clase_id")
    )

    clases_por_alumno = {}

    for alumno_id, clase_id in progresos:
        clases_por_alumno.setdefault(
            alumno_id,
            set(),
        ).add(clase_id)

    entregas = (
        Entrega.objects
        .filter(
            alumno_id__in=alumnos_ids,
            actividad__in=actividades_disponibles,
        )
        .select_related("actividad")
    )

    entregas_por_alumno = {}

    for entrega in entregas:
        entregas_por_alumno.setdefault(
            entrega.alumno_id,
            [],
        ).append(entrega)

    seguimiento = []

    for inscripcion in inscripciones:
        alumno = inscripcion.alumno

        completadas = len(
            clases_por_alumno.get(
                alumno.pk,
                set(),
            )
        )

        if total_clases:
            progreso = round(
                completadas
                / total_clases
                * 100
            )
        else:
            progreso = 0

        entregas_alumno = entregas_por_alumno.get(
            alumno.pk,
            [],
        )

        cantidad_entregadas = sum(
            1
            for entrega in entregas_alumno
            if entrega.estado in [
                Entrega.ESTADO_ENTREGADA,
                Entrega.ESTADO_CORREGIDA,
            ]
        )

        cantidad_corregidas = sum(
            1
            for entrega in entregas_alumno
            if entrega.estado == Entrega.ESTADO_CORREGIDA
        )

        porcentajes_calificados = []

        for entrega in entregas_alumno:
            if (
                entrega.calificacion is not None
                and entrega.actividad.puntaje_maximo
                and entrega.actividad.puntaje_maximo > 0
            ):
                porcentaje = (
                    float(entrega.calificacion)
                    / float(
                        entrega.actividad.puntaje_maximo
                    )
                    * 100
                )

                porcentajes_calificados.append(
                    porcentaje
                )

        promedio = None

        if porcentajes_calificados:
            promedio = round(
                sum(porcentajes_calificados)
                / len(porcentajes_calificados)
            )

        seguimiento.append(
            {
                "inscripcion": inscripcion,
                "alumno": alumno,
                "clases_completadas": completadas,
                "progreso": progreso,
                "actividades_entregadas": cantidad_entregadas,
                "actividades_corregidas": cantidad_corregidas,
                "promedio": promedio,
            }
        )

    return render(
        request,
        "cursos/seguimiento.html",
        {
            "curso": curso,
            "seguimiento": seguimiento,
            "total_clases": total_clases,
            "total_actividades": total_actividades,
        },
    )


@login_required
def seguimiento_alumno(request, curso_pk, alumno_pk):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=curso_pk,
    )

    puede_ver = (
        request.user.is_superuser
        or curso.docentes.filter(pk=request.user.pk).exists()
        or tiene_rol_en_institucion(
            request.user,
            "Coordinador",
            curso.institucion,
        )
    )

    if not puede_ver:
        raise PermissionDenied

    inscripcion = get_object_or_404(
        Inscripcion.objects.select_related("alumno"),
        curso=curso,
        alumno_id=alumno_pk,
    )
    alumno = inscripcion.alumno
    ahora = timezone.now()

    clases = list(
        Clase.objects
        .filter(
            modulo__curso=curso,
            modulo__visible=True,
            visible=True,
        )
        .filter(
            Q(fecha_publicacion__isnull=True)
            | Q(fecha_publicacion__lte=ahora)
        )
        .select_related("modulo")
        .order_by("modulo__orden", "orden", "id")
    )

    clases_completadas_ids = set(
        ProgresoClase.objects
        .filter(
            alumno=alumno,
            clase__in=clases,
            completada=True,
        )
        .values_list("clase_id", flat=True)
    )

    detalle_clases = []
    for clase in clases:
        detalle_clases.append(
            {
                "clase": clase,
                "completada": clase.pk in clases_completadas_ids,
            }
        )

    total_clases = len(clases)
    clases_completadas = len(clases_completadas_ids)
    progreso = (
        round(clases_completadas / total_clases * 100)
        if total_clases
        else 0
    )

    actividades = list(
        Actividad.objects
        .filter(
            clase__in=clases,
            visible=True,
        )
        .select_related("clase", "clase__modulo")
        .order_by(
            "clase__modulo__orden",
            "clase__orden",
            "id",
        )
        .distinct()
    )

    entregas = {
        entrega.actividad_id: entrega
        for entrega in Entrega.objects
        .filter(
            alumno=alumno,
            actividad__in=actividades,
        )
        .select_related("actividad")
    }

    detalle_actividades = []
    porcentajes_calificados = []
    actividades_corregidas = 0

    for actividad in actividades:
        entrega = entregas.get(actividad.pk)
        porcentaje_nota = None

        if entrega and entrega.estado == Entrega.ESTADO_CORREGIDA:
            actividades_corregidas += 1

        if (
            entrega
            and entrega.calificacion is not None
            and actividad.puntaje_maximo
            and actividad.puntaje_maximo > 0
        ):
            porcentaje_nota = round(
                float(entrega.calificacion)
                / float(actividad.puntaje_maximo)
                * 100
            )
            porcentajes_calificados.append(porcentaje_nota)

        detalle_actividades.append(
            {
                "actividad": actividad,
                "entrega": entrega,
                "porcentaje_nota": porcentaje_nota,
            }
        )

    total_actividades = len(actividades)
    actividades_entregadas = sum(
        1
        for entrega in entregas.values()
        if entrega.estado in [
            Entrega.ESTADO_ENTREGADA,
            Entrega.ESTADO_CORREGIDA,
        ]
    )
    actividades_rehacer = sum(
        1
        for entrega in entregas.values()
        if entrega.estado == Entrega.ESTADO_REHACER
    )
    actividades_pendientes = max(
        total_actividades - actividades_entregadas,
        0,
    )
    promedio = (
        round(
            sum(porcentajes_calificados)
            / len(porcentajes_calificados)
        )
        if porcentajes_calificados
        else None
    )

    return render(
        request,
        "cursos/seguimiento_alumno.html",
        {
            "curso": curso,
            "inscripcion": inscripcion,
            "alumno": alumno,
            "detalle_clases": detalle_clases,
            "total_clases": total_clases,
            "clases_completadas": clases_completadas,
            "progreso": progreso,
            "detalle_actividades": detalle_actividades,
            "total_actividades": total_actividades,
            "actividades_entregadas": actividades_entregadas,
            "actividades_pendientes": actividades_pendientes,
            "actividades_rehacer": actividades_rehacer,
            "actividades_corregidas": actividades_corregidas,
            "promedio": promedio,
        },
    )
