from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.actividades.models import Actividad, Entrega
from apps.contenidos.models import Clase, ProgresoClase
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

    # =====================================================
    # MÉTRICAS DEL ALUMNO
    # =====================================================

    cantidad_actividades = 0
    actividades_pendientes = 0
    actividades_entregadas = 0
    actividades_rehacer = 0
    actividades_corregidas = 0

    total_clases = 0
    clases_completadas = 0
    progreso = 0

    # =====================================================
    # MÉTRICAS DEL DOCENTE
    # =====================================================

    cantidad_actividades_docente = 0
    entregas_por_corregir = 0
    entregas_corregidas_docente = 0

    usuario_es_docente = es_docente(
        usuario
    )

    usuario_es_alumno = es_alumno(
        usuario
    )

    # =====================================================
    # DOCENTE
    # =====================================================

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

    # =====================================================
    # ALUMNO
    # =====================================================

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

        # -------------------------------------------------
        # ACTIVIDADES
        # -------------------------------------------------

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

        # -------------------------------------------------
        # ACTIVIDADES ENTREGADAS
        #
        # Solamente consideramos resueltas aquellas que:
        #
        # - fueron entregadas y esperan corrección
        # - ya fueron corregidas
        #
        # Una actividad en REHACER vuelve a ser pendiente.
        # -------------------------------------------------

        entregas_resueltas_o_en_revision = (
            entregas_alumno
            .filter(
                estado__in=[
                    Entrega.ESTADO_ENTREGADA,
                    Entrega.ESTADO_CORREGIDA,
                ],
            )
        )

        actividades_entregadas = (
            entregas_resueltas_o_en_revision.count()
        )

        actividades_corregidas = (
            entregas_alumno
            .filter(
                estado=Entrega.ESTADO_CORREGIDA,
            )
            .count()
        )

        actividades_rehacer = (
            entregas_alumno
            .filter(
                estado=Entrega.ESTADO_REHACER,
            )
            .count()
        )

        # -------------------------------------------------
        # PENDIENTES
        #
        # Incluye:
        #
        # - actividades nunca entregadas
        # - actividades que el docente mandó a rehacer
        # -------------------------------------------------

        actividades_pendientes = max(
            cantidad_actividades
            - actividades_entregadas,
            0,
        )

        # -------------------------------------------------
        # PROGRESO REAL DE CLASES
        # -------------------------------------------------

        clases_disponibles = (
            Clase.objects
            .filter(
                modulo__curso__in=cursos_alumno,
                visible=True,
                modulo__visible=True,
            )
            .filter(
                Q(
                    fecha_publicacion__isnull=True
                )
                |
                Q(
                    fecha_publicacion__lte=timezone.now()
                )
            )
            .distinct()
        )

        total_clases = (
            clases_disponibles.count()
        )

        clases_completadas = (
            ProgresoClase.objects
            .filter(
                alumno=usuario,
                clase__in=clases_disponibles,
                completada=True,
            )
            .count()
        )

        if total_clases > 0:
            progreso = round(
                (
                    clases_completadas
                    / total_clases
                )
                * 100
            )

        # Si es solamente alumno,
        # mostramos sus cursos.
        if not usuario_es_docente:
            cursos = cursos_alumno

    # =====================================================
    # CONTEXTO
    # =====================================================

    context = {
        "cursos": cursos,
        "cantidad_cursos": cursos.count(),

        # Alumno - actividades
        "cantidad_actividades": (
            cantidad_actividades
        ),
        "actividades_pendientes": (
            actividades_pendientes
        ),
        "actividades_entregadas": (
            actividades_entregadas
        ),
        "actividades_rehacer": (
            actividades_rehacer
        ),
        "actividades_corregidas": (
            actividades_corregidas
        ),

        # Alumno - progreso
        "total_clases": total_clases,
        "clases_completadas": (
            clases_completadas
        ),
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