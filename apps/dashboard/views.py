from django.contrib.auth.decorators import login_required
from django.db.models import Count
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

    cantidad_actividades = 0
    actividades_pendientes = 0
    actividades_entregadas = 0
    actividades_corregidas = 0
    progreso = 0

    if es_docente(usuario):
        cursos = (
            Curso.objects
            .filter(docentes=usuario)
            .select_related("institucion")
            .distinct()
        )

    elif es_alumno(usuario):
        cursos = (
            Curso.objects
            .filter(
                inscripciones__alumno=usuario,
            )
            .select_related("institucion")
            .distinct()
        )

        actividades = (
            Actividad.objects
            .filter(
                clase__modulo__curso__in=cursos,
                visible=True,
                clase__visible=True,
                clase__modulo__visible=True,
            )
            .distinct()
        )

        cantidad_actividades = actividades.count()

        entregas = (
            Entrega.objects
            .filter(
                alumno=usuario,
                actividad__in=actividades,
            )
            .select_related(
                "actividad"
            )
        )

        actividades_entregadas = entregas.count()

        actividades_corregidas = (
            entregas
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

    context = {
        "cursos": cursos,
        "cantidad_cursos": cursos.count(),

        "cantidad_actividades": cantidad_actividades,
        "actividades_pendientes": actividades_pendientes,
        "actividades_entregadas": actividades_entregadas,
        "actividades_corregidas": actividades_corregidas,

        "progreso": progreso,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )