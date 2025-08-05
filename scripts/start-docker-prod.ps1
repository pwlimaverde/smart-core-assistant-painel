# Script PowerShell para iniciar o ambiente de produção com Docker

Write-Host "🐳 Iniciando ambiente de produção Smart Core Assistant..." -ForegroundColor Cyan

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
Write-Host "🔨 Construindo imagens Docker para produção..." -ForegroundColor Blue
docker-compose build

# Iniciar serviços
Write-Host "🚀 Iniciando serviços de produção..." -ForegroundColor Green
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

Write-Host "✅ Ambiente de produção iniciado com sucesso!" -ForegroundColor Green
Write-Host "🌐 Aplicação disponível em: http://localhost:8000" -ForegroundColor White
Write-Host "🔧 Evolution API disponível em: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "📋 Comandos úteis:" -ForegroundColor Cyan
Write-Host "  - Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "  - Parar: docker-compose down" -ForegroundColor White
Write-Host "  - Reiniciar: docker-compose restart" -ForegroundColor White
Write-Host "  - Shell Django: docker-compose exec django-app bash" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  ATENÇÃO: Este é o ambiente de PRODUÇÃO!" -ForegroundColor Red