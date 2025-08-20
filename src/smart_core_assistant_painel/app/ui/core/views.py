"""Views para o aplicativo core.

Este módulo contém views básicas do sistema, incluindo health check
e páginas de status.
"""

from django.http import HttpRequest, HttpResponse


def health_check(request: HttpRequest) -> HttpResponse:
    """View simples para health check do Docker.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        HttpResponse: Resposta HTTP com status 200.
    """
    return HttpResponse("OK", status=200)


def home(request: HttpRequest) -> HttpResponse:
    """View para página inicial.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        HttpResponse: Resposta HTTP simples.
    """
    return HttpResponse(
        "<h1>Smart Core Assistant Painel</h1>"
        "<p>Sistema funcionando corretamente!</p>"
        "<p><a href='/admin/'>Acessar Admin</a></p>",
        content_type="text/html"
    )