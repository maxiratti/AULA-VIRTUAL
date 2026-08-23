from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.utils.http import (
    url_has_allowed_host_and_scheme,
)

from .models import Notificacion


@login_required
def lista_notificaciones(request):
    notificaciones = (
        request.user.notificaciones
        .all()
        .order_by(
            "-fecha_creacion"
        )
    )

    return render(
        request,
        "notificaciones/lista.html",
        {
            "notificaciones": notificaciones,
        },
    )


@login_required
def abrir_notificacion(request, pk):
    notificacion = get_object_or_404(
        Notificacion,
        pk=pk,
        usuario=request.user,
    )

    if not notificacion.leida:
        notificacion.leida = True
        notificacion.fecha_lectura = (
            timezone.now()
        )

        notificacion.save(
            update_fields=[
                "leida",
                "fecha_lectura",
            ]
        )

    destino = notificacion.url

    if (
        destino
        and url_has_allowed_host_and_scheme(
            url=destino,
            allowed_hosts={
                request.get_host()
            },
            require_https=request.is_secure(),
        )
    ):
        return redirect(destino)

    return redirect(
        "lista_notificaciones"
    )


@login_required
def marcar_todas_leidas(request):
    if request.method == "POST":
        (
            request.user.notificaciones
            .filter(leida=False)
            .update(
                leida=True,
                fecha_lectura=timezone.now(),
            )
        )

    return redirect(
        "lista_notificaciones"
    )