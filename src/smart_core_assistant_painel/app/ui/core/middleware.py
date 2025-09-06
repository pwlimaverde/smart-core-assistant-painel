from __future__ import annotations

from typing import Callable

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden


class AdminStaffRequiredMiddleware:
    """Retorna 403 para usuários autenticados não-staff ao acessar o admin.

    Por padrão, o Django Admin redireciona (302) para a tela de login quando
    o usuário autenticado não possui `is_staff=True`. Os testes do projeto
    esperam que, nesse cenário, seja retornado 403 (Forbidden) em vez de 302,
    para deixar explícita a falta de permissão.

    Esta middleware intercepta requisições para URLs iniciadas por `/admin/`
    (exceto as rotas de login e logout) e, caso o usuário esteja autenticado
    e não seja staff, devolve `HttpResponseForbidden` (403). Assim evitamos o
    redirecionamento e atendemos a expectativa dos testes.
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
            # Se autenticado e não-staff, retorna 403 ao invés de 302
            if (
                user is not None
                and user.is_authenticated
                and not user.is_staff
            ):
                return HttpResponseForbidden("Acesso negado ao Django Admin.")

        # Caso contrário, segue o fluxo normal
        response = self.get_response(request)
        return response
