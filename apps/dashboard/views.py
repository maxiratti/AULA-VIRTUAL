from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.actividades.models import Actividad, Entrega
from apps.cursos.models import Curso
from apps.roles.utils import es_alumno, es_docente


@login_required
def dashboard(request):
    usuario = request.user

    if usuario.debe_cambiar_password:
        return redirect(
            "cambiar_password_obligatorio"
        )

    cursos = Curso.objects.none()

    # Métricas del alumno
    cantidad_actividades = 0
    actividades_pendientes = 0
    actividades_entregadas = 0
    actividades_corregidas = 0
    progreso = 0

    # Métricas del docente
    cantidad_actividades_docente = 0
    entregas_por_corregir = 0
    entregas_corregidas_docente = 0

    usuario_es_docente = es_docente(usuario)
    usuario_es_alumno = es_alumno(usuario)

    # DOCENTE
    if usuario_es_docente:
        cursos = (
            Curso.objects
            .filter(
                docentes=usuario,
            )
            .select_related(
                "institucion",
            )
            .distinct()
        )

        actividades_docente = (
            Actividad.objects
            .filter(
                clase__modulo__curso__in=cursos,
            )
            .distinct()
        )

        cantidad_actividades_docente = (
            actividades_docente.count()
        )

        entregas_por_corregir = (
            Entrega.objects
            .filter(
                actividad__in=actividades_docente,
                estado=Entrega.ESTADO_ENTREGADA,
            )
            .count()
        )

        entregas_corregidas_docente = (
            Entrega.objects
            .filter(
                actividad__in=actividades_docente,
                estado=Entrega.ESTADO_CORREGIDA,
            )
            .count()
        )

    # ALUMNO
    if usuario_es_alumno:
        cursos_alumno = (
            Curso.objects
            .filter(
                inscripciones__alumno=usuario,
            )
            .select_related(
                "institucion",
            )
            .distinct()
        )

        actividades_alumno = (
            Actividad.objects
            .filter(
                clase__modulo__curso__in=cursos_alumno,
                visible=True,
                clase__visible=True,
                clase__modulo__visible=True,
            )
            .distinct()
        )

        cantidad_actividades = (
            actividades_alumno.count()
        )

        entregas_alumno = (
            Entrega.objects
            .filter(
                alumno=usuario,
                actividad__in=actividades_alumno,
            )
            .select_related(
                "actividad",
            )
        )

        actividades_entregadas = (
            entregas_alumno.count()
        )

        actividades_corregidas = (
            entregas_alumno
            .filter(
                estado=Entrega.ESTADO_CORREGIDA,
            )
            .count()
        )

        actividades_pendientes = max(
            cantidad_actividades
            - actividades_entregadas,
            0,
        )

        if cantidad_actividades > 0:
            progreso = round(
                (
                    actividades_entregadas
                    / cantidad_actividades
                )
                * 100
            )

        # Si es solamente alumno,
        # mostramos sus cursos en el dashboard.
        if not usuario_es_docente:
            cursos = cursos_alumno

    context = {
        "cursos": cursos,
        "cantidad_cursos": cursos.count(),

        # Alumno
        "cantidad_actividades": cantidad_actividades,
        "actividades_pendientes": actividades_pendientes,
        "actividades_entregadas": actividades_entregadas,
        "actividades_corregidas": actividades_corregidas,
        "progreso": progreso,

        # Docente
        "cantidad_actividades_docente": (
            cantidad_actividades_docente
        ),
        "entregas_por_corregir": (
            entregas_por_corregir
        ),
        "entregas_corregidas_docente": (
            entregas_corregidas_docente
        ),
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )