from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import File
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.contenidos.models import Clase
from apps.cursos.models import Curso
from apps.roles.utils import tiene_rol_en_institucion

from django.utils import timezone

from apps.inscripciones.models import Inscripcion

from .forms import (
    ActividadForm,
    CorreccionEntregaForm,
    EntregaForm,
)

from .models import (
    Actividad,
    Cuestionario,
    Entrega,
    IntentoCuestionario,
    IntentoEntrega,
    OpcionCuestionario,
    PreguntaCuestionario,
    RespuestaCuestionario,
)

from django.urls import reverse

from apps.notificaciones.models import Notificacion

from apps.notificaciones.services import (
    notificar_actividad_publicada,
    notificar_entrega_corregida,
    notificar_nueva_entrega,
    notificar_cuestionario_publicado,
    notificar_cuestionario_realizado,
)



def copiar_archivo_a_intento(entrega, intento):
    """Guarda una copia independiente del archivo de la entrega en el intento."""
    if not entrega.archivo:
        return

    nombre_origen = entrega.archivo.name or ""
    nombre_intento = intento.archivo.name if intento.archivo else ""

    # Si ya está almacenado dentro de actividades/intentos/, no duplicamos.
    if nombre_intento.startswith("actividades/intentos/"):
        return

    entrega.archivo.open("rb")
    try:
        nombre_archivo = nombre_origen.rsplit("/", 1)[-1]
        intento.archivo.save(
            nombre_archivo,
            File(entrega.archivo.file),
            save=False,
        )
        intento.save(update_fields=["archivo"])
    finally:
        entrega.archivo.close()


def crear_intento_desde_entrega(entrega, numero, estado):
    intento = IntentoEntrega.objects.create(
        entrega=entrega,
        numero=numero,
        texto=entrega.texto,
        estado=estado,
        fecha_entrega=entrega.fecha_entrega,
        calificacion=entrega.calificacion,
        devolucion=entrega.devolucion,
        fecha_correccion=entrega.fecha_correccion,
        corregido_por=entrega.corregido_por,
    )
    copiar_archivo_a_intento(entrega, intento)
    return intento


def obtener_o_crear_intento_actual(entrega):
    intento = entrega.intentos.order_by("-numero").first()

    if intento is None:
        intento = crear_intento_desde_entrega(
            entrega=entrega,
            numero=1,
            estado=(
                IntentoEntrega.ESTADO_CORREGIDO
                if entrega.estado == Entrega.ESTADO_CORREGIDA
                else IntentoEntrega.ESTADO_REHACER
                if entrega.estado == Entrega.ESTADO_REHACER
                else IntentoEntrega.ESTADO_ENTREGADO
            ),
        )
    elif (
        intento.archivo
        and not intento.archivo.name.startswith("actividades/intentos/")
        and entrega.archivo
        and intento.archivo.name == entrega.archivo.name
    ):
        # Normaliza intentos creados por la primera versión del historial,
        # que apuntaban al mismo archivo de Entrega.
        copiar_archivo_a_intento(entrega, intento)

    return intento


def puede_gestionar_actividad(usuario, clase):
    curso = clase.modulo.curso

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
def lista_actividades(request, clase_id):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ),
        pk=clase_id,
    )

    if not puede_gestionar_actividad(
        request.user,
        clase,
    ):
        raise PermissionDenied

    actividades = (
        Actividad.objects
        .filter(clase=clase)
        .prefetch_related("entregas")
        .order_by(
            "fecha_limite",
            "id",
        )
    )

    return render(
        request,
        "actividades/lista.html",
        {
            "curso": clase.modulo.curso,
            "modulo": clase.modulo,
            "clase": clase,
            "actividades": actividades,
            "cuestionarios": clase.cuestionarios.all(),
        },
    )


@login_required
def nueva_actividad(request, clase_id):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ),
        pk=clase_id,
    )

    if not puede_gestionar_actividad(
        request.user,
        clase,
    ):
        raise PermissionDenied

    if clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. Sus actividades están disponibles solo para consulta.",
        )
        return redirect("lista_actividades", clase_id=clase.pk)

    if request.method == "POST":
        form = ActividadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            actividad = form.save(
                commit=False
            )

            actividad.clase = clase
            actividad.save()

            notificar_actividad_publicada(
                actividad
            )

            messages.success(
                request,
                "Actividad creada correctamente.",
            )

            return redirect(
                "lista_actividades",
                clase_id=clase.pk,
            )

    else:
        form = ActividadForm()

    return render(
        request,
        "actividades/form.html",
        {
            "curso": clase.modulo.curso,
            "modulo": clase.modulo,
            "clase": clase,
            "form": form,
            "titulo": "Nueva actividad",
        },
    )


@login_required
def editar_actividad(request, pk):
    actividad = get_object_or_404(
        Actividad.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        ),
        pk=pk,
    )

    clase = actividad.clase

    if actividad.clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. La actividad está disponible solo para consulta.",
        )
        return redirect("lista_cursos")

    if not puede_gestionar_actividad(
        request.user,
        clase,
    ):
        raise PermissionDenied

    era_visible = actividad.visible

    if request.method == "POST":
        form = ActividadForm(
            request.POST,
            request.FILES,
            instance=actividad,
        )

        if form.is_valid():
            actividad_editada = form.save()

            if (
                not era_visible
                and actividad_editada.visible
            ):
                notificar_actividad_publicada(
                    actividad_editada
                )

            messages.success(
                request,
                "Actividad actualizada correctamente.",
            )

            return redirect(
                "lista_actividades",
                clase_id=clase.pk,
            )

    else:
        form = ActividadForm(
            instance=actividad,
        )

    return render(
        request,
        "actividades/form.html",
        {
            "curso": clase.modulo.curso,
            "modulo": clase.modulo,
            "clase": clase,
            "actividad": actividad,
            "form": form,
            "titulo": "Editar actividad",
        },
    )

def alumno_puede_acceder_actividad(
    usuario,
    actividad,
):
    curso = actividad.clase.modulo.curso

    inscripciones = Inscripcion.objects.filter(
        curso=curso,
        alumno=usuario,
    )

    if curso.estado == Curso.ESTADO_FINALIZADO:
        # En un curso finalizado el alumno conserva acceso histórico
        # a las actividades, aunque su inscripción ya sea un estado final.
        return inscripciones.exists()

    return inscripciones.filter(
        estado__in=[
            Inscripcion.ESTADO_INSCRIPTO,
            Inscripcion.ESTADO_CURSANDO,
        ]
    ).exists()


@login_required
def detalle_actividad_alumno(request, pk):
    actividad = get_object_or_404(
        Actividad.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        ),
        pk=pk,
        visible=True,
        clase__visible=True,
        clase__modulo__visible=True,
    )

    if not alumno_puede_acceder_actividad(
        request.user,
        actividad,
    ):
        raise PermissionDenied

    ahora = timezone.now()

    disponible = True
    mensaje_bloqueo = ""

    if (
        actividad.fecha_apertura
        and ahora < actividad.fecha_apertura
    ):
        disponible = False
        mensaje_bloqueo = (
            "Esta actividad todavía no está disponible."
        )

    if (
        actividad.fecha_limite
        and ahora > actividad.fecha_limite
    ):
        disponible = False
        mensaje_bloqueo = (
            "El plazo para realizar esta actividad finalizó."
        )

    entrega = (
        Entrega.objects
        .filter(
            actividad=actividad,
            alumno=request.user,
        )
        .first()
    )

    intentos = []

    if entrega:
        obtener_o_crear_intento_actual(entrega)
        intentos = entrega.intentos.select_related(
            "corregido_por"
        ).order_by("numero")

        if entrega.estado == Entrega.ESTADO_REHACER:
            disponible = True
            mensaje_bloqueo = ""

    return render(
        request,
        "actividades/detalle_alumno.html",
        {
            "actividad": actividad,
            "clase": actividad.clase,
            "modulo": actividad.clase.modulo,
            "curso": actividad.clase.modulo.curso,
            "entrega": entrega,
            "intentos": intentos,
            "disponible": disponible,
            "mensaje_bloqueo": mensaje_bloqueo,
        },
    )


@login_required
def entregar_actividad(request, pk):
    actividad = get_object_or_404(
        Actividad.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
        ),
        pk=pk,
        visible=True,
        clase__visible=True,
        clase__modulo__visible=True,
    )

    if actividad.clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. La actividad está disponible solo para consulta.",
        )
        return redirect("lista_cursos")

    if not alumno_puede_acceder_actividad(request.user, actividad):
        raise PermissionDenied

    ahora = timezone.now()
    entrega_existente = Entrega.objects.filter(
        actividad=actividad,
        alumno=request.user,
    ).first()
    es_reentrega = bool(
        entrega_existente
        and entrega_existente.estado == Entrega.ESTADO_REHACER
    )

    if actividad.fecha_apertura and ahora < actividad.fecha_apertura:
        messages.error(request, "La actividad todavía no está disponible.")
        return redirect("detalle_actividad_alumno", pk=actividad.pk)

    if actividad.fecha_limite and ahora > actividad.fecha_limite and not es_reentrega:
        messages.error(request, "El plazo de entrega finalizó.")
        return redirect("detalle_actividad_alumno", pk=actividad.pk)

    if entrega_existente and not es_reentrega:
        messages.info(request, "Ya realizaste la entrega de esta actividad.")
        return redirect("detalle_actividad_alumno", pk=actividad.pk)

    if request.method == "POST":
        form = EntregaForm(
            request.POST,
            request.FILES,
            actividad=actividad,
        )

        if form.is_valid():
            if es_reentrega:
                entrega = entrega_existente
                intento_anterior = obtener_o_crear_intento_actual(entrega)
                numero_intento = intento_anterior.numero + 1

                entrega.texto = form.cleaned_data.get("texto", "")
                archivo_nuevo = form.cleaned_data.get("archivo")
                if archivo_nuevo:
                    entrega.archivo = archivo_nuevo
                else:
                    entrega.archivo = None
                entrega.estado = Entrega.ESTADO_ENTREGADA
                entrega.fecha_entrega = ahora
                entrega.calificacion = None
                entrega.devolucion = ""
                entrega.fecha_correccion = None
                entrega.corregido_por = None
                entrega.save()
            else:
                entrega = form.save(commit=False)
                entrega.actividad = actividad
                entrega.alumno = request.user
                entrega.save()
                numero_intento = 1

            crear_intento_desde_entrega(
                entrega=entrega,
                numero=numero_intento,
                estado=IntentoEntrega.ESTADO_ENTREGADO,
            )

            inscripcion = (
                Inscripcion.objects
                .filter(
                    curso=actividad.clase.modulo.curso,
                    alumno=request.user,
                )
                .first()
            )

            if inscripcion:
                inscripcion.iniciar_cursado()

            notificar_nueva_entrega(
                entrega,
                numero_intento=numero_intento,
                es_reentrega=es_reentrega,
            )

            messages.success(
                request,
                "Tu nueva entrega fue enviada correctamente."
                if es_reentrega
                else "Tu actividad fue entregada correctamente.",
            )
            return redirect("detalle_actividad_alumno", pk=actividad.pk)
    else:
        form = EntregaForm(actividad=actividad)

    return render(
        request,
        "actividades/entregar.html",
        {
            "actividad": actividad,
            "clase": actividad.clase,
            "curso": actividad.clase.modulo.curso,
            "form": form,
            "es_reentrega": es_reentrega,
            "entrega_anterior": entrega_existente if es_reentrega else None,
        },
    )

@login_required
def lista_entregas(request, actividad_id):
    actividad = get_object_or_404(
        Actividad.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        ),
        pk=actividad_id,
    )

    clase = actividad.clase
    curso = clase.modulo.curso

    if not puede_gestionar_actividad(
        request.user,
        clase,
    ):
        raise PermissionDenied

    inscripciones = (
        Inscripcion.objects
        .filter(
            curso=curso,
        )
        .select_related("alumno")
        .order_by(
            "alumno__last_name",
            "alumno__first_name",
            "alumno__username",
        )
    )

    entregas = (
        Entrega.objects
        .filter(
            actividad=actividad,
        )
        .select_related(
            "alumno",
            "corregido_por",
        )
    )

    entregas_por_alumno = {
        entrega.alumno_id: entrega
        for entrega in entregas
    }

    alumnos = []

    for inscripcion in inscripciones:
        entrega = entregas_por_alumno.get(
            inscripcion.alumno_id
        )

        alumnos.append(
            {
                "alumno": inscripcion.alumno,
                "entrega": entrega,
            }
        )

    return render(
        request,
        "actividades/entregas_lista.html",
        {
            "curso": curso,
            "clase": clase,
            "actividad": actividad,
            "alumnos": alumnos,
        },
    )


@login_required
def corregir_entrega(request, pk):
    entrega = get_object_or_404(
        Entrega.objects.select_related(
            "actividad",
            "actividad__clase",
            "actividad__clase__modulo",
            "actividad__clase__modulo__curso",
            "actividad__clase__modulo__curso__institucion",
            "alumno",
        ),
        pk=pk,
    )

    actividad = entrega.actividad
    clase = actividad.clase

    if actividad.clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. La actividad está disponible solo para consulta.",
        )
        return redirect("lista_cursos")

    if not puede_gestionar_actividad(request.user, clase):
        raise PermissionDenied

    intento_actual = obtener_o_crear_intento_actual(entrega)

    if request.method == "POST":
        accion = request.POST.get("accion", "corregir")
        form = CorreccionEntregaForm(
            request.POST,
            instance=entrega,
            actividad=actividad,
        )

        if accion == "rehacer":
            devolucion = request.POST.get("devolucion", "").strip()

            if not devolucion:
                form.add_error(
                    "devolucion",
                    "Escribí una devolución indicando qué debe rehacer el alumno.",
                )
            else:
                entrega.estado = Entrega.ESTADO_REHACER
                entrega.calificacion = None
                entrega.devolucion = devolucion
                entrega.fecha_correccion = timezone.now()
                entrega.corregido_por = request.user
                entrega.save()

                intento_actual.estado = IntentoEntrega.ESTADO_REHACER
                intento_actual.calificacion = None
                intento_actual.devolucion = devolucion
                intento_actual.fecha_correccion = entrega.fecha_correccion
                intento_actual.corregido_por = request.user
                intento_actual.save()

                curso = actividad.clase.modulo.curso
                url_actividad = reverse(
                    "detalle_actividad_alumno",
                    kwargs={"pk": actividad.pk},
                )
                Notificacion.objects.update_or_create(
                    usuario=entrega.alumno,
                    clave=f"entrega_rehacer:{entrega.pk}:{intento_actual.numero}",
                    defaults={
                        "tipo": Notificacion.TIPO_CORRECCION,
                        "titulo": "Tenés que rehacer una actividad",
                        "mensaje": (
                            f"El docente solicitó una nueva entrega de "
                            f"“{actividad.titulo}” en {curso.nombre}."
                        ),
                        "url": url_actividad,
                        "leida": False,
                        "fecha_lectura": None,
                    },
                )
                messages.success(
                    request,
                    "Se solicitó una nueva entrega al alumno.",
                )
                return redirect("lista_entregas", actividad_id=actividad.pk)

        elif form.is_valid():
            entrega = form.save(commit=False)
            entrega.estado = Entrega.ESTADO_CORREGIDA
            entrega.fecha_correccion = timezone.now()
            entrega.corregido_por = request.user
            entrega.save()

            intento_actual.estado = IntentoEntrega.ESTADO_CORREGIDO
            intento_actual.calificacion = entrega.calificacion
            intento_actual.devolucion = entrega.devolucion
            intento_actual.fecha_correccion = entrega.fecha_correccion
            intento_actual.corregido_por = request.user
            intento_actual.save()

            notificar_entrega_corregida(
                entrega,
                numero_intento=intento_actual.numero,
            )
            messages.success(request, "Entrega corregida correctamente.")
            return redirect("lista_entregas", actividad_id=actividad.pk)
    else:
        form = CorreccionEntregaForm(
            instance=entrega,
            actividad=actividad,
        )

    intentos = entrega.intentos.select_related(
        "corregido_por"
    ).order_by("numero")

    return render(
        request,
        "actividades/corregir_entrega.html",
        {
            "curso": clase.modulo.curso,
            "clase": clase,
            "actividad": actividad,
            "entrega": entrega,
            "intentos": intentos,
            "form": form,
        },
    )

@login_required
def mis_calificaciones(request):
    usuario = request.user

    inscripciones = (
        Inscripcion.objects
        .filter(alumno=usuario)
        .filter(
            Q(
                estado__in=[
                    Inscripcion.ESTADO_INSCRIPTO,
                    Inscripcion.ESTADO_CURSANDO,
                ]
            )
            | Q(curso__estado=Curso.ESTADO_FINALIZADO)
        )
        .select_related(
            "curso",
            "curso__institucion",
        )
    )

    cursos_ids = inscripciones.values_list(
        "curso_id",
        flat=True,
    )

    actividades = list(
        Actividad.objects
        .filter(
            clase__modulo__curso_id__in=cursos_ids,
            visible=True,
            clase__visible=True,
            clase__modulo__visible=True,
        )
        .select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        )
        .order_by(
            "clase__modulo__curso__nombre",
            "clase__modulo__orden",
            "clase__orden",
            "id",
        )
        .distinct()
    )

    entregas = (
        Entrega.objects
        .filter(
            alumno=usuario,
            actividad__in=actividades,
        )
    )

    entregas_por_actividad = {
        entrega.actividad_id: entrega
        for entrega in entregas
    }

    ahora = timezone.now()

    cantidad_corregidas = 0
    suma_porcentajes = 0
    cantidad_evaluaciones_calificadas = 0

    for actividad in actividades:
        entrega = entregas_por_actividad.get(
            actividad.pk
        )

        actividad.entrega_alumno = entrega

        if entrega:
            if entrega.estado == Entrega.ESTADO_CORREGIDA:
                actividad.estado_alumno = "CORREGIDA"
                cantidad_corregidas += 1

                if (
                    entrega.calificacion is not None
                    and actividad.puntaje_maximo
                ):
                    porcentaje = (
                        float(entrega.calificacion)
                        / float(actividad.puntaje_maximo)
                    ) * 100

                    suma_porcentajes += porcentaje
                    cantidad_evaluaciones_calificadas += 1

            elif entrega.estado == Entrega.ESTADO_REHACER:
                actividad.estado_alumno = "REHACER"
            else:
                actividad.estado_alumno = "ENTREGADA"

        elif (
            actividad.fecha_apertura
            and actividad.fecha_apertura > ahora
        ):
            actividad.estado_alumno = "PROXIMAMENTE"

        elif (
            actividad.fecha_limite
            and actividad.fecha_limite < ahora
        ):
            actividad.estado_alumno = "VENCIDA"

        else:
            actividad.estado_alumno = "PENDIENTE"

    cuestionarios = list(
        Cuestionario.objects
        .filter(
            clase__modulo__curso_id__in=cursos_ids,
            visible=True,
            clase__visible=True,
            clase__modulo__visible=True,
        )
        .select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        )
        .prefetch_related(
            "preguntas",
        )
        .order_by(
            "clase__modulo__curso__nombre",
            "clase__modulo__orden",
            "clase__orden",
            "id",
        )
        .distinct()
    )

    intentos = (
        IntentoCuestionario.objects
        .filter(
            alumno=usuario,
            cuestionario__in=cuestionarios,
            finalizado=True,
        )
        .select_related(
            "cuestionario",
        )
        .order_by(
            "cuestionario_id",
            "-puntaje_obtenido",
            "numero",
        )
    )

    mejores_intentos = {}

    for intento in intentos:
        if intento.cuestionario_id not in mejores_intentos:
            mejores_intentos[
                intento.cuestionario_id
            ] = intento

    cantidad_cuestionarios_resueltos = 0

    for cuestionario in cuestionarios:
        mejor_intento = mejores_intentos.get(
            cuestionario.pk
        )

        cuestionario.mejor_intento_alumno = mejor_intento
        cuestionario.porcentaje_alumno = None

        if mejor_intento:
            cuestionario.estado_alumno = "AUTOCORREGIDO"
            cantidad_cuestionarios_resueltos += 1

            if cuestionario.puntaje_maximo:
                porcentaje = (
                    float(
                        mejor_intento.puntaje_obtenido
                    )
                    / float(
                        cuestionario.puntaje_maximo
                    )
                ) * 100

                cuestionario.porcentaje_alumno = round(
                    porcentaje
                )

                suma_porcentajes += porcentaje
                cantidad_evaluaciones_calificadas += 1

        else:
            cuestionario.estado_alumno = "PENDIENTE"

    promedio = 0

    if cantidad_evaluaciones_calificadas > 0:
        promedio = round(
            suma_porcentajes
            / cantidad_evaluaciones_calificadas
        )

    return render(
        request,
        "actividades/mis_calificaciones.html",
        {
            "actividades": actividades,
            "cuestionarios": cuestionarios,
            "cantidad_corregidas": cantidad_corregidas,
            "cantidad_cuestionarios_resueltos": (
                cantidad_cuestionarios_resueltos
            ),
            "cantidad_evaluaciones_calificadas": (
                cantidad_evaluaciones_calificadas
            ),
            "promedio": promedio,
        },
    )


@login_required
def libro_calificaciones(request, curso_id):
    from apps.cursos.models import Curso

    curso = get_object_or_404(
        Curso.objects.select_related(
            "institucion",
        ),
        pk=curso_id,
    )

    if request.user.is_superuser:
        puede_acceder = True

    elif tiene_rol_en_institucion(
        request.user,
        "Coordinador",
        curso.institucion,
    ):
        puede_acceder = True

    elif (
        tiene_rol_en_institucion(
            request.user,
            "Docente",
            curso.institucion,
        )
        and curso.docentes.filter(
            pk=request.user.pk
        ).exists()
    ):
        puede_acceder = True

    else:
        puede_acceder = False

    if not puede_acceder:
        raise PermissionDenied


    actividades = list(
        Actividad.objects
        .filter(
            clase__modulo__curso=curso,
        )
        .select_related(
            "clase",
            "clase__modulo",
        )
        .order_by(
            "clase__modulo__orden",
            "clase__orden",
            "id",
        )
    )

    cuestionarios = list(
        Cuestionario.objects
        .filter(
            clase__modulo__curso=curso,
        )
        .select_related(
            "clase",
            "clase__modulo",
        )
        .prefetch_related(
            "preguntas",
        )
        .order_by(
            "clase__modulo__orden",
            "clase__orden",
            "id",
        )
    )


    inscripciones = Inscripcion.objects.filter(
        curso=curso,
    )

    if curso.estado != Curso.ESTADO_FINALIZADO:
        inscripciones = inscripciones.filter(
            estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
        )

    inscripciones = (
        inscripciones
        .select_related(
            "alumno",
        )
        .order_by(
            "alumno__last_name",
            "alumno__first_name",
            "alumno__username",
        )
    )


    entregas = (
        Entrega.objects
        .filter(
            actividad__in=actividades,
            alumno__in=inscripciones.values(
                "alumno_id"
            ),
        )
        .select_related(
            "actividad",
            "alumno",
        )
    )


    entregas_por_clave = {
        (
            entrega.alumno_id,
            entrega.actividad_id,
        ): entrega
        for entrega in entregas
    }

    intentos_cuestionarios = (
        IntentoCuestionario.objects
        .filter(
            cuestionario__in=cuestionarios,
            alumno__in=inscripciones.values(
                "alumno_id"
            ),
            finalizado=True,
        )
        .select_related(
            "cuestionario",
            "alumno",
        )
        .order_by(
            "alumno_id",
            "cuestionario_id",
            "-puntaje_obtenido",
            "numero",
        )
    )

    mejor_intento_por_clave = {}

    for intento in intentos_cuestionarios:
        clave = (
            intento.alumno_id,
            intento.cuestionario_id,
        )

        if clave not in mejor_intento_por_clave:
            mejor_intento_por_clave[clave] = intento


    filas = []

    for inscripcion in inscripciones:
        alumno = inscripcion.alumno

        celdas = []

        suma_porcentajes = 0
        cantidad_calificadas = 0

        for actividad in actividades:
            entrega = entregas_por_clave.get(
                (
                    alumno.pk,
                    actividad.pk,
                )
            )

            estado = "PENDIENTE"
            porcentaje = None

            if entrega:
                if (
                    entrega.estado
                    == Entrega.ESTADO_CORREGIDA
                ):
                    estado = "CORREGIDA"

                    if (
                        entrega.calificacion
                        is not None
                        and actividad.puntaje_maximo
                    ):
                        porcentaje = (
                            float(
                                entrega.calificacion
                            )
                            / float(
                                actividad.puntaje_maximo
                            )
                        ) * 100

                        suma_porcentajes += porcentaje
                        cantidad_calificadas += 1

                elif entrega.estado == Entrega.ESTADO_REHACER:
                    estado = "REHACER"
                else:
                    estado = "ENTREGADA"

            celdas.append(
                {
                    "actividad": actividad,
                    "entrega": entrega,
                    "estado": estado,
                }
            )

        celdas_cuestionarios = []

        for cuestionario in cuestionarios:
            mejor_intento = mejor_intento_por_clave.get(
                (
                    alumno.pk,
                    cuestionario.pk,
                )
            )

            porcentaje = None

            if (
                mejor_intento
                and cuestionario.puntaje_maximo
            ):
                porcentaje = (
                    float(
                        mejor_intento.puntaje_obtenido
                    )
                    / float(
                        cuestionario.puntaje_maximo
                    )
                ) * 100

                suma_porcentajes += porcentaje
                cantidad_calificadas += 1

            celdas_cuestionarios.append(
                {
                    "cuestionario": cuestionario,
                    "intento": mejor_intento,
                    "porcentaje": (
                        round(porcentaje)
                        if porcentaje is not None
                        else None
                    ),
                }
            )


        promedio = None

        if cantidad_calificadas > 0:
            promedio = round(
                suma_porcentajes
                / cantidad_calificadas
            )


        filas.append(
            {
                "alumno": alumno,
                "celdas": celdas,
                "celdas_cuestionarios": celdas_cuestionarios,
                "promedio": promedio,
            }
        )


    return render(
        request,
        "actividades/libro_calificaciones.html",
        {
            "curso": curso,
            "actividades": actividades,
            "cuestionarios": cuestionarios,
            "filas": filas,
        },
    )

@login_required
def calificaciones_docente(request):
    from apps.cursos.models import Curso

    cursos = (
        Curso.objects
        .filter(
            docentes=request.user,
        )
        .select_related(
            "institucion",
        )
        .distinct()
        .order_by(
            "institucion__nombre",
            "nombre",
        )
    )

    return render(
        request,
        "actividades/calificaciones_docente.html",
        {
            "cursos": cursos,
        },
    )


@login_required
def actividades_docente(request):
    from apps.cursos.models import Curso

    if request.user.is_superuser:
        cursos = Curso.objects.filter(
            estado=Curso.ESTADO_ACTIVO,
        )

    else:
        cursos = (
            Curso.objects
            .filter(
                docentes=request.user,
                estado=Curso.ESTADO_ACTIVO,
            )
            .distinct()
        )

    actividades = (
        Actividad.objects
        .filter(
            clase__modulo__curso__in=cursos,
        )
        .select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        )
        .prefetch_related(
            "entregas",
        )
        .order_by(
            "clase__modulo__curso__nombre",
            "clase__modulo__orden",
            "clase__orden",
            "id",
        )
        .distinct()
    )

    actividades_data = []

    for actividad in actividades:
        entregas = list(
            actividad.entregas.all()
        )

        cantidad_entregas = len(
            entregas
        )

        pendientes_correccion = sum(
            1
            for entrega in entregas
            if entrega.estado
            == Entrega.ESTADO_ENTREGADA
        )

        corregidas = sum(
            1
            for entrega in entregas
            if entrega.estado
            == Entrega.ESTADO_CORREGIDA
        )

        actividades_data.append(
            {
                "actividad": actividad,
                "cantidad_entregas": cantidad_entregas,
                "pendientes_correccion": pendientes_correccion,
                "corregidas": corregidas,
            }
        )

    return render(
        request,
        "actividades/actividades_docente.html",
        {
            "actividades_data": actividades_data,
        },
    )

@login_required
def calendario_alumno(request):
    usuario = request.user

    inscripciones = (
        Inscripcion.objects
        .filter(alumno=usuario)
        .filter(
            Q(
                estado__in=[
                    Inscripcion.ESTADO_INSCRIPTO,
                    Inscripcion.ESTADO_CURSANDO,
                ]
            )
            | Q(curso__estado=Curso.ESTADO_FINALIZADO)
        )
        .select_related(
            "curso",
            "curso__institucion",
        )
    )

    cursos_ids = inscripciones.values_list(
        "curso_id",
        flat=True,
    )

    actividades = list(
        Actividad.objects
        .filter(
            clase__modulo__curso_id__in=cursos_ids,
            visible=True,
            clase__visible=True,
            clase__modulo__visible=True,
        )
        .select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        )
        .order_by(
            "fecha_limite",
            "id",
        )
        .distinct()
    )

    entregas = (
        Entrega.objects
        .filter(
            alumno=usuario,
            actividad__in=actividades,
        )
    )

    entregas_por_actividad = {
        entrega.actividad_id: entrega
        for entrega in entregas
    }

    ahora = timezone.now()

    for actividad in actividades:
        entrega = entregas_por_actividad.get(
            actividad.pk
        )

        actividad.entrega_alumno = entrega

        if entrega:
            if entrega.estado == Entrega.ESTADO_CORREGIDA:
                actividad.estado_alumno = "CORREGIDA"
            elif entrega.estado == Entrega.ESTADO_REHACER:
                actividad.estado_alumno = "REHACER"
            else:
                actividad.estado_alumno = "ENTREGADA"

        elif (
            actividad.fecha_apertura
            and actividad.fecha_apertura > ahora
        ):
            actividad.estado_alumno = "PROXIMAMENTE"

        elif (
            actividad.fecha_limite
            and actividad.fecha_limite < ahora
        ):
            actividad.estado_alumno = "VENCIDA"

        else:
            actividad.estado_alumno = "PENDIENTE"

    return render(
        request,
        "actividades/calendario_alumno.html",
        {
            "actividades": actividades,
        },
    )



def cuestionario_tiene_respuestas(cuestionario):
    return cuestionario.intentos.filter(
        finalizado=True,
    ).exists()


def normalizar_orden_preguntas(cuestionario):
    for orden, pregunta in enumerate(
        cuestionario.preguntas.order_by(
            "orden",
            "id",
        ),
        start=1,
    ):
        if pregunta.orden != orden:
            pregunta.orden = orden
            pregunta.save(
                update_fields=["orden"]
            )


def bloquear_edicion_cuestionario_si_corresponde(
    request,
    cuestionario,
):
    if cuestionario_tiene_respuestas(
        cuestionario
    ):
        messages.warning(
            request,
            (
                "Este cuestionario ya tiene respuestas de alumnos. "
                "Las preguntas, opciones, puntajes y orden quedaron "
                "bloqueados para preservar los resultados históricos."
            ),
        )
        return True

    return False

@login_required
def nuevo_cuestionario(request, clase_id):
    clase = get_object_or_404(
        Clase.objects.select_related(
            "modulo",
            "modulo__curso",
            "modulo__curso__institucion",
        ),
        pk=clase_id,
    )

    if not puede_gestionar_actividad(request.user, clase):
        raise PermissionDenied

    if clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. Los cuestionarios están disponibles solo para consulta.",
        )
        return redirect("lista_actividades", clase_id=clase.pk)

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        intentos = request.POST.get("intentos_permitidos", "1").strip()

        if not titulo:
            messages.error(request, "Ingresá un título para el cuestionario.")
        else:
            try:
                intentos = max(1, int(intentos))
            except ValueError:
                intentos = 1

            cuestionario = Cuestionario.objects.create(
                clase=clase,
                titulo=titulo,
                descripcion=descripcion,
                intentos_permitidos=intentos,
                visible=False,
            )
            messages.success(
                request,
                "Cuestionario creado. Ahora agregá las preguntas.",
            )
            return redirect(
                "editar_cuestionario",
                pk=cuestionario.pk,
            )

    return render(
        request,
        "actividades/cuestionario_form.html",
        {
            "clase": clase,
            "curso": clase.modulo.curso,
        },
    )


@login_required
def editar_cuestionario(request, pk):
    cuestionario = get_object_or_404(
        Cuestionario.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        ),
        pk=pk,
    )

    if not puede_gestionar_actividad(
        request.user,
        cuestionario.clase,
    ):
        raise PermissionDenied

    if cuestionario.clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. El cuestionario está disponible solo para consulta.",
        )
        return redirect("lista_actividades", clase_id=cuestionario.clase.pk)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "publicar":
            preguntas = cuestionario.preguntas.prefetch_related("opciones")
            valido = bool(preguntas)

            for pregunta in preguntas:
                opciones = list(pregunta.opciones.all())
                if (
                    len(opciones) < 2
                    or sum(1 for opcion in opciones if opcion.es_correcta) != 1
                ):
                    valido = False
                    break

            if valido:
                cuestionario.visible = True
                cuestionario.save(update_fields=["visible"])
                notificar_cuestionario_publicado(cuestionario)
                messages.success(request, "Cuestionario publicado.")
            else:
                messages.error(
                    request,
                    "Cada pregunta debe tener al menos dos opciones y exactamente una correcta.",
                )

        elif accion == "ocultar":
            cuestionario.visible = False
            cuestionario.save(update_fields=["visible"])
            messages.success(request, "Cuestionario ocultado.")

        return redirect("editar_cuestionario", pk=cuestionario.pk)

    preguntas = cuestionario.preguntas.prefetch_related(
        "opciones"
    )

    intentos_finalizados = cuestionario.intentos.filter(
        finalizado=True,
    )

    tiene_respuestas = intentos_finalizados.exists()

    return render(
        request,
        "actividades/cuestionario_editar.html",
        {
            "cuestionario": cuestionario,
            "preguntas": preguntas,
            "clase": cuestionario.clase,
            "curso": cuestionario.clase.modulo.curso,
            "tiene_respuestas": tiene_respuestas,
            "cantidad_intentos": intentos_finalizados.count(),
            "cantidad_alumnos": (
                intentos_finalizados
                .values("alumno_id")
                .distinct()
                .count()
            ),
        },
    )


@login_required
def nueva_pregunta_cuestionario(request, pk):
    cuestionario = get_object_or_404(
        Cuestionario.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
            "clase__modulo__curso__institucion",
        ),
        pk=pk,
    )

    if not puede_gestionar_actividad(request.user, cuestionario.clase):
        raise PermissionDenied

    if cuestionario.clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. El cuestionario está disponible solo para consulta.",
        )
        return redirect("lista_actividades", clase_id=cuestionario.clase.pk)

    if request.method != "POST":
        return redirect("editar_cuestionario", pk=cuestionario.pk)

    if bloquear_edicion_cuestionario_si_corresponde(
        request,
        cuestionario,
    ):
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    enunciado = request.POST.get("enunciado", "").strip()
    puntaje = request.POST.get("puntaje", "1").strip()
    opciones = [
        request.POST.get(f"opcion_{i}", "").strip()
        for i in range(1, 5)
    ]
    correcta = request.POST.get("correcta", "1")

    opciones_validas = [
        (indice, texto)
        for indice, texto in enumerate(opciones, start=1)
        if texto
    ]

    if not enunciado or len(opciones_validas) < 2:
        messages.error(
            request,
            "Ingresá el enunciado y al menos dos opciones.",
        )
        return redirect("editar_cuestionario", pk=cuestionario.pk)

    try:
        from decimal import Decimal
        puntaje = Decimal(puntaje)
        if puntaje < 0:
            raise ValueError
    except Exception:
        messages.error(request, "El puntaje ingresado no es válido.")
        return redirect("editar_cuestionario", pk=cuestionario.pk)

    try:
        correcta = int(correcta)
    except ValueError:
        correcta = 1

    if correcta not in [indice for indice, _ in opciones_validas]:
        messages.error(
            request,
            "Seleccioná como correcta una opción que tenga texto.",
        )
        return redirect("editar_cuestionario", pk=cuestionario.pk)

    pregunta = PreguntaCuestionario.objects.create(
        cuestionario=cuestionario,
        enunciado=enunciado,
        puntaje=puntaje,
        orden=cuestionario.preguntas.count() + 1,
    )

    for indice, texto in opciones_validas:
        OpcionCuestionario.objects.create(
            pregunta=pregunta,
            texto=texto,
            es_correcta=(indice == correcta),
            orden=indice,
        )

    cuestionario.visible = False
    cuestionario.save(update_fields=["visible"])

    messages.success(request, "Pregunta agregada.")
    return redirect("editar_cuestionario", pk=cuestionario.pk)



@login_required
def editar_pregunta_cuestionario(request, pk):
    pregunta = get_object_or_404(
        PreguntaCuestionario.objects.select_related(
            "cuestionario",
            "cuestionario__clase",
            "cuestionario__clase__modulo",
            "cuestionario__clase__modulo__curso",
            "cuestionario__clase__modulo__curso__institucion",
        ).prefetch_related("opciones"),
        pk=pk,
    )

    cuestionario = pregunta.cuestionario

    if not puede_gestionar_actividad(
        request.user,
        cuestionario.clase,
    ):
        raise PermissionDenied

    if cuestionario.clase.modulo.curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. El cuestionario está disponible solo para consulta.",
        )
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    if bloquear_edicion_cuestionario_si_corresponde(
        request,
        cuestionario,
    ):
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    if request.method != "POST":
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    enunciado = request.POST.get(
        "enunciado",
        "",
    ).strip()
    puntaje = request.POST.get(
        "puntaje",
        "1",
    ).strip()
    opciones = [
        request.POST.get(
            f"opcion_{i}",
            "",
        ).strip()
        for i in range(1, 5)
    ]
    correcta = request.POST.get(
        "correcta",
        "1",
    )

    opciones_validas = [
        (indice, texto)
        for indice, texto in enumerate(
            opciones,
            start=1,
        )
        if texto
    ]

    if (
        not enunciado
        or len(opciones_validas) < 2
    ):
        messages.error(
            request,
            "Ingresá el enunciado y al menos dos opciones.",
        )
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    try:
        from decimal import Decimal

        puntaje = Decimal(puntaje)

        if puntaje < 0:
            raise ValueError
    except Exception:
        messages.error(
            request,
            "El puntaje ingresado no es válido.",
        )
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    try:
        correcta = int(correcta)
    except ValueError:
        correcta = 1

    indices_validos = [
        indice
        for indice, _ in opciones_validas
    ]

    if correcta not in indices_validos:
        messages.error(
            request,
            "Seleccioná como correcta una opción que tenga texto.",
        )
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    pregunta.enunciado = enunciado
    pregunta.puntaje = puntaje
    pregunta.save(
        update_fields=[
            "enunciado",
            "puntaje",
        ]
    )

    pregunta.opciones.all().delete()

    for indice, texto in opciones_validas:
        OpcionCuestionario.objects.create(
            pregunta=pregunta,
            texto=texto,
            es_correcta=(
                indice == correcta
            ),
            orden=indice,
        )

    cuestionario.visible = False
    cuestionario.save(
        update_fields=["visible"]
    )

    messages.success(
        request,
        "Pregunta actualizada. El cuestionario volvió a borrador para que revises los cambios.",
    )

    return redirect(
        "editar_cuestionario",
        pk=cuestionario.pk,
    )


@login_required
def eliminar_pregunta_cuestionario(request, pk):
    pregunta = get_object_or_404(
        PreguntaCuestionario.objects.select_related(
            "cuestionario",
            "cuestionario__clase",
            "cuestionario__clase__modulo",
            "cuestionario__clase__modulo__curso",
            "cuestionario__clase__modulo__curso__institucion",
        ),
        pk=pk,
    )

    cuestionario = pregunta.cuestionario

    if not puede_gestionar_actividad(
        request.user,
        cuestionario.clase,
    ):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    if (
        cuestionario.clase.modulo.curso.estado
        == Curso.ESTADO_FINALIZADO
        or bloquear_edicion_cuestionario_si_corresponde(
            request,
            cuestionario,
        )
    ):
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    pregunta.delete()
    normalizar_orden_preguntas(
        cuestionario
    )

    cuestionario.visible = False
    cuestionario.save(
        update_fields=["visible"]
    )

    messages.success(
        request,
        "Pregunta eliminada.",
    )

    return redirect(
        "editar_cuestionario",
        pk=cuestionario.pk,
    )


@login_required
def duplicar_pregunta_cuestionario(request, pk):
    pregunta = get_object_or_404(
        PreguntaCuestionario.objects.select_related(
            "cuestionario",
            "cuestionario__clase",
            "cuestionario__clase__modulo",
            "cuestionario__clase__modulo__curso",
            "cuestionario__clase__modulo__curso__institucion",
        ).prefetch_related("opciones"),
        pk=pk,
    )

    cuestionario = pregunta.cuestionario

    if not puede_gestionar_actividad(
        request.user,
        cuestionario.clase,
    ):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    if (
        cuestionario.clase.modulo.curso.estado
        == Curso.ESTADO_FINALIZADO
        or bloquear_edicion_cuestionario_si_corresponde(
            request,
            cuestionario,
        )
    ):
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    nueva = PreguntaCuestionario.objects.create(
        cuestionario=cuestionario,
        enunciado=f"{pregunta.enunciado} (copia)",
        puntaje=pregunta.puntaje,
        orden=cuestionario.preguntas.count() + 1,
    )

    for opcion in pregunta.opciones.all():
        OpcionCuestionario.objects.create(
            pregunta=nueva,
            texto=opcion.texto,
            es_correcta=opcion.es_correcta,
            orden=opcion.orden,
        )

    cuestionario.visible = False
    cuestionario.save(
        update_fields=["visible"]
    )

    messages.success(
        request,
        "Pregunta duplicada.",
    )

    return redirect(
        "editar_cuestionario",
        pk=cuestionario.pk,
    )


@login_required
def mover_pregunta_cuestionario(request, pk, direccion):
    pregunta = get_object_or_404(
        PreguntaCuestionario.objects.select_related(
            "cuestionario",
            "cuestionario__clase",
            "cuestionario__clase__modulo",
            "cuestionario__clase__modulo__curso",
            "cuestionario__clase__modulo__curso__institucion",
        ),
        pk=pk,
    )

    cuestionario = pregunta.cuestionario

    if not puede_gestionar_actividad(
        request.user,
        cuestionario.clase,
    ):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    if (
        cuestionario.clase.modulo.curso.estado
        == Curso.ESTADO_FINALIZADO
        or bloquear_edicion_cuestionario_si_corresponde(
            request,
            cuestionario,
        )
    ):
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    preguntas = list(
        cuestionario.preguntas.order_by(
            "orden",
            "id",
        )
    )

    indice = next(
        (
            i
            for i, item in enumerate(preguntas)
            if item.pk == pregunta.pk
        ),
        None,
    )

    if indice is None:
        return redirect(
            "editar_cuestionario",
            pk=cuestionario.pk,
        )

    if direccion == "subir":
        destino = indice - 1
    elif direccion == "bajar":
        destino = indice + 1
    else:
        destino = indice

    if 0 <= destino < len(preguntas):
        preguntas[indice], preguntas[destino] = (
            preguntas[destino],
            preguntas[indice],
        )

        for orden, item in enumerate(
            preguntas,
            start=1,
        ):
            if item.orden != orden:
                item.orden = orden
                item.save(
                    update_fields=["orden"]
                )

        cuestionario.visible = False
        cuestionario.save(
            update_fields=["visible"]
        )

        messages.success(
            request,
            "Orden de preguntas actualizado.",
        )

    return redirect(
        "editar_cuestionario",
        pk=cuestionario.pk,
    )

@login_required
def resolver_cuestionario(request, pk):
    cuestionario = get_object_or_404(
        Cuestionario.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
        ).prefetch_related("preguntas__opciones"),
        pk=pk,
        visible=True,
    )

    curso = cuestionario.clase.modulo.curso

    inscripciones_alumno = Inscripcion.objects.filter(
        curso=curso,
        alumno=request.user,
    )

    if curso.estado == Curso.ESTADO_FINALIZADO:
        inscripcion = inscripciones_alumno.first()
    else:
        inscripcion = inscripciones_alumno.filter(
            estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
        ).first()

    if not inscripcion:
        raise PermissionDenied

    if curso.estado == Curso.ESTADO_FINALIZADO:
        messages.info(
            request,
            "El curso está finalizado. El cuestionario se conserva en modo consulta.",
        )
        return redirect(
            "resultado_cuestionario",
            pk=cuestionario.pk,
        )

    ahora = timezone.now()
    if cuestionario.fecha_apertura and ahora < cuestionario.fecha_apertura:
        messages.error(request, "El cuestionario todavía no está disponible.")
        return redirect("detalle_clase_alumno", pk=cuestionario.clase.pk)

    if cuestionario.fecha_limite and ahora > cuestionario.fecha_limite:
        messages.error(request, "El plazo del cuestionario finalizó.")
        return redirect("detalle_clase_alumno", pk=cuestionario.clase.pk)

    realizados = cuestionario.intentos.filter(
        alumno=request.user,
        finalizado=True,
    ).count()

    if realizados >= cuestionario.intentos_permitidos:
        messages.info(request, "Ya utilizaste todos los intentos permitidos.")
        return redirect("resultado_cuestionario", pk=cuestionario.pk)

    if request.method == "POST":
        preguntas = list(cuestionario.preguntas.all())

        if any(
            not request.POST.get(f"pregunta_{pregunta.pk}")
            for pregunta in preguntas
        ):
            messages.error(request, "Respondé todas las preguntas antes de enviar.")
        else:
            intento = IntentoCuestionario.objects.create(
                cuestionario=cuestionario,
                alumno=request.user,
                numero=realizados + 1,
            )

            total = 0
            for pregunta in preguntas:
                opcion = get_object_or_404(
                    OpcionCuestionario,
                    pk=request.POST.get(f"pregunta_{pregunta.pk}"),
                    pregunta=pregunta,
                )
                obtenido = pregunta.puntaje if opcion.es_correcta else 0
                RespuestaCuestionario.objects.create(
                    intento=intento,
                    pregunta=pregunta,
                    opcion=opcion,
                    correcta=opcion.es_correcta,
                    puntaje_obtenido=obtenido,
                )
                total += obtenido

            intento.puntaje_obtenido = total
            intento.fecha_envio = timezone.now()
            intento.finalizado = True
            intento.save(
                update_fields=[
                    "puntaje_obtenido",
                    "fecha_envio",
                    "finalizado",
                ]
            )

            notificar_cuestionario_realizado(intento)

            inscripcion.iniciar_cursado()

            messages.success(
                request,
                "Cuestionario enviado y corregido automáticamente.",
            )
            return redirect("resultado_cuestionario", pk=cuestionario.pk)

    return render(
        request,
        "actividades/cuestionario_resolver.html",
        {
            "cuestionario": cuestionario,
            "curso": curso,
            "intento_numero": realizados + 1,
        },
    )


@login_required
def resultado_cuestionario(request, pk):
    cuestionario = get_object_or_404(
        Cuestionario.objects.select_related(
            "clase",
            "clase__modulo",
            "clase__modulo__curso",
        ),
        pk=pk,
    )

    if not Inscripcion.objects.filter(
        curso=cuestionario.clase.modulo.curso,
        alumno=request.user,
    ).exists():
        raise PermissionDenied

    intentos = (
        cuestionario.intentos
        .filter(
            alumno=request.user,
            finalizado=True,
        )
        .prefetch_related(
            "respuestas__pregunta",
            "respuestas__opcion",
        )
        .order_by("-numero")
    )

    return render(
        request,
        "actividades/cuestionario_resultado.html",
        {
            "cuestionario": cuestionario,
            "curso": cuestionario.clase.modulo.curso,
            "intentos": intentos,
        },
    )
