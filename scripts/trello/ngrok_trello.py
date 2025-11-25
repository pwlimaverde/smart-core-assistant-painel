import os
import subprocess
import sys
import time
from pathlib import Path

# Configuration
NGROK_AUTHTOKEN = "35MOKU9i2ViPpWj5w4YKXh6L7xl_7hEQit9gnB6HUZZX1AFZK"
DOMAIN = "margareta-impedimentary-congenially.ngrok-free.dev"
PORT = 8000
ENV_FILE = Path(".env")


def main():
    # 1. Set Authtoken
    print("Configuring ngrok authtoken...")
    try:
        subprocess.run(
            ["ngrok", "config", "add-authtoken", NGROK_AUTHTOKEN],
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error configuring authtoken: {e}")
        return
    except FileNotFoundError:
        print(
            "Error: ngrok command not found. Make sure ngrok is installed and in your PATH."
        )
        return

    # 2. Start ngrok
    print(f"Starting ngrok tunnel on port {PORT} with domain {DOMAIN}...")
    try:
        # Start ngrok process
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", f"--domain={DOMAIN}", str(PORT)],
            stdout=sys.stdout,  # Redirect stdout to console so user sees logs
            stderr=sys.stderr,
            shell=True,
        )

        # Give it a moment to start
        time.sleep(2)

        if ngrok_process.poll() is not None:
            print("Error: ngrok failed to start immediately.")
            return

        public_url = f"https://{DOMAIN}"
        # URL do Webhook (não OAuth)
        callback_url = f"{public_url}/api/trello_sync/webhook/"

        print(f"\n[OK] Túnel ngrok iniciado.")
        print(f"Porta local: {PORT}")
        print(f"URL pública: {public_url}")

        # 3. Update .env
        update_env_file(public_url, callback_url)

        print(f"TRELLO_WEBHOOK_CALLBACK_URL atualizado em .env para:")
        print(f"{callback_url}")
        print(
            "CORS_ALLOWED_ORIGINS atualizado para incluir o domínio do ngrok."
        )
        print("Mantenha o processo do ngrok rodando para receber os webhooks.")
        print("Pressione Ctrl+C para parar.")

        # Keep running
        ngrok_process.wait()

    except KeyboardInterrupt:
        print("\nStopping ngrok...")
        ngrok_process.terminate()
        try:
            ngrok_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ngrok_process.kill()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def update_env_file(public_url, callback_url):
    if not ENV_FILE.exists():
        print(f"Warning: {ENV_FILE} not found. Skipping update.")
        return

    try:
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        new_lines = []

        # Flags to track updates
        trello_updated = False
        cors_updated = False

        for line in lines:
            # Update Webhook URL
            if line.startswith("TRELLO_WEBHOOK_CALLBACK_URL="):
                new_lines.append(f"TRELLO_WEBHOOK_CALLBACK_URL={callback_url}")
                trello_updated = True
            # Remove OAuth URL (cleanup)
            elif line.startswith("TRELLO_OAUTH_REDIRECT_URI="):
                continue
            # Update CORS
            elif line.startswith("CORS_ALLOWED_ORIGINS="):
                current_origins = line.split("=", 1)[1].strip()
                if public_url not in current_origins:
                    if current_origins:
                        new_origins = f"{current_origins},{public_url}"
                    else:
                        new_origins = public_url
                    new_lines.append(f"CORS_ALLOWED_ORIGINS={new_origins}")
                else:
                    new_lines.append(line)
                cors_updated = True
            else:
                new_lines.append(line)

        # Add if missing
        if not trello_updated:
            new_lines.append(f"TRELLO_WEBHOOK_CALLBACK_URL={callback_url}")

        if not cors_updated:
            new_lines.append(f"CORS_ALLOWED_ORIGINS={public_url}")

        ENV_FILE.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"Updated {ENV_FILE} successfully.")
    except Exception as e:
        print(f"Failed to update {ENV_FILE}: {e}")


if __name__ == "__main__":
    main()
