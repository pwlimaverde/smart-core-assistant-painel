"""
Script para iniciar um túnel HTTPS com ngrok e atualizar o .env
com a variável CLICKUP_OAUTH_REDIRECT_URI apontando para o callback
do ClickUp em Django.

Fluxo:
- Verifica se o binário do ngrok está disponível.
- Inicia o túnel em background na porta configurada (default 8000).
- Consulta o endpoint local `http://127.0.0.1:4040/api/tunnels` para
  obter a URL pública HTTPS.
- Atualiza o arquivo `.env` com o novo `CLICKUP_OAUTH_REDIRECT_URI`.

Observação: este script não configura o Redirect URI dentro do painel
do ClickUp. Após obter a URL, você deve copiá-la e adicionar ao
aplicativo no ClickUp.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
import re

from decouple import config
from urllib.request import urlopen


def _resolve_ngrok_binary() -> Optional[str]:
    """Resolve o caminho para o binário do ngrok.

    Tenta `NGROK_PATH` (absoluto) e, em seguida, busca no PATH.
    """
    explicit: str = config("NGROK_PATH", default="")
    if explicit:
        p = Path(explicit)
        if p.exists():
            return str(p)
    found: Optional[str] = shutil.which("ngrok")
    if found:
        return found

    # Fallbacks comuns no Windows
    try:
        home = Path.home()
        local_app: Path = home / "AppData" / "Local" / "ngrok" / "ngrok.exe"
        if local_app.exists():
            return str(local_app)
    except Exception:
        pass

    program_files: Path = Path("C:/Program Files/ngrok/ngrok.exe")
    if program_files.exists():
        return str(program_files)

    return None


def check_ngrok_installed() -> bool:
    """Verifica se o binário do ngrok está disponível."""
    return _resolve_ngrok_binary() is not None


def start_ngrok(port: int, authtoken: Optional[str]) -> subprocess.Popen:
    """Inicia o ngrok em background na porta informada.

    Para ngrok v3, habilita logs em stdout para permitir extração da URL
    pública quando a API local (4040) não estiver disponível.
    """
    cmd: list[str]
    binary: str = _resolve_ngrok_binary() or "ngrok"
    cmd = [binary, "http", str(port), "--log=stdout", "--log-format=logfmt"]
    if authtoken:
        cmd += ["--authtoken", authtoken]

    # Mantém processo em background e permite leitura de stdout
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def get_public_https_url(timeout_sec: int = 30) -> Optional[str]:
    """Consulta o endpoint local do ngrok e retorna a URL pública HTTPS.

    Faz polling até `timeout_sec` segundos para aguardar a criação do
    túnel. Retorna `None` se não encontrar.
    """
    deadline: float = time.time() + timeout_sec
    endpoint: str = "http://127.0.0.1:4040/api/tunnels"
    while time.time() < deadline:
        try:
            with urlopen(endpoint) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(1)
            continue

        tunnels = data.get("tunnels", [])
        for t in tunnels:
            url = t.get("public_url", "")
            if url.startswith("https://"):
                return url
        time.sleep(1)
    return None


def parse_public_url_from_logs(proc: subprocess.Popen, timeout_sec: int = 30) -> Optional[str]:
    """Lê o stdout do processo ngrok e tenta extrair a URL pública HTTPS.

    Compatível com ngrok v3 em modo `--log=stdout --log-format=logfmt`.
    Procura padrões contendo `https://` e retorna a primeira ocorrência.
    """
    deadline: float = time.time() + timeout_sec
    # Apenas domínios válidos do ngrok (evita capturar links de dashboard)
    url_regex = re.compile(
        r"https://[a-zA-Z0-9.-]+\.ngrok(?:-free)?\.(?:app|dev|io)(?:/[^\s]*)?"
    )
    if not proc.stdout:
        return None
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.5)
            continue
        # Se houver erro de autenticação, retorne None cedo para mensagens claras
        if "authentication failed" in line or "ERR_NGROK_107" in line:
            return None
        match = url_regex.search(line)
        if match:
            candidate: str = match.group(0)
            return candidate
    return None


def build_clickup_redirect(base_url: str) -> str:
    """Monta a URL completa de callback do ClickUp para Django."""
    # Garante barra final e caminho do callback
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    return f"{base_url}integrations/clickup/callback/"


def update_env_value(env_path: Path, key: str, value: str) -> None:
    """Atualiza (ou adiciona) uma chave=valor no arquivo .env.

    Implementação simples que preserva linhas que não são da chave.
    """
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


def main() -> None:
    """Ponto de entrada do script."""
    if not check_ngrok_installed():
        print(
            (
                "[ERRO] ngrok não encontrado. "
                "Defina NGROK_PATH no .env apontando para o binário (ex.: "
                "C\\Program Files\\ngrok\\ngrok.exe ou %USERPROFILE%\\AppData\\Local\\ngrok\\ngrok.exe), "
                "ou adicione o ngrok ao PATH do Windows. Alternativamente, "
                "instale com 'winget install Ngrok.Ngrok' ou 'choco install ngrok' "
                "e configure o authtoken."
            )
        )
        sys.exit(1)

    # Lê variáveis de ambiente
    authtoken: str = config("NGROK_AUTHTOKEN", default="")
    port_str: str = config("SERVER_PORT", default="8000")
    try:
        port: int = int(port_str)
    except ValueError:
        port = 8000

    # Inicia ngrok
    proc = start_ngrok(port=port, authtoken=authtoken or None)
    time.sleep(1)

    # Obtém URL pública
    # 1) Tenta via API local (v2); 2) Tenta via parsing de logs (v3)
    public_url: Optional[str] = get_public_https_url(timeout_sec=5)
    if not public_url:
        public_url = parse_public_url_from_logs(proc, timeout_sec=30)
    if not public_url:
        print(
            (
                "[ERRO] Não foi possível obter a URL pública do ngrok. "
                "Verifique se o authtoken está configurado e válido e "
                "tente novamente. Em versões mais novas (v3), confirme "
                "se o domínio público foi exibido no terminal."
            )
        )
        proc.terminate()
        sys.exit(2)

    redirect_uri: str = build_clickup_redirect(public_url)

    # Atualiza .env na raiz do projeto
    project_root: Path = Path(__file__).resolve().parents[2]
    env_path: Path = project_root / ".env"
    update_env_value(env_path, "CLICKUP_OAUTH_REDIRECT_URI", redirect_uri)

    print("[OK] Túnel ngrok iniciado.")
    print(f"Porta local: {port}")
    print(f"URL pública: {public_url}")
    print(
        (
            "CLICKUP_OAUTH_REDIRECT_URI atualizado em .env para:\n" 
            f"{redirect_uri}"
        )
    )
    print(
        (
            "Adicione esta URL como Redirect URI no app do ClickUp e "
            "mantenha o processo do ngrok rodando enquanto autentica."
        )
    )

    # Mantém o processo vivo até ser interrompido
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()