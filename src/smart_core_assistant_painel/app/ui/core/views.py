"""Views para o aplicativo core.

Este módulo contém views básicas do sistema, incluindo health check
e páginas de status.
"""

import json
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from decouple import config
from django.http import HttpRequest, HttpResponse

API_TOKEN_URL: str = "https://api.clickup.com/api/v2/oauth/token"


def _update_env_value(key: str, value: str) -> None:
    """Atualiza (ou adiciona) uma chave=valor no arquivo .env da raiz.

    Comentário: persiste o token OAuth do ClickUp no `.env` do projeto
    (pasta raiz), mantendo as demais linhas intactas. Anteriormente,
    este helper escrevia em `src/.env`; ajustado para a raiz.
    """
    # Caminha de `.../src/smart_core_assistant_painel/app/ui/core/views.py`
    # até a raiz do projeto. parents[5] aponta para a pasta do projeto.
    project_root: Path = Path(__file__).resolve().parents[5]
    env_path: Path = project_root / ".env"
    lines: list[str]
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    written: bool = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            written = True
        else:
            new_lines.append(line)

    if not written:
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Troca o `code` por `access_token` na API do ClickUp.

    Comentário: usa client_id e client_secret do .env via decouple.
    """
    client_id: str = config("CLICKUP_CLIENT_ID", default="")
    client_secret: str = config("CLICKUP_CLIENT_SECRET", default="")
    payload: Dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    body: bytes = json.dumps(payload).encode("utf-8")
    req = Request(
        API_TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except HTTPError as e:
        return {"error": f"HTTPError: {e.code}", "body": e.read().decode()}
    except URLError as e:
        return {"error": f"URLError: {e.reason}"}


def health_check(request: HttpRequest) -> HttpResponse:
    """[SYS-INI-003] View simples para health check do Docker.

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
        content_type="text/html",
    )


def clickup_callback(request: HttpRequest) -> HttpResponse:
    """[ADM-CFG-001] Callback OAuth do ClickUp.

    Fluxo:
    - Lê `code` da querystring.
    - Lê `CLICKUP_OAUTH_REDIRECT_URI` do .env para validar.
    - Troca `code` por `access_token` e persiste em `.env`.
    - Exibe mensagem de sucesso e orientações.
    """
    code: str | None = request.GET.get("code")
    if not code:
        return HttpResponse("Faltou o parâmetro 'code' na URL.", status=400)

    redirect_uri: str = config("CLICKUP_OAUTH_REDIRECT_URI", default="")
    if not redirect_uri:
        return HttpResponse(
            "CLICKUP_OAUTH_REDIRECT_URI não configurado no .env.",
            status=500,
        )

    data: Dict[str, Any] = _exchange_code_for_token(code, redirect_uri)
    access_token: str = data.get("access_token", "")
    if not access_token:
        return HttpResponse(
            f"Falha na troca do code: {json.dumps(data)[:200]}", status=502
        )

    _update_env_value("CLICKUP_OAUTH_ACCESS_TOKEN", access_token)

    # Máscara parcial para evitar exposição total
    masked: str = access_token[:6] + "..." + access_token[-6:]
    html: str = (
        "<h2>ClickUp OAuth concluído</h2>"
        "<p>Token salvo no .env como CLICKUP_OAUTH_ACCESS_TOKEN.</p>"
        f"<p>Token (parcial): <code>{masked}</code></p>"
        "<p>Agora você pode fechar esta janela e continuar.</p>"
    )
    return HttpResponse(html, content_type="text/html", status=200)
