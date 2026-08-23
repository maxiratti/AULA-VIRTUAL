def notificaciones(request):
    if not request.user.is_authenticated:
        return {
            "notificaciones_no_leidas": 0,
            "notificaciones_recientes": [],
        }

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