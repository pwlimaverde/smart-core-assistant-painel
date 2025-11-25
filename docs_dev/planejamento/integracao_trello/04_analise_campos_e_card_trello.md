# Análise de Campos e Representação no Card do Trello

> **⚠️ IMPORTANTE**: Este documento foi atualizado para refletir a implementação atual.  
> **Versão Gratuita**: Custom Fields NÃO estão disponíveis. Todas as informações são exibidas via **Descrição Markdown**.  
> **Última Atualização**: 24/11/2024

---

## 📋 Sumário

Este documento detalha o mapeamento dos campos dos modelos Django para os elementos visuais nos cards do Trello. A tabela abaixo serve como guia para a sincronização de dados entre o sistema de atendimentos e o Trello.

> 💡 **Para detalhes sobre formatação e melhorias implementadas**: Ver [`06_visualizacao_cards_melhorias.md`](./06_visualizacao_cards_melhorias.md)

---

## 🗺️ Tabela de Mapeamento: Django ↔ Trello Card

### Recursos Nativos do Trello (Disponíveis na Versão Gratuita)

| Modelo e Campo Django | Elemento no Card do Trello | Direção | Notas |
|:----------------------|:---------------------------|:--------|:------|
| **Contato.nome_contato** | 📛 **Título do Card** | `→` | Formato: `Nome - Empresa - Assunto - Intents` |
| **Atendimento.assunto** | 📛 **Título do Card** (parte) | `→` | Incluído no título para contexto rápido |
| **Cliente.nome_fantasia** | 📛 **Título do Card** (parte) | `→` | Nome da empresa associada |
| **Atendimento.prioridade** | 🏷️ **Label** | `↔` | Cores: Verde(baixa), Azul(normal), Laranja(alta), Vermelho(urgente) |
| **EtapaFluxo.nome** | 📋 **Lista do Trello** | `↔` | Sincronização bidirecional automática |
| **Atendente.nome** | 👤 **Membro do Card** | `↔` | Atribuição automática ao mover de FILA para TRABALHO |
| **EtapaFluxo.cor** | 🎨 **Cover (Capa)** | `→` | Cor da etapa aplicada como capa do card |
| **Atendimento.data_inicio** | 📅 **Start Date** | `→` | Data de início do atendimento |
| **Atendimento.data_inicio + 1d** | 📅 **Due Date** | `→` | SLA básico (1 dia após início) |
| **Atendimento (TODOS)** | 📝 **Descrição Markdown** | `→` | **Descrição rica formatada** (ver abaixo) |

### Informações na Descrição Markdown

Todas as informações abaixo são renderizadas na **descrição do card** com formatação Markdown aprimorada:

| Campo Django | Seção na Descrição | Formato | Condicional |
|:-------------|:-------------------|:--------|:------------|
| **Atendimento.status** | Título (emoji) | `# {emoji} Atendimento #ID` | Sempre |
| **Contato.nome_contato** | 📋 Informações do Contato | `**Nome:** valor` | Sempre |
| **Contato.telefone** | 📋 Informações do Contato | `` **Telefone:** `valor` `` | Sempre |
| **Contato.email** | 📋 Informações do Contato | `**E-mail:** valor` | Sempre |
| **Atendimento.departamento** | 🎯 Detalhes do Atendimento | `**Departamento:** valor` | Sempre |
| **Atendimento.etapa_atual** | 🎯 Detalhes do Atendimento | `**Etapa Atual:** valor` | Sempre |
| **Atendimento.prioridade** | 🎯 Detalhes do Atendimento | `**Prioridade:** valor {emoji}` | Sempre |
| **Atendimento.canal** | 🎯 Detalhes do Atendimento | `**Canal:** {emoji} valor` | Sempre |
| **Atendimento.produto_servico** | 💼 Informações Comerciais | `**Produto/Serviço:** valor` | Se existir |
| **Atendimento.categoria_venda** | 💼 Informações Comerciais | `**Categoria:** valor` | Se existir |
| **Atendimento.valor_orcamento** | 💼 Informações Comerciais | `**Valor Orçamento:** R$ X.XXX,XX` | Se existir |
| **Atendimento.data_inicio** | ⏱️ Métricas | `**Tempo Total:** há X hora(s)` | Sempre |
| **Atendimento.data_ultima_mensagem** | ⏱️ Métricas | `**Última Interação:** há X hora(s)` | Sempre |
| **Atendimento.atendente_humano** | ⏱️ Métricas | `**Atendente:** nome` ou `⏳ Não atribuído` | Sempre |
| **Atendimento.tags** | ⏱️ Métricas | `**Tags:** tag1, tag2, tag3` | Se existir |
| **Histórico.intents_detectados** | 🤖 Análise de IA | `` - `intent`: valor `` | Se existir |
| **Histórico.entidades_extraidas** | 🤖 Análise de IA | `` - `entidade`: valor `` | Se existir |
| **Mensagem (últimas 5)** | 💬 Mensagens Recentes | Blockquotes com timestamp humanizado | Sempre |

---

## 🎨 Exemplo Visual de um Card Completo

### Título do Card
```
Maria Souza - Empresa XYZ - Dúvida sobre Fatura - solicitacao_informacao
```

### Membros
👤 Carlos Andrade (avatar do atendente)

### Labels
🟠 Alta (label laranja)

### Datas
- **Start**: 22/11/2024 09:15
- **Due**: 23/11/2024 09:15

### Cover (Capa)
Cor laranja (cor da etapa "Em Negociação")

### Descrição

````markdown
# 💬 Atendimento #451

**Assunto:** Dúvida sobre Fatura

## 📋 Informações do Contato

**Nome:** Maria Souza
**Telefone:** `5511987654321`
**E-mail:** maria.souza@email.com

## 🎯 Detalhes do Atendimento

**Departamento:** Comercial
**Etapa Atual:** Em Negociação
**Prioridade:** Alta 🟠
**Canal:** 📱 whatsapp

## 💼 Informações Comerciais

**Produto/Serviço:** Plano Premium
**Categoria:** Assinatura
**Valor Orçamento:** R$ 1.499,90

## ⏱️ Métricas

**Tempo Total:** há 2 dia(s)
**Última Interação:** há 3 hora(s)
**Atendente:** Carlos Andrade

**Tags:** VIP, Primeira Compra

## 🤖 Análise de IA

**Intenções Detectadas:**
- `solicitacao_informacao`: alta
- `duvida_financeira`: média

**Entidades Extraídas:**
- `valor`: R$ 100,00
- `data`: próxima semana

## 💬 Mensagens Recentes (últimas 5)

**há 3 hora(s)**
> Bom dia, recebi minha fatura e o valor parece incorreto. Podem me ajudar?
> 🤖 *Resposta:* Olá Maria! Vou verificar sua fatura imediatamente...

**há 5 hora(s)**
> Obrigada pelo atendimento anterior!
````

---

## 🔄 Sincronização Bidirecional

### Django → Trello (Automático via Signals)

| Evento no Django | Ação no Trello | Signal |
|:-----------------|:---------------|:-------|
| Novo `FluxoAtendimento` | Cria Board | `fluxo_created_sync_trello` |
| Nova `EtapaFluxo` | Cria List | `etapa_created_sync_trello` |
| Novo `Atendimento` | Cria Card | `atendimento_created_sync_trello` |
| `Atendimento.etapa_atual` altera | Move Card entre Lists | `atendimento_etapa_updated_move_card` |
| `Atendimento.atendente_humano` altera | Atribui/Remove Membro | `atendimento_updated_assign_member_trello` |
| Nova `Mensagem` | Atualiza Descrição | `mensagem_created_update_trello_card` |
| `Atendimento.status` = RESOLVIDO | Move para lista "Resolvido" | `atendimento_resolvido_move_to_resolvido` |

