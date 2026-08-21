from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.cursos.models import Curso
from apps.roles.utils import es_alumno, es_docente




@login_required
def dashboard(request):
    usuario = request.user

    if usuario.debe_cambiar_password:
        return redirect(
            "cambiar_password_obligatorio"
        )

    cursos = Curso.objects.none()

    if es_docente(usuario):
        cursos = (
            Curso.objects
            .filter(docentes=usuario)
            .select_related("institucion")
            .distinct()
        )

    elif es_alumno(usuario):
        cursos = (
            Curso.objects
            .filter(
                inscripciones__alumno=usuario,
            )
            .select_related("institucion")
            .distinct()
        )

    context = {
        "cursos": cursos,
        "cantidad_cursos": cursos.count(),
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )