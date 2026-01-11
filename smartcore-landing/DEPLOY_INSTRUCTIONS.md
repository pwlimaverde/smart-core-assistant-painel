# Instruções de Publicação - Landing Page (Cloudflare Pages)

Este diretório contém os arquivos estáticos necessários para publicar sua Landing Page no Cloudflare Pages.

## Passo 1: Publicar no Cloudflare Pages
1. Aceda ao painel do Cloudflare: **Workers & Pages** > **Create Application** > **Pages**.
2. Escolha **"Upload assets"**.
3. Defina o nome do projeto (ex: `smartcore-landing`).
4. Arraste **todo o conteúdo desta pasta (`cloud_pages_deploy`)** para a área de upload.
   - Certifique-se de incluir `index.html`, `coming_soon.html` e a pasta `static`.
5. Clique em **Deploy Site**.

## Passo 2: Configurar Domínios
No painel do seu projeto Cloudflare Pages:
1. Vá em **Custom domains** > **Set up a custom domain**.
2. Adicione `smartcoreassistant.com.br` (Domínio Principal).
   - O Cloudflare pedirá para atualizar o DNS (substituindo o Tunnel). **Confirme**.
3. Adicione `www.smartcoreassistant.com.br`.

## Passo 3: Ajustar o Tunnel (Sistema)
No painel **Zero Trust** > **Networks** > **Tunnels**:
1. Edite o tunnel do seu servidor Docker.
2. Na aba **Public Hostnames**, localize a entrada antiga (raiz ou www).
3. Altere para o subdomínio `app`:
   - Subdomain: `app`
   - Domain: `smartcoreassistant.com.br`
   - Service: `http://smart_core_django_app:8000` (ou como estava configurado).

## Resumo da Nova Arquitetura
- **Site Institucional**: `smartcoreassistant.com.br` (Cloudflare Pages - Estático)
- **Sistema/Login**: `app.smartcoreassistant.com.br` (Django - Tunnel)
- **Clientes**: `cliente.smartcoreassistant.com.br` (Django - Tunnel)
