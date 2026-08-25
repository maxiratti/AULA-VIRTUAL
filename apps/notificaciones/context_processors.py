def notificaciones(request):
    if not request.user.is_authenticated:
        return {
            "notificaciones_no_leidas": 0,
            "notificaciones_recientes": [],
        }

    from .services import sincronizar_notificaciones_clases

    sincronizar_notificaciones_clases(
        request.user
    )

    no_leidas = (
        request.user.notificaciones
        .filter(leida=False)
    )

    return {
        "notificaciones_no_leidas": (
            no_leidas.count()
        ),
        "notificaciones_recientes": (
            list(no_leidas[:5])
        ),
    }