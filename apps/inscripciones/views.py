from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from openpyxl import Workbook, load_workbook

from apps.cursos.models import Curso
from apps.roles.utils import tiene_rol_en_institucion
from apps.usuarios.models import (
    MembresiaInstitucional,
    Usuario,
)

from .forms import (
    CargaMasivaAlumnosForm,
    InscripcionForm,
    NuevoAlumnoCursoForm,
)
from .models import Inscripcion


def puede_gestionar_curso(usuario, curso):
    if usuario.is_superuser:
        return True

    return (
        tiene_rol_en_institucion(
            usuario,
            "Administrador institucional",
            curso.institucion,
        )
        or tiene_rol_en_institucion(
            usuario,
            "Coordinador",
            curso.institucion,
        )
    )


@login_required
def lista_inscripciones(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=curso_id,
    )

    if not puede_gestionar_curso(
        request.user,
        curso,
    ):
        raise PermissionDenied

    inscripciones = (
        Inscripcion.objects
        .filter(curso=curso)
        .select_related("alumno")
        .order_by(
            "alumno__last_name",
            "alumno__first_name",
            "alumno__username",
        )
    )

    return render(
        request,
        "inscripciones/lista.html",
        {
            "curso": curso,
            "inscripciones": inscripciones,
            "total_inscriptos": inscripciones.count(),
        },
    )


@login_required
def nueva_inscripcion(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=curso_id,
    )

    if curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. Las inscripciones están en modo solo lectura.",
        )
        return redirect(
            "lista_inscripciones",
            curso_id=curso.pk,
        )

    if not puede_gestionar_curso(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = InscripcionForm(
            request.POST,
            curso=curso,
        )

        if form.is_valid():
            inscripcion = form.save(
                commit=False
            )

            inscripcion.curso = curso
            inscripcion.save()

            messages.success(
                request,
                "Alumno inscripto correctamente.",
            )

            return redirect(
                "lista_inscripciones",
                curso_id=curso.pk,
            )

    else:
        form = InscripcionForm(
            curso=curso,
        )

    return render(
        request,
        "inscripciones/form.html",
        {
            "curso": curso,
            "form": form,
            "titulo": "Inscribir alumno",
        },
    )


@login_required
def nuevo_alumno_curso(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=curso_id,
    )

    if curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. Las inscripciones están en modo solo lectura.",
        )
        return redirect(
            "lista_inscripciones",
            curso_id=curso.pk,
        )

    if not puede_gestionar_curso(request.user, curso):
        raise PermissionDenied

    if request.method == "POST":
        form = NuevoAlumnoCursoForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                usuario = Usuario(
                    username=form.cleaned_data["username"],
                    first_name=form.cleaned_data["nombre"],
                    last_name=form.cleaned_data["apellido"],
                    email=form.cleaned_data["email"],
                    is_active=True,
                    debe_cambiar_password=True,
                )
                usuario.set_password(
                    form.cleaned_data["password"]
                )
                usuario.save()

                rol_alumno = Group.objects.get(name="Alumno")

                membresia = MembresiaInstitucional.objects.create(
                    usuario=usuario,
                    institucion=curso.institucion,
                    activa=True,
                )
                membresia.roles.add(rol_alumno)

                Inscripcion.objects.create(
                    curso=curso,
                    alumno=usuario,
                    estado=Inscripcion.ESTADO_INSCRIPTO,
                )

            messages.success(
                request,
                (
                    "Alumno creado e inscripto correctamente. "
                    "En su primer ingreso deberá cambiar la contraseña."
                ),
            )

            return redirect(
                "lista_inscripciones",
                curso_id=curso.pk,
            )
    else:
        form = NuevoAlumnoCursoForm()

    return render(
        request,
        "inscripciones/nuevo_alumno.html",
        {
            "curso": curso,
            "form": form,
        },
    )


