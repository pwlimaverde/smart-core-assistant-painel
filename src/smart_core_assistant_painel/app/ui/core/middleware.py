from __future__ import annotations

from typing import Callable

from django.core.exceptions import PermissionDenied


class AdminStaffRequiredMiddleware:
    """[ADM-USR-003] Retorna 403 para usuários não-staff ao acessar o admin.

    Intercepta requisições para URLs iniciadas por `/admin/` (exceto login/logout).
    Se o usuário não estiver autenticado ou não for staff, levanta PermissionDenied
    para exibir a página de erro 403 personalizada.
    """

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path

        # Somente trata URLs do admin que não sejam login/logout
        if path.startswith("/admin/") and not (
            path.startswith("/admin/login/")
            or path.startswith("/admin/logout/")
        ):
            user = getattr(request, "user", None)
            # Se não autenticado ou não-staff, levanta PermissionDenied (403)
            if user is None or not user.is_authenticated or not user.is_staff:
                raise PermissionDenied()

        # Caso contrário, segue o fluxo normal
        response = self.get_response(request)
        return response
