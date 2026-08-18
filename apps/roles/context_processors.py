from .utils import (
    es_administrador,
    es_alumno,
    es_coordinador,
    es_docente,
)


def roles_usuario(request):
    usuario = request.user

    return {
        "es_administrador": es_administrador(usuario),
        "es_coordinador": es_coordinador(usuario),
        "es_docente": es_docente(usuario),
        "es_alumno": es_alumno(usuario),
    }