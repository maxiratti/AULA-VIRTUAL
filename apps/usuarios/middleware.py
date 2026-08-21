from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse


class CambioPasswordObligatorioMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        usuario = request.user

        if (
            usuario.is_authenticated
            and getattr(
                usuario,
                "debe_cambiar_password",
                False,
            )
        ):
            try:
                url_cambio = reverse(
                    "cambiar_password_obligatorio"
                )

                url_logout = reverse(
                    "logout"
                )

            except NoReverseMatch:
                return self.get_response(request)

            rutas_permitidas = [
                url_cambio,
                url_logout,
            ]

            if request.path not in rutas_permitidas:
                return redirect(
                    "cambiar_password_obligatorio"
                )

        return self.get_response(request)