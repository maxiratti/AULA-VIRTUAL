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

def es_preceptor(usuario):
    return tiene_rol(usuario, "Preceptor")


def es_observador_institucional(usuario):
    return tiene_rol(usuario, "Observador institucional")


def puede_supervisar_curso(usuario, curso):
    if not usuario.is_authenticated:
        return False

    if usuario.is_superuser:
        return True

    if tiene_rol_en_institucion(
        usuario, "Observador institucional", curso.institucion
    ):
        return True

    return (
        tiene_rol_en_institucion(usuario, "Preceptor", curso.institucion)
        and curso.preceptores.filter(pk=usuario.pk).exists()
    )
