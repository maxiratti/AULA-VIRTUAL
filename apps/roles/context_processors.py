from .utils import (
    es_administrador,
    es_alumno,
    es_coordinador,
    es_docente,
)


def roles_usuario(request):
    usuario = request.user

    if not usuario.is_authenticated:
        return {
            "es_administrador": False,
            "es_coordinador": False,
            "es_docente": False,
            "es_alumno": False,
            "roles_actuales": [],
            "roles_actuales_texto": "",
        }

    if usuario.is_superuser:
        return {
            "es_administrador": True,
            "es_coordinador": False,
            "es_docente": False,
            "es_alumno": False,
            "roles_actuales": ["Superadministrador"],
            "roles_actuales_texto": "Superadministrador",
        }

    roles = list(
        usuario.membresias
        .filter(
            activa=True,
            institucion__activa=True,
        )
        .values_list(
            "roles__name",
            flat=True,
        )
        .exclude(
            roles__name=None,
        )
        .distinct()
        .order_by("roles__name")
    )

    return {
        "es_administrador": es_administrador(usuario),
        "es_coordinador": es_coordinador(usuario),
        "es_docente": es_docente(usuario),
        "es_alumno": es_alumno(usuario),
        "roles_actuales": roles,
        "roles_actuales_texto": " · ".join(roles),
    }