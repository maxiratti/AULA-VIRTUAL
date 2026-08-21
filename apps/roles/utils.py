def tiene_rol(usuario, nombre_rol):
    if not usuario.is_authenticated:
        return False

    return usuario.membresias.filter(
        activa=True,
        institucion__activa=True,
        roles__name=nombre_rol,
    ).exists()


def tiene_rol_en_institucion(
    usuario,
    nombre_rol,
    institucion,
):
    if not usuario.is_authenticated:
        return False

    return usuario.membresias.filter(
        institucion=institucion,
        institucion__activa=True,
        activa=True,
        roles__name=nombre_rol,
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