# Script PowerShell para iniciar o ambiente de desenvolvimento Docker
# Certifique-se de que o Ollama está rodando localmente antes de executar

Write-Host "🚀 Iniciando ambiente de desenvolvimento Docker..." -ForegroundColor Green

# Verifica se o arquivo de credenciais do Firebase existe
$firebaseKeyPath = "src\smart_core_assistant_painel\modules\initial_loading\utils\keys\firebase_config\firebase_key.json"
if (-not (Test-Path $firebaseKeyPath)) {
    Write-Host "❌ Erro: Arquivo de credenciais do Firebase não encontrado!" -ForegroundColor Red
    Write-Host "📋 Certifique-se de que o arquivo firebase_key.json está presente em:" -ForegroundColor Yellow
    Write-Host "   $firebaseKeyPath" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "💡 Para obter as credenciais:" -ForegroundColor Cyan
    Write-Host "   1. Acesse o Console do Firebase" -ForegroundColor White
    Write-Host "   2. Vá em Configurações do Projeto > Contas de Serviço" -ForegroundColor White
    Write-Host "   3. Clique em 'Gerar nova chave privada'" -ForegroundColor White
    Write-Host "   4. Salve o arquivo como firebase_key.json no caminho indicado" -ForegroundColor White
    exit 1
}

Write-Host "✅ Credenciais do Firebase encontradas!" -ForegroundColor Green

# Verifica se o Ollama está rodando
Write-Host "🤖 Verificando se o Ollama está rodando..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Ollama está rodando!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Aviso: Ollama não está acessível em localhost:11434" -ForegroundColor Yellow
    Write-Host "📋 Certifique-se de que o Ollama está rodando localmente" -ForegroundColor Yellow
    Write-Host "💡 Para instalar/iniciar o Ollama: https://ollama.ai/" -ForegroundColor Cyan
}

# Verificar se o Docker está rodando
try {
    docker info | Out-Null
}
catch {
    Write-Host "❌ Docker não está rodando. Por favor, inicie o Docker primeiro." -ForegroundColor Red
    exit 1
}

# Parar containers existentes se estiverem rodando
Write-Host "🛑 Parando containers existentes..." -ForegroundColor Yellow
docker-compose down

# Construir imagens
Write-Host "🔨 Construindo imagens Docker..." -ForegroundColor Blue
docker-compose build --no-cache

# Iniciar serviços
Write-Host "🚀 Iniciando serviços..." -ForegroundColor Green
docker-compose up -d

# Aguardar um pouco para os serviços iniciarem
Write-Host "⏳ Aguardando serviços iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Mostrar status dos containers
Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
docker-compose ps

# Mostrar logs do Django
Write-Host "📝 Logs do Django (últimas 20 linhas):" -ForegroundColor Cyan
docker-compose logs --tail=20 django-app

Write-Host "✅ Ambiente de desenvolvimento iniciado com sucesso!" -ForegroundColor Green
Write-Host "🌐 Aplicação disponível em: http://localhost:8000" -ForegroundColor White
Write-Host "🔧 Evolution API disponível em: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "👤 Credenciais padrão do Django Admin:" -ForegroundColor Yellow
Write-Host "   Usuário: admin" -ForegroundColor White
Write-Host "   Senha: 123456" -ForegroundColor White
Write-Host ""
Write-Host "📋 Comandos úteis:" -ForegroundColor Cyan
Write-Host "  - Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "  - Parar: docker-compose down" -ForegroundColor White
Write-Host "  - Reiniciar: docker-compose restart" -ForegroundColor White
Write-Host "  - Shell Django: docker-compose exec django-app bash" -ForegroundColor White
Write-Host "  - Shell QCluster: docker-compose exec django-qcluster bash" -ForegroundColor White