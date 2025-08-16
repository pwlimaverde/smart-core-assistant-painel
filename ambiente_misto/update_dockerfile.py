import os
import re

def update_dockerfile():
    dockerfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Dockerfile'))
    
    if not os.path.exists(dockerfile_path):
        print(f"Dockerfile nao encontrado em: {dockerfile_path}")
        return

    with open(dockerfile_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        # Comenta as linhas que comecam com ENTRYPOINT ou CMD
        if re.match(r'^\s*ENTRYPOINT', line) or re.match(r'^\s*CMD', line):
            new_lines.append(f'# {line}')
        else:
            new_lines.append(line)

    with open(dockerfile_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        f.write('\n# As linhas ENTRYPOINT e CMD foram comentadas pelo ambiente_misto.\n')

    print(f"'Dockerfile' atualizado com sucesso em: {dockerfile_path}")

if __name__ == "__main__":
    update_dockerfile()