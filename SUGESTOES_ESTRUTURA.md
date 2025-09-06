# Plano de Reorganização e Migração (Banco do Zero)

Este documento define, de forma operacional e faseada, como reorganizar o projeto em múltiplos apps, iniciar o banco do zero, remover migrações antigas, manter apenas a 0001 para ser criada e aplicada ao final, mover a habilitação do pgvector para o app de atendimentos e remover o app `oraculo` ao término. Cada fase é independente e possui objetivos, passos, comandos e critérios de saída claros (gate).

Contexto de infraestrutura
- Banco hospedado em servidor local: http://192.168.3.127/
- Execução e validação via Docker (Windows), com `uv`/Taskipy
- Sem segredos no código; variáveis sensíveis via `.env` (fornecer `.env.example`)

Arquitetura alvo (apps)
- operacional: recursos internos (departamentos, atendentes, capacidade)
- clientes: entidades externas (clientes, contatos)
- atendimentos: fluxo de conversas/atendimentos; migração pgvector residirá aqui
- treinamento: base de conhecimento, documentos, vetorização
- oraculo: será removido ao final (compatibilidade temporária durante transição)

Diretrizes obrigatórias
- Banco do zero: não haverá migrações aplicadas até a Fase Final
- Remoção de migrações atuais: deletar agora todas as migrações existentes (manter apenas `__init__.py`); a 0001 de cada app será criada e aplicada somente na Fase Final
- pgvector: habilitação via `RunSQL("CREATE EXTENSION IF NOT EXISTS vector;")` ficará na migração 0001 do app `atendimentos` (na Fase Final)
- Remoção do `oraculo`: eliminar o app antes de criar as migrações finais; toda lógica deve estar nos novos apps
- Qualidade: manter lint, type-check e testes sempre verdes; pré-migração sem DB real; pós-migração com DB real

Política de testes por modo
- Pré-migração (Fases 0–9):
  - uv run task lint
  - uv run task type-check
  - uv run task test (foco em lógica de negócio; usar mocks para DB/ORM)
  - Cobertura de negócio ≥ 80%
- Pós-migração (Fase Final):
  - uv run task lint
  - uv run task type-check
  - uv run task test-docker (com DB real e migrações aplicadas)
  - Cobertura global ≥ 80%

Fase 0 — Preparação e limpeza de migrações (executar agora)
Objetivo
- Baseline verde e repositório sem migrações (apenas `__init__.py` em cada `migrations/`)

Entradas
- Código atual
- Padrões do projeto (PEP8, mypy, ruff, pytest)

Passos
1) Sincronizar dependências: uv sync --dev
2) Remover todas as migrações existentes mantendo apenas `__init__.py` em cada diretório migrations
3) Garantir que nenhum arquivo 000*.py permaneceu no repositório
4) Configurar estratégia de testes sem DB (mocks/fixtures e, se aplicável, marcar testes que requerem DB)

Comandos (Windows/PowerShell)
- Lint, tipos e testes (sem DB):
  - uv run task lint
  - uv run task type-check
  - uv run task test
- Remoção de migrações (exemplos; execute com cautela e revise os caminhos):
  - Listar migrações: Get-ChildItem -Recurse -Filter "000*.py" src | Select-Object FullName
  - Remover migrações (exceto __init__.py):
    - Get-ChildItem -Recurse src -Include 000*.py | Where-Object { $_.Name -ne "__init__.py" } | Remove-Item -Force
  - Confirmar que restaram apenas __init__.py em cada migrations/

Gate (saída da fase)
- Repositório sem migrações (apenas __init__.py)
- uv run task lint OK, uv run task type-check OK
- uv run task test OK (≥ 80% cobertura de negócio)

Fase 1 — Esqueleto dos novos apps (sem mover código)
Objetivo
- Criar estrutura vazia para operacional, clientes, atendimentos e treinamento

Passos
1) Criar diretórios mínimos: apps.py, admin.py, models/, migrations/ (com __init__.py), views.py, urls.py, templates/<app>/, tests/
2) Registrar os apps em INSTALLED_APPS (sem modelos ainda)
3) Garantir que migrations/ permaneça vazio (apenas __init__.py)

Comandos
- uv run task lint
- uv run task type-check
- uv run task test

Gate
- Estrutura criada, lint e tipos OK, testes de negócio OK (≥ 80%)

Fase 2 — Mapeamento e plano de movimentação de modelos
Objetivo
- Tabelar cada entidade e seu domínio de destino com relacionamentos

Passos
1) Mapear entidades atuais do oraculo para os novos apps
2) Desenhar relacionamentos e dependências entre apps
3) Definir estratégia final de migrações: preservar db_table, ajustar ContentType/app_label via RunPython (aplicado apenas na Fase Final)
4) Atualizar este documento conforme decisões

Comandos e Gate
- uv run task lint, type-check, test
- Lint e tipos OK; testes de negócio OK

Fase 3 — Plano de templates/URLs/views/admin/signals
Objetivo
- Planejar divisão por domínio sem mover código ainda

Passos
1) Namespacing de templates por app
2) urls.py por app, agregando no roteador principal via include()
3) Separar admin e signals por app (ordem de import segura)

Comandos e Gate
- uv run task lint, type-check, test
- OK nos três

Fase 4 — Compatibilidade temporária (reexports)
Objetivo
- Planejar facades no oraculo para manter compatibilidade durante a transição

Passos
1) Definir reexports (import e reexport dos novos apps) para nomes públicos antigos
2) Documentar DeprecationWarning e janela de convivência

Comandos e Gate
- uv run task lint, type-check, test
- OK nos três

Fase 5 — Movimentação de código (sem migrações)
Objetivo
- Mover models, views, urls, admin, signals e templates para os novos apps mantendo o projeto compilável

Passos
1) Mover módulos por domínio
2) Ajustar imports
3) Manter reexports temporários no oraculo até a fase 9
4) Garantir migrations/ vazio (apenas __init__.py)

Comandos e Gate
- uv run task lint, type-check, test (usar mocks para DB)
- OK nos três, cobertura de negócio ≥ 80%

Fase 6 — Testes e qualidade (pré‑migração)
Objetivo
- Reorganizar testes por app e consolidar cobertura sem DB

Passos
1) Realocar testes para cada app respectivo
2) Atualizar fixtures/factories para não depender de DB real

Comandos e Gate
- uv run task lint, type-check, test
- OK nos três, cobertura de negócio ≥ 80%

Fase 7 — Observabilidade e scripts
Objetivo
- Alinhar logs (loguru), tasks (Taskipy) e scripts à nova estrutura

Passos
1) Revisar mensagens/logs e caminhos
2) Atualizar scripts utilitários, sem tocar em migrações

Comandos e Gate
- uv run task lint, type-check, test
- OK nos três

Fase 8 — Documentação e comunicação
Objetivo
- Atualizar README/docs/diagramas e guias de uso

Passos
1) Revisar documentação para refletir a nova arquitetura
2) Preparar guia para integradores/usuários

Comandos e Gate
- uv run task lint, type-check, test
- OK nos três

Fase 9 — Remoção do app oraculo (antes das migrações)
Objetivo
- Remover definitivamente o app oraculo do código e de INSTALLED_APPS

Passos
1) Eliminar reexports e módulos do oraculo
2) Remover rotas/templates antigos
3) Confirmar que todas importações apontam para os novos apps
4) migrations/ continuam vazios (apenas __init__.py)

Comandos e Gate
- uv run task lint, type-check, test
- OK nos três

Fase Final — Criação e aplicação das migrações 0001 (com pgvector)
Objetivo
- Criar e aplicar as migrações 0001 de cada app e habilitar pgvector no app atendimentos

Passos
1) Verificar `.env` apontando para o banco em http://192.168.3.127/ (ou Docker local conforme ambiente); nunca versionar segredos
2) No app atendimentos, criar migração 0001 com RunSQL("CREATE EXTENSION IF NOT EXISTS vector;")
3) Gerar migrações iniciais 0001 para todos os apps na ordem de dependências (ex.: clientes → operacional → treinamento → atendimentos)
4) Aplicar migrações no Docker: uv run task migrate
5) Executar suíte com DB real: uv run task test-docker e garantir cobertura global ≥ 80%

Saídas
- Banco inicializado do zero com a estrutura final
- pgvector habilitado via migração 0001 do app atendimentos
- App oraculo removido definitivamente

Notas de portabilidade
- Mesmo que o ambiente crie a extensão via SQL externo (ex.: initdb/00-extensions.sql), mantenha a migração idempotente no atendimentos (RunSQL com IF NOT EXISTS) para garantir portabilidade

Checklist resumido por fase (copie para PRs)
- Fase N
  - Lint (uv run task lint): OK
  - Type-check (uv run task type-check): OK
  - Testes (pré: uv run task test | pós: uv run task test-docker): OK
  - Cobertura (pré: negócio ≥ 80% | pós: global ≥ 80%): OK
  - Itens de passos concluídos e documentados

Observações finais
- Não criar/aplicar migrações antes da Fase Final
- Garantir que `migrations/` contenha apenas `__init__.py` até a Fase Final
- Remover o `oraculo` antes de gerar as migrações 0001
- A migração do pgvector deve existir apenas no app `atendimentos`
