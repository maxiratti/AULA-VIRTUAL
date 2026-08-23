from django.urls import reverse

from apps.inscripciones.models import Inscripcion

from .models import Notificacion


def notificar_actividad_publicada(actividad):
    if not actividad.visible:
        return

    curso = actividad.clase.modulo.curso

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
    )

    url = reverse(
        "detalle_actividad_alumno",
        kwargs={
            "pk": actividad.pk,
        },
    )

    for inscripcion in inscripciones:
        Notificacion.objects.get_or_create(
            usuario=inscripcion.alumno,
            clave=(
                f"actividad_publicada:"
                f"{actividad.pk}"
            ),
            defaults={
                "tipo": Notificacion.TIPO_ACTIVIDAD,
                "titulo": "Nueva actividad",
                "mensaje": (
                    f"Se publicó “{actividad.titulo}” "
                    f"en {curso.nombre}."
                ),
                "url": url,
            },
        )


def notificar_nueva_entrega(entrega):
    actividad = entrega.actividad
    curso = actividad.clase.modulo.curso

    alumno = entrega.alumno

    nombre_alumno = (
        alumno.get_full_name()
        or alumno.username
    )

    url = reverse(
        "corregir_entrega",
        kwargs={
            "pk": entrega.pk,
        },
    )

    docentes = curso.docentes.all()

    for docente in docentes:
        Notificacion.objects.get_or_create(
            usuario=docente,
            clave=(
                f"entrega_nueva:"
                f"{entrega.pk}"
            ),
            defaults={
                "tipo": Notificacion.TIPO_ENTREGA,
                "titulo": "Nueva entrega recibida",
                "mensaje": (
                    f"{nombre_alumno} entregó "
                    f"“{actividad.titulo}” "
                    f"en {curso.nombre}."
                ),
                "url": url,
            },
        )


def notificar_entrega_corregida(entrega):
    actividad = entrega.actividad
    curso = actividad.clase.modulo.curso

    url = reverse(
        "detalle_actividad_alumno",
        kwargs={
            "pk": actividad.pk,
        },
    )

    Notificacion.objects.update_or_create(
        usuario=entrega.alumno,
        clave=(
            f"entrega_corregida:"
            f"{entrega.pk}"
        ),
        defaults={
            "tipo": Notificacion.TIPO_CORRECCION,
            "titulo": "Actividad corregida",
            "mensaje": (
                f"Tu entrega de "
                f"“{actividad.titulo}” "
                f"en {curso.nombre} fue corregida."
            ),
            "url": url,
            "leida": False,
            "fecha_lectura": None,
        },
    )