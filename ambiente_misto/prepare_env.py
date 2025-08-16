import os
import shutil
import sys

def get_env_value(key):
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if not os.path.exists(env_path):
        return None
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.strip().split('=', 1)
                if len(parts) == 2 and parts[0].strip() == key:
                    return parts[1].strip()
    return None

def prepare_env():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_path = os.path.join(project_root, '.env')
    firebase_key_path = os.path.join(project_root, 'firebase_key.json')

    # 1. Check for .env and firebase_key.json
    if not os.path.exists(env_path) or not os.path.exists(firebase_key_path):
        print("ERRO: Antes de executar a criação do ambiente local, salve os arquivos .env e firebase_key.json na raiz do projeto.", file=sys.stderr)
        sys.exit(1)

    print("Arquivos .env and firebase_key.json encontrados.")

    # 2. Move firebase_key.json
    gac_path_str = get_env_value("GOOGLE_APPLICATION_CREDENTIALS")
    if not gac_path_str:
        print("ERRO: A variável GOOGLE_APPLICATION_CREDENTIALS não está definida no arquivo .env.", file=sys.stderr)
        sys.exit(1)
        
    gac_path = os.path.join(project_root, gac_path_str)
    gac_dir = os.path.dirname(gac_path)

    os.makedirs(gac_dir, exist_ok=True)
    
    # Move the file if it's not already there
    if os.path.abspath(firebase_key_path) != os.path.abspath(gac_path):
        if os.path.exists(gac_path):
            print(f"Aviso: O arquivo de destino '{gac_path}' já existe. Ele não será sobrescrito.")
        else:
            shutil.move(firebase_key_path, gac_path)
            print(f"Arquivo '{firebase_key_path}' movido para '{gac_path}'")
    else:
        print(f"Arquivo '{firebase_key_path}' já está no local correto.")

    print("Preparação do ambiente concluída com sucesso.")

if __name__ == "__main__":
    prepare_env()