### Trello → Django (Via Webhooks)

| Evento no Trello | Ação no Django | Handler |
|:-----------------|:---------------|:--------|
| Mover Card entre Lists | Atualiza `Atendimento.etapa_atual` | `WebhookProcessingService` |
| Atribuir Membro ao Card | Atualiza `Atendimento.atendente_humano` | `WebhookProcessingService` |
| Alterar Label | Atualiza `Atendimento.prioridade` | `WebhookProcessingService` |

---

## 🎯 Estratégia de Formatação

### Emojis de Status
- ⏳ **Fila**: Aguardando atendimento
- 💬 **Em Atendimento**: Conversa ativa
- ⏸️ **Pendência**: Pausado
- ✅ **Resolvido**: Finalizado
- ❌ **Cancelado**: Cancelado

### Emojis de Prioridade
- 🟢 **Baixa**
- 🔵 **Normal**
- 🟠 **Alta**
- 🔴 **Urgente**

### Emojis de Canal
- 📱 **WhatsApp**
- ✈️ **Telegram**
- 📧 **E-mail**
- 🌐 **Web**

### Tempo Humanizado
- "há 30 minuto(s)" em vez de "24/11/2024 14:30"
- "há 2 dia(s)" em vez de "22/11/2024"
- "há menos de 1 minuto" para ações recentes

---

## 💡 Por que NÃO Usamos Custom Fields?

### Limitação da Versão Gratuita
- Custom Fields **não estão disponíveis** em workspaces gratuitos do Trello
- Requerem upgrade para plano pago (Standard/Premium/Enterprise)

### Solução Adotada
- **Descrição Markdown Rica**: Todas as informações em formato visual profissional
- **Labels**: Prioridades com cores
- **Covers**: Cores das etapas
- **Datas Nativas**: Start/Due para SLA
- **Membros**: Atribuição de atendentes

### Benefícios da Abordagem
✅ **Custo Zero**: Funciona 100% na versão gratuita  
✅ **Visualmente Rico**: Markdown + emojis = experiência premium  
✅ **Flexível**: Fácil adicionar/remover informações  
✅ **Portátil**: Descrição funciona em qualquer plano Trello  
✅ **Legível**: Formato humanizado facilita compreensão

---

## 📚 Documentação Relacionada

- **Detalhes de Implementação**: [`06_visualizacao_cards_melhorias.md`](./06_visualizacao_cards_melhorias.md)
- **Estratégia Geral**: [`00_relatorio_final_integracao_trello.md`](./00_relatorio_final_integracao_trello.md)
- **Modelos Trello Sync**: [`03_modelos_trello_sync.md`](./03_modelos_trello_sync.md)

---

## 📊 Recursos Utilizados vs Disponíveis

| Recurso Trello | Versão Gratuita | Implementado | Uso |
|:---------------|:----------------|:-------------|:----|
| Labels | ✅ Sim | ✅ Sim | Prioridades |
| Membros | ✅ Sim | ✅ Sim | Atendentes |
| Descrição Markdown | ✅ Sim | ✅ Sim | Todas as informações |
| Datas (Start/Due) | ✅ Sim | ✅ Sim | SLA e timestamps |
| Covers (Capas) | ✅ Sim | ✅ Sim | Cores das etapas |
| Listas | ✅ Sim (ilimitadas) | ✅ Sim | Etapas do fluxo |
| Checklists | ✅ Sim | ⏳ Planejado | Progresso do fluxo |
| Custom Fields | ❌ Não | ❌ Não | Não disponível |
| Automations | ❌ Limitadas | ❌ Não | Usamos Django Signals |
| Power-Ups | ❌ 1 apenas | ❌ Não | Não necessário |

---

> **Atualizado em**: 24/11/2024  
> **Status**: ✅ Implementação Completa (Categoria A)  
> **Próximos Passos**: Implementar Categoria B (Checklists e Labels Expandidos)