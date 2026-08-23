from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from apps.contenidos.models import Clase
from apps.roles.utils import tiene_rol_en_institucion

from django.utils import timezone

from apps.inscripciones.models import Inscripcion

from .forms import (
    ActividadForm,
    CorreccionEntregaForm,
    EntregaForm,
)

from .models import Actividad, Entrega


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

    if not puede_gestionar_actividad(
        request.user,
        clase,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = ActividadForm(
            request.POST,
            request.FILES,
            instance=actividad,
        )

        if form.is_valid():
            form.save()

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

    return Inscripcion.objects.filter(
        curso=curso,
        alumno=usuario,
        estado__in=[
            Inscripcion.ESTADO_INSCRIPTO,
            Inscripcion.ESTADO_CURSANDO,
        ],
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

    return render(
        request,
        "actividades/detalle_alumno.html",
        {
            "actividad": actividad,
            "clase": actividad.clase,
            "modulo": actividad.clase.modulo,
            "curso": actividad.clase.modulo.curso,
            "entrega": entrega,
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

    if not alumno_puede_acceder_actividad(
        request.user,
        actividad,
    ):
        raise PermissionDenied

    ahora = timezone.now()

    if (
        actividad.fecha_apertura
        and ahora < actividad.fecha_apertura
    ):
        messages.error(
            request,
            "La actividad todavía no está disponible.",
        )

        return redirect(
            "detalle_actividad_alumno",
            pk=actividad.pk,
        )

    if (
        actividad.fecha_limite
        and ahora > actividad.fecha_limite
    ):
        messages.error(
            request,
            "El plazo de entrega finalizó.",
        )

        return redirect(
            "detalle_actividad_alumno",
            pk=actividad.pk,
        )

    if Entrega.objects.filter(
        actividad=actividad,
        alumno=request.user,
    ).exists():
        messages.info(
            request,
            "Ya realizaste la entrega de esta actividad.",
        )

        return redirect(
            "detalle_actividad_alumno",
            pk=actividad.pk,
        )

    if request.method == "POST":
        form = EntregaForm(
            request.POST,
            request.FILES,
            actividad=actividad,
        )

        if form.is_valid():
            entrega = form.save(
                commit=False
            )

            entrega.actividad = actividad
            entrega.alumno = request.user
            entrega.save()

            messages.success(
                request,
                "Tu actividad fue entregada correctamente.",
            )

            return redirect(
                "detalle_actividad_alumno",
                pk=actividad.pk,
            )

    else:
        form = EntregaForm(
            actividad=actividad,
        )

    return render(
        request,
        "actividades/entregar.html",
        {
            "actividad": actividad,
            "clase": actividad.clase,
            "curso": actividad.clase.modulo.curso,
            "form": form,
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
            estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
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

    if not puede_gestionar_actividad(
        request.user,
        clase,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = CorreccionEntregaForm(
            request.POST,
            instance=entrega,
            actividad=actividad,
        )

        if form.is_valid():
            entrega = form.save(
                commit=False
            )

            entrega.estado = Entrega.ESTADO_CORREGIDA
            entrega.fecha_correccion = timezone.now()
            entrega.corregido_por = request.user

            entrega.save()

            messages.success(
                request,
                "Entrega corregida correctamente.",
            )

            return redirect(
                "lista_entregas",
                actividad_id=actividad.pk,
            )

    else:
        form = CorreccionEntregaForm(
            instance=entrega,
            actividad=actividad,
        )

    return render(
        request,
        "actividades/corregir_entrega.html",
        {
            "curso": clase.modulo.curso,
            "clase": clase,
            "actividad": actividad,
            "entrega": entrega,
            "form": form,
        },
    )


@login_required
def mis_calificaciones(request):
    usuario = request.user

    inscripciones = (
        Inscripcion.objects
        .filter(
            alumno=usuario,
            estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
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

    promedio = 0

    if cantidad_corregidas > 0:
        promedio = round(
            suma_porcentajes / cantidad_corregidas
        )

    return render(
        request,
        "actividades/mis_calificaciones.html",
        {
            "actividades": actividades,
            "cantidad_corregidas": cantidad_corregidas,
            "promedio": promedio,
        },
    )