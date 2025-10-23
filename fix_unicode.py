"""Script para substituir caracteres Unicode por ASCII."""

import pathlib

# Ler arquivo
file_path = pathlib.Path('src/smart_core_assistant_painel/app/notion_sync/scripts/setup_notion_databases.py')
text = file_path.read_text(encoding='utf-8')

# Substituir caracteres Unicode
replacements = {
    '✓': 'OK',
    '✗': 'X',
    '⚠': '!',
    '→': '->',
    'ℹ': 'i',
    '═': '=',
}

for old, new in replacements.items():
    count = text.count(old)
    if count > 0:
        print(f"Substituindo '{old}' por '{new}': {count} ocorrencias")
    text = text.replace(old, new)

# Salvar
file_path.write_text(text, encoding='utf-8')
print('\nCaracteres Unicode substituidos com sucesso!')
