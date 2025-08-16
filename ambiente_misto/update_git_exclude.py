import os
import subprocess

def update_git_exclude():
    # Garante que o diretorio .git/info exista
    git_info_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.git', 'info'))
    os.makedirs(git_info_dir, exist_ok=True)

    exclude_path = os.path.join(git_info_dir, 'exclude')
    
    # Caminhos relativos a partir da raiz do projeto
    lines_to_add = [
        '# Arquivos de configuracao para o ambiente_misto',
        '/docker-compose.yml',
        '/Dockerfile',
        '/.gitignore',
        '/.env',
        '/src/smart_core_assistant_painel/app/ui/core/settings.py',
        '/src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json'
    ]
    
    existing_content = ''
    if os.path.exists(exclude_path):
        with open(exclude_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

    # Verifica se as regras ja existem antes de adicionar
    if '# Arquivos de configuracao para o ambiente_misto' not in existing_content:
        with open(exclude_path, 'a', encoding='utf-8') as f:
            f.write('\n')
            for line in lines_to_add:
                f.write(f'{line}\n')
        print(f"'.git/info/exclude' atualizado com sucesso em: {exclude_path}")

    # Arquivos para marcar com assume-unchanged (devem estar no repo)
    files_to_assume = [
        'Dockerfile',
        'docker-compose.yml',
        '.gitignore',
        'src/smart_core_assistant_painel/app/ui/core/settings.py'
    ]

    try:
        print("Limpando flags 'assume-unchanged' existentes...")
        subprocess.run(['git', 'update-index', '--no-assume-unchanged'] + files_to_assume, check=True, capture_output=True, text=True)
        
        print("Marcando arquivos de configuracao para serem ignorados localmente...")
        subprocess.run(['git', 'update-index', '--assume-unchanged'] + files_to_assume, check=True, capture_output=True, text=True)
        
        print("Configuracao do Git para o ambiente misto concluida com sucesso.")
    except subprocess.CalledProcessError as e:
        print("Ocorreu um erro ao executar o comando git:")
        print(e.stderr)

if __name__ == "__main__":
    update_git_exclude()
