from django.db import models
from django.urls import reverse
from django.utils import timezone

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

def notificar_clase_publicada(clase):
    """
    Crea una sola notificación por alumno cuando una clase ya está
    efectivamente disponible. Si está programada para el futuro, no
    notifica todavía.
    """
    if not clase.visible or not clase.modulo.visible:
        return

    ahora = timezone.now()

    if (
        clase.fecha_publicacion
        and clase.fecha_publicacion > ahora
    ):
        return

    curso = clase.modulo.curso

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
        "detalle_clase_alumno",
        kwargs={"pk": clase.pk},
    )

    for inscripcion in inscripciones:
        Notificacion.objects.get_or_create(
            usuario=inscripcion.alumno,
            clave=f"clase_publicada:{clase.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Nueva clase disponible",
                "mensaje": (
                    f"Ya está disponible “{clase.titulo}” "
                    f"en {curso.nombre}."
                ),
                "url": url,
            },
        )


def sincronizar_notificaciones_clases(usuario):
    """
    Materializa las notificaciones de clases programadas cuya fecha de
    publicación ya llegó. Se ejecuta al cargar una página autenticada,
    por lo que no requiere un proceso en segundo plano.
    """
    from apps.contenidos.models import Clase

    ahora = timezone.now()

    clases_disponibles = (
        Clase.objects
        .filter(
            visible=True,
            modulo__visible=True,
            fecha_publicacion__isnull=False,
            fecha_publicacion__lte=ahora,
            modulo__curso__inscripciones__alumno=usuario,
            modulo__curso__inscripciones__estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
        )
        .select_related(
            "modulo",
            "modulo__curso",
        )
        .distinct()
    )

    for clase in clases_disponibles:
        Notificacion.objects.get_or_create(
            usuario=usuario,
            clave=f"clase_publicada:{clase.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Nueva clase disponible",
                "mensaje": (
                    f"Ya está disponible “{clase.titulo}” "
                    f"en {clase.modulo.curso.nombre}."
                ),
                "url": reverse(
                    "detalle_clase_alumno",
                    kwargs={"pk": clase.pk},
                ),
            },
        )




def notificar_cuestionario_publicado(cuestionario):
    """Notifica a los alumnos cuando el cuestionario está efectivamente disponible."""
    if not cuestionario.visible:
        return

    if not cuestionario.clase.visible or not cuestionario.clase.modulo.visible:
        return

    ahora = timezone.now()
    if cuestionario.fecha_apertura and cuestionario.fecha_apertura > ahora:
        return

    curso = cuestionario.clase.modulo.curso

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
        "resolver_cuestionario",
        kwargs={"pk": cuestionario.pk},
    )

    for inscripcion in inscripciones:
        Notificacion.objects.get_or_create(
            usuario=inscripcion.alumno,
            clave=f"cuestionario_publicado:{cuestionario.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Nuevo cuestionario disponible",
                "mensaje": (
                    f"Ya está disponible “{cuestionario.titulo}” "
                    f"en {curso.nombre}."
                ),
                "url": url,
            },
        )


def sincronizar_notificaciones_cuestionarios(usuario):
    """Materializa cuestionarios programados cuando llega su fecha de apertura."""
    from apps.actividades.models import Cuestionario

    ahora = timezone.now()

    cuestionarios = (
        Cuestionario.objects
        .filter(
            visible=True,
            clase__visible=True,
            clase__modulo__visible=True,
            clase__modulo__curso__inscripciones__alumno=usuario,
            clase__modulo__curso__inscripciones__estado__in=[
                Inscripcion.ESTADO_INSCRIPTO,
                Inscripcion.ESTADO_CURSANDO,
            ],
        )
        .filter(
            models.Q(fecha_apertura__isnull=True)
            | models.Q(fecha_apertura__lte=ahora)
        )
        .filter(
            models.Q(fecha_limite__isnull=True)
            | models.Q(fecha_limite__gte=ahora)
        )
        .exclude(
            intentos__alumno=usuario,
            intentos__finalizado=True,
        )
        .select_related("clase__modulo__curso")
        .distinct()
    )

    for cuestionario in cuestionarios:
        Notificacion.objects.get_or_create(
            usuario=usuario,
            clave=f"cuestionario_publicado:{cuestionario.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Nuevo cuestionario disponible",
                "mensaje": (
                    f"Ya está disponible “{cuestionario.titulo}” "
                    f"en {cuestionario.clase.modulo.curso.nombre}."
                ),
                "url": reverse(
                    "resolver_cuestionario",
                    kwargs={"pk": cuestionario.pk},
                ),
            },
        )


def notificar_cuestionario_realizado(intento):
    """Notifica a todos los docentes del curso cuando un alumno envía un intento."""
    cuestionario = intento.cuestionario
    curso = cuestionario.clase.modulo.curso
    alumno = intento.alumno
    nombre_alumno = alumno.get_full_name() or alumno.username

    url = reverse(
        "editar_cuestionario",
        kwargs={"pk": cuestionario.pk},
    )

    for docente in curso.docentes.all():
        Notificacion.objects.get_or_create(
            usuario=docente,
            clave=f"cuestionario_realizado:{intento.pk}",
            defaults={
                "tipo": Notificacion.TIPO_SISTEMA,
                "titulo": "Cuestionario realizado",
                "mensaje": (
                    f"{nombre_alumno} realizó “{cuestionario.titulo}” "
                    f"en {curso.nombre} (intento {intento.numero})."
                ),
                "url": url,
            },
        )