@login_required
def editar_inscripcion(request, pk):
    inscripcion = get_object_or_404(
        Inscripcion.objects.select_related(
            "curso",
            "curso__institucion",
            "alumno",
        ),
        pk=pk,
    )

    curso = inscripcion.curso

    if not puede_gestionar_curso(
        request.user,
        curso,
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = InscripcionForm(
            request.POST,
            instance=inscripcion,
            curso=curso,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Inscripción actualizada correctamente.",
            )

            return redirect(
                "lista_inscripciones",
                curso_id=curso.pk,
            )

    else:
        form = InscripcionForm(
            instance=inscripcion,
            curso=curso,
        )

    return render(
        request,
        "inscripciones/form.html",
        {
            "curso": curso,
            "form": form,
            "titulo": "Editar inscripción",
        },
    )


@login_required
def descargar_plantilla_alumnos(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=curso_id,
    )

    if not puede_gestionar_curso(
        request.user,
        curso,
    ):
        raise PermissionDenied

    workbook = Workbook()
    hoja = workbook.active
    hoja.title = "Alumnos"

    hoja.append(
        [
            "nombre",
            "apellido",
            "usuario",
            "email",
            "contraseña",
        ]
    )

    hoja.append(
        [
            "Juan",
            "Pérez",
            "jperez",
            "juan@ejemplo.com",
            "Temporal123",
        ]
    )

    salida = BytesIO()

    workbook.save(salida)
    salida.seek(0)

    response = HttpResponse(
        salida.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    response["Content-Disposition"] = (
        'attachment; filename="plantilla_alumnos.xlsx"'
    )

    return response


@login_required
def carga_masiva_alumnos(request, curso_id):
    curso = get_object_or_404(
        Curso.objects.select_related("institucion"),
        pk=curso_id,
    )

    if curso.estado == Curso.ESTADO_FINALIZADO:
        messages.warning(
            request,
            "El curso está finalizado. Las inscripciones están en modo solo lectura.",
        )
        return redirect(
            "lista_inscripciones",
            curso_id=curso.pk,
        )

    if not puede_gestionar_curso(
        request.user,
        curso,
    ):
        raise PermissionDenied

    resultado = None

    if request.method == "POST":
        form = CargaMasivaAlumnosForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            archivo = form.cleaned_data["archivo"]
            workbook = None

            try:
                workbook = load_workbook(
                    archivo,
                    read_only=True,
                    data_only=True,
                )

                hoja = workbook.active

                filas = list(
                    hoja.iter_rows(
                        values_only=True
                    )
                )

                if not filas:
                    raise ValueError(
                        "El archivo está vacío."
                    )

                encabezados = [
                    str(valor).strip().lower()
                    if valor is not None
                    else ""
                    for valor in filas[0]
                ]

                encabezados_requeridos = [
                    "nombre",
                    "apellido",
                    "usuario",
                    "email",
                    "contraseña",
                ]

                if encabezados != encabezados_requeridos:
                    raise ValueError(
                        "La plantilla no tiene "
                        "las columnas esperadas."
                    )

                errores = []
                registros = []
                usernames_vistos = set()

                for numero_fila, fila in enumerate(
                    filas[1:],
                    start=2,
                ):
                    (
                        nombre,
                        apellido,
                        username,
                        email,
                        password,
                    ) = fila

                    nombre = (
                        str(nombre).strip()
                        if nombre
                        else ""
                    )

                    apellido = (
                        str(apellido).strip()
                        if apellido
                        else ""
                    )

                    username = (
                        str(username).strip()
                        if username
                        else ""
                    )

                    email = (
                        str(email).strip()
                        if email
                        else ""
                    )

                    password = (
                        str(password).strip()
                        if password
                        else ""
                    )

                    if not username:
                        errores.append(
                            f"Fila {numero_fila}: "
                            "falta el usuario."
                        )
                        continue

                    if username in usernames_vistos:
                        errores.append(
                            f"Fila {numero_fila}: "
                            f"el usuario '{username}' "
                            "está repetido en el archivo."
                        )
                        continue

                    usernames_vistos.add(
                        username
                    )

                    registros.append(
                        {
                            "numero_fila": numero_fila,
                            "nombre": nombre,
                            "apellido": apellido,
                            "username": username,
                            "email": email,
                            "password": password,
                        }
                    )

                usernames = [
                    registro["username"]
                    for registro in registros
                ]

                usuarios_existentes = {
                    usuario.username: usuario
                    for usuario in (
                        Usuario.objects
                        .filter(
                            username__in=usernames
                        )
                    )
                }

                existentes = len(
                    usuarios_existentes
                )

                registros_validos = []
                usuarios_nuevos = []

                for registro in registros:
                    username = registro[
                        "username"
                    ]

                    if (
                        username
                        not in usuarios_existentes
                        and not registro["password"]
                    ):
                        errores.append(
                            f"Fila "
                            f"{registro['numero_fila']}: "
                            "falta la contraseña."
                        )
                        continue

                    registros_validos.append(
                        registro
                    )

                    if username in usuarios_existentes:
                        continue

                    usuario = Usuario(
                        username=username,
                        first_name=registro["nombre"],
                        last_name=registro["apellido"],
                        email=registro["email"],
                        is_active=True,
                        debe_cambiar_password=True,
                    )

                    usuario.set_password(
                        registro["password"]
                    )

                    usuarios_nuevos.append(
                        usuario
                    )

                with transaction.atomic():
                    if usuarios_nuevos:
                        Usuario.objects.bulk_create(
                            usuarios_nuevos,
                            batch_size=250,
                        )

                    usernames_validos = [
                        registro["username"]
                        for registro
                        in registros_validos
                    ]

                    usuarios_por_username = {
                        usuario.username: usuario
                        for usuario in (
                            Usuario.objects
                            .filter(
                                username__in=(
                                    usernames_validos
                                )
                            )
                        )
                    }

                    usuarios = [
                        usuarios_por_username[
                            registro["username"]
                        ]
                        for registro
                        in registros_validos
                        if registro["username"]
                        in usuarios_por_username
                    ]

                    usuarios_ids = [
                        usuario.pk
                        for usuario in usuarios
                    ]

                    membresias_existentes = {
                        membresia.usuario_id: membresia
                        for membresia in (
                            MembresiaInstitucional.objects
                            .filter(
                                usuario_id__in=usuarios_ids,
                                institucion=curso.institucion,
                            )
                        )
                    }

                    membresias_nuevas = [
                        MembresiaInstitucional(
                            usuario=usuario,
                            institucion=curso.institucion,
                            activa=True,
                        )
                        for usuario in usuarios
                        if (
                            usuario.pk
                            not in membresias_existentes
                        )
                    ]

                    if membresias_nuevas:
                        MembresiaInstitucional.objects.bulk_create(
                            membresias_nuevas,
                            batch_size=250,
                            ignore_conflicts=True,
                        )

                    membresias_inactivas = [
                        membresia
                        for membresia
                        in membresias_existentes.values()
                        if not membresia.activa
                    ]

                    for membresia in membresias_inactivas:
                        membresia.activa = True

                    if membresias_inactivas:
                        MembresiaInstitucional.objects.bulk_update(
                            membresias_inactivas,
                            ["activa"],
                            batch_size=250,
                        )

                    membresias = list(
                        MembresiaInstitucional.objects
                        .filter(
                            usuario_id__in=usuarios_ids,
                            institucion=curso.institucion,
                        )
                    )

                    rol_alumno = Group.objects.get(
                        name="Alumno"
                    )

                    through = (
                        MembresiaInstitucional
                        .roles
                        .through
                    )

                    campo_membresia = next(
                        campo.name
                        for campo
                        in through._meta.fields
                        if (
                            getattr(
                                campo.remote_field,
                                "model",
                                None,
                            )
                            is MembresiaInstitucional
                        )
                    )

                    campo_grupo = next(
                        campo.name
                        for campo
                        in through._meta.fields
                        if (
                            getattr(
                                campo.remote_field,
                                "model",
                                None,
                            )
                            is Group
                        )
                    )

                    membresias_ids = [
                        membresia.pk
                        for membresia in membresias
                    ]

                    filtro_roles = {
                        (
                            f"{campo_membresia}_id"
                            "__in"
                        ): membresias_ids,
                        f"{campo_grupo}_id": (
                            rol_alumno.pk
                        ),
                    }

                    membresias_con_rol = set(
                        through.objects
                        .filter(
                            **filtro_roles
                        )
                        .values_list(
                            f"{campo_membresia}_id",
                            flat=True,
                        )
                    )

                    relaciones_roles = []

                    for membresia in membresias:
                        if (
                            membresia.pk
                            in membresias_con_rol
                        ):
                            continue

                        datos_relacion = {
                            (
                                f"{campo_membresia}_id"
                            ): membresia.pk,
                            (
                                f"{campo_grupo}_id"
                            ): rol_alumno.pk,
                        }

                        relaciones_roles.append(
                            through(
                                **datos_relacion
                            )
                        )

                    if relaciones_roles:
                        through.objects.bulk_create(
                            relaciones_roles,
                            batch_size=250,
                            ignore_conflicts=True,
                        )

                    inscripciones_existentes = set(
                        Inscripcion.objects
                        .filter(
                            curso=curso,
                            alumno_id__in=usuarios_ids,
                        )
                        .values_list(
                            "alumno_id",
                            flat=True,
                        )
                    )

                    inscripciones_nuevas = [
                        Inscripcion(
                            curso=curso,
                            alumno=usuario,
                        )
                        for usuario in usuarios
                        if (
                            usuario.pk
                            not in inscripciones_existentes
                        )
                    ]

                    if inscripciones_nuevas:
                        Inscripcion.objects.bulk_create(
                            inscripciones_nuevas,
                            batch_size=250,
                            ignore_conflicts=True,
                        )

                resultado = {
                    "creados": len(
                        usuarios_nuevos
                    ),
                    "existentes": existentes,
                    "inscriptos": len(
                        inscripciones_nuevas
                    ),
                    "errores": errores,
                }

                messages.success(
                    request,
                    (
                        "Carga masiva completada: "
                        f"{resultado['creados']} usuarios creados, "
                        f"{resultado['existentes']} usuarios existentes y "
                        f"{resultado['inscriptos']} nuevas inscripciones."
                    ),
                )

                if errores:
                    messages.warning(
                        request,
                        (
                            f"{len(errores)} fila(s) no pudieron procesarse. "
                            "Revisá la planilla antes de volver a cargarlas."
                        ),
                    )

                return redirect(
                    "lista_inscripciones",
                    curso_id=curso.pk,
                )

            except Exception as error:
                messages.error(
                    request,
                    (
                        "No se pudo procesar "
                        f"el archivo: {error}"
                    ),
                )

            finally:
                if workbook is not None:
                    workbook.close()

    else:
        form = CargaMasivaAlumnosForm()

    return render(
        request,
        "inscripciones/carga_masiva.html",
        {
            "curso": curso,
            "form": form,
            "resultado": resultado,
        },
    )
