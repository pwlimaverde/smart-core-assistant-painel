# PRD - Sprint Features Q1/2026

## Título
Teste de Treinamento, Whitelist UI e Refatoração de Apps

## Resumo Executivo
Este sprint abrange a implementação de 2 features principais no Smart Core Assistant Painel:
1. **Whitelist UI** - Painel de configurações no dashboard para gerenciar números ignorados
2. **Teste de Treinamento** - Chat interativo para testar respostas do bot na página de treinamento

A Feature 2 (Refatoração de Apps Django) foi adiada para um sprint futuro devido ao alto risco.

## Problema
- Administradores precisam acessar o Django Admin para gerenciar a whitelist de números, uma operação que deveria ser acessível no dashboard principal.
- Não existe forma de testar as respostas do bot antes de colocá-lo em produção, obrigando testes manuais via WhatsApp.

## Solução Proposta
- Criar um painel de configurações no dashboard com CRUD completo de whitelist
- Criar interface de chat para testar respostas do bot com análise de entidades e intents

## Stakeholders
| Papel | Nome | Responsabilidade |
|-------|------|------------------|
| Developer | Claude Code | Implementação completa |
| QA | Usuário | Teste manual pós-implementação |

## Requisitos Funcionais

### RF-001: Painel de Configurações - Whitelist
**Descrição:** CRUD completo de números na whitelist via dashboard
**Prioridade:** Alta
**Critérios de Aceite:**
- [x] Listar números da whitelist com nome, telefone, status e data
- [x] Adicionar novo número com validação de formato brasileiro
- [x] Editar nome e telefone de números existentes
- [x] Excluir números com confirmação
- [x] Toggle ativo/inativo inline
- [x] Busca por nome ou telefone
- [x] Permissões de admin verificadas

### RF-002: Teste de Treinamento - Chat Interativo
**Descrição:** Interface para enviar mensagens simuladas e ver resposta do bot
**Prioridade:** Alta
**Critérios de Aceite:**
- [x] Enviar mensagem e receber resposta do bot
- [x] Visualizar score de confiabilidade
- [x] Visualizar entidades extraídas
- [x] Visualizar intents detectados
- [x] Avaliar resposta como boa ou ruim
- [x] Corrigir resposta e armazenar feedback
- [x] Model de feedback para registro

### RF-003: Navegação
**Descrição:** Links de acesso às novas features
**Prioridade:** Alta
**Critérios de Aceite:**
- [x] Link "Configurações" na sidebar do dashboard
- [x] Link "Testar Respostas" na página verificar_query_compose

## Requisitos Não-Funcionais

### RNF-001: Multi-Tenant
- Isolamento de dados por tenant obrigatório
- WhiteList e QueryTestFeedback isolados por banco do tenant

### RNF-002: Design System
- Seguir padrão Tailwind CSS (stone colors, rounded-xl, shadow-sm)
- Cor destaque: #a98f71

### RNF-003: Segurança
- CSRF protection em todos os forms
- Validação de permissões de admin
- Input sanitizado

## Escopo

### Incluído
- Feature 3: Whitelist UI completa
- Feature 1: Teste de Treinamento completo
- Navegação e links

### Não Incluído (Fora de Escopo)
- Feature 2: Refatoração de Apps Django (adiada)
- Testes automatizados (teste manual)
- Streaming de respostas LLM
- Painel de configurações IA/Integrações (futuro)

## Riscos
| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| LLM lento na resposta | Média | Baixo | Loading spinner + timeout |
| Custo de API por teste | Baixa | Baixo | Uso em ambiente de dev |
| Dados de treinamento ausentes | Média | Médio | Mensagem informativa |

## Aprovações
| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Developer | Claude Code | 2026-02-06 | Aprovado |
