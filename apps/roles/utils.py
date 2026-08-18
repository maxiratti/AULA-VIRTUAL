def tiene_rol(usuario, nombre_rol):
    if not usuario.is_authenticated:
        return False

    return usuario.groups.filter(
        name=nombre_rol
    ).exists()


def es_administrador(usuario):
    if not usuario.is_authenticated:
        return False

    return (
        usuario.is_superuser
        or tiene_rol(
            usuario,
            "Administrador institucional",
        )
    )


def es_coordinador(usuario):
    return tiene_rol(
        usuario,
        "Coordinador",
    )


def es_docente(usuario):
    return tiene_rol(
        usuario,
        "Docente",
    )


def es_alumno(usuario):
    return tiene_rol(
        usuario,
        "Alumno",
    )