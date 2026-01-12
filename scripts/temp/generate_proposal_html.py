import markdown
import base64
import os
from pathlib import Path

# Configurações de caminhos
BASE_DIR = Path("c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel")
DOCS_DIR = BASE_DIR / "docs_dev/planejamento/funcionalidades"
ASSETS_DIR = BASE_DIR / "docs_dev/planejamento/institucional"
OUTPUT_FILE = DOCS_DIR / "proposta_ecoprint.html"
INPUT_MD = DOCS_DIR / "custo_implementacao.md"
LOGO_FILE = ASSETS_DIR / "logo_smart.png"


def get_image_base64(image_path):
    if not image_path.exists():
        print(f"Alerta: Logo não encontrada em {image_path}")
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def generate_html():
    # 1. Ler o Markdown
    if not INPUT_MD.exists():
        print(f"Erro: Arquivo MD não encontrado em {INPUT_MD}")
        return

    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_lines = f.readlines()

    # Remover a primeira linha se for um título (para substituir pelo customizado)
    if md_lines and md_lines[0].startswith("# "):
        md_content = "".join(md_lines[1:])
    else:
        md_content = "".join(md_lines)

    # 2. Converter para HTML
    html_content = markdown.markdown(md_content, extensions=["tables"])

    # 3. Preparar a Logo
    logo_b64 = get_image_base64(LOGO_FILE)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="Smart Core Logo" class="logo">'
        if logo_b64
        else ""
    )

    # 4. Template HTML Profissional
    full_html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proposta de Custos - Ecoprint</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        body {{
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: #333;
            max_width: 800px;
            margin: 0 auto;
            padding: 40px;
            background-color: #fff;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #eaeaea;
            padding-bottom: 20px;
            margin-bottom: 30px;
            height: 80px; /* Altura fixa para garantir alinhamento vertical */
        }}

        .logo-container {{
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            height: 100%;
        }}

        /* Logo ajustada pela altura para não ultrapassar o texto */
        .logo {{
            max-height: 65px; 
            width: auto;
            max-width: 200px;
        }}

        .header-text {{
            text-align: right;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .main-title {{
            font-size: 24px;
            margin: 0;
            color: #2c3e50;
            font-weight: 700;
            line-height: 1.2;
        }}

        .client-name {{
            font-size: 14px;
            color: #7f8c8d;
            margin: 5px 0 0 0;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* H2 no corpo do texto markdown */
        h2 {{
            font-size: 20px;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
            margin-top: 25px;
        }}

        h3 {{
            font-size: 16px;
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }}

        ul {{
            list-style-type: none;
            padding: 0;
        }}

        li {{
            margin-bottom: 8px;
            padding-left: 20px;
            position: relative;
            font-size: 15px;
        }}

        li:before {{
            content: "•";
            color: #3498db;
            font-weight: bold;
            display: inline-block;
            width: 1em;
            margin-left: -1em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #f8f9fa;
            font-size: 15px;
        }}

        th, td {{
            padding: 10px 12px;
            border: 1px solid #ddd;
            text-align: left;
        }}

        th {{
            background-color: #2c3e50;
            color: white;
            font-weight: 600;
        }}

        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 0.8em;
            color: #95a5a6;
            border-top: 1px solid #eee;
            padding-top: 15px;
        }}

        @media print {{
            body {{
                padding: 20px;
            }}
            .no-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            {logo_html}
        </div>
        <div class="header-text">
            <h1 class="main-title">Proposta Custo Implementação</h1>
            <p class="client-name">Cliente: Ecoprint</p>
        </div>
    </div>

    <div class="content">
        {html_content}
    </div>

    <div class="footer">
        <p>Smart Core Assistant Painel - Soluções em Inteligência Artificial</p>
        <p>Gerado em {os.popen("date /t").read().strip()}</p>
    </div>
</body>
</html>
    """

    # 5. Salvar Arquivo
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Sucesso! Arquivo gerado em: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_html()
