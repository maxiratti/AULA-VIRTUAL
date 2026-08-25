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


def notificar_nueva_entrega(
    entrega,
    numero_intento=1,
    es_reentrega=False,
):
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

    titulo = (
        "Nueva reentrega recibida"
        if es_reentrega
        else "Nueva entrega recibida"
    )

    clave = (
        f"entrega_nueva:"
        f"{entrega.pk}:"
        f"{numero_intento}"
    )

    docentes = curso.docentes.all()

    for docente in docentes:
        Notificacion.objects.update_or_create(
            usuario=docente,
            clave=clave,
            defaults={
                "tipo": Notificacion.TIPO_ENTREGA,
                "titulo": titulo,
                "mensaje": (
                    f"{nombre_alumno} entregó "
                    f"“{actividad.titulo}” "
                    f"en {curso.nombre}."
                ),
                "url": url,
                "leida": False,
                "fecha_lectura": None,
            },
        )


def notificar_entrega_corregida(
    entrega,
    numero_intento=1,
):
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
            f"{entrega.pk}:"
            f"{numero_intento}"
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



def notificar_curso_finalizado(curso):
    inscripciones = (
        Inscripcion.objects
        .filter(curso=curso)
        .select_related("alumno")
    )

    url = reverse(
        "detalle_curso_alumno",
        kwargs={"pk": curso.pk},
    )

    for inscripcion in inscripciones:
        Notificacion.objects.get_or_create(
            usuario=inscripcion.alumno,
            clave=f"curso_finalizado:{curso.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Curso finalizado",
                "mensaje": (
                    f"Finalizó el curso “{curso.nombre}”. "
                    "Podés seguir consultando sus contenidos, "
                    "actividades y calificaciones."
                ),
                "url": url,
            },
        )


def notificar_aviso_curso(aviso):
    if not aviso.visible:
        return

    curso = aviso.curso

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
        "detalle_curso_alumno",
        kwargs={"pk": curso.pk},
    ) + f"#aviso-{aviso.pk}"

    for inscripcion in inscripciones:
        Notificacion.objects.get_or_create(
            usuario=inscripcion.alumno,
            clave=f"aviso_curso:{aviso.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Nuevo aviso del curso",
                "mensaje": (
                    f"{curso.nombre}: {aviso.titulo}"
                ),
                "url": url,
            },
        )


def notificar_mensaje_curso(mensaje):
    conversacion = mensaje.conversacion
    curso = conversacion.curso
    alumno = conversacion.alumno

    url_alumno = reverse(
        "mensajeria_alumno",
        kwargs={"pk": curso.pk},
    )

    if mensaje.autor_id == alumno.pk:
        nombre_alumno = (
            alumno.get_full_name()
            or alumno.username
        )

        docentes = curso.docentes.all()

        for docente in docentes:
            Notificacion.objects.create(
                usuario=docente,
                tipo=Notificacion.TIPO_SISTEMA,
                titulo="Nueva consulta de alumno",
                mensaje=(
                    f"{nombre_alumno} envió un mensaje "
                    f"en {curso.nombre}."
                ),
                url=reverse(
                    "mensajeria_docente_conversacion",
                    kwargs={
                        "curso_pk": curso.pk,
                        "alumno_pk": alumno.pk,
                    },
                ),
            )

    else:
        Notificacion.objects.create(
            usuario=alumno,
            tipo=Notificacion.TIPO_SISTEMA,
            titulo="Nueva respuesta del curso",
            mensaje=(
                f"Tenés una nueva respuesta "
                f"en {curso.nombre}."
            ),
            url=url_alumno,
        )
