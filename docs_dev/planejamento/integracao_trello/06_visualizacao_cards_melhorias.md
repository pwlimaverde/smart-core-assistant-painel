# Visualização de Cards no Trello: Melhorias e Formatação

> **Status**: ✅ Implementado  
> **Versão**: 1.0  
> **Última Atualização**: 24/11/2024  
> **Branch**: `feature/melhorar-visualizacao-cards-trello`  
> **Commit**: `61b4dd8`

## 📋 Sumário

Este documento detalha as melhorias implementadas na visualização dos cards de atendimento no Trello, focando em otimizar a experiência visual e a legibilidade das informações, respeitando as limitações da versão gratuita do Trello (sem Custom Fields).

---

## 🎯 Motivação

A implementação inicial da sincronização Trello utilizava uma descrição funcional mas básica. Com o objetivo de tornar os cards mais **profissionais**, **escaneáveis** e **informativos**, foram implementadas melhorias significativas na formatação utilizando recursos nativos do Markdown suportados pelo Trello.

### Problemas Identificados (Situação Anterior)

- ❌ Descrição em texto simples com pouca hierarquia visual
- ❌ Timestamps brutos (difíceis de interpretar rapidamente)
- ❌ Informações misturadas sem organização clara
- ❌ Falta de indicadores visuais (emojis) para identificação rápida
- ❌ Seções sempre presentes mesmo quando vazias (poluição visual)

### Benefícios das Melhorias

- ✅ **Hierarquia visual clara** com headings Markdown (# ##)
- ✅ **Emojis estratégicos** para identificação instantânea
- ✅ **Tempo humanizado** ("há 3 horas" vs "23/11/2024 14:30")
- ✅ **Seções condicionais** que aparecem só quando relevantes
- ✅ **Formatação profissional** com negrito, code blocks e blockquotes
- ✅ **Limite inteligente** de mensagens (máximo 5 recentes)

---

## 🏗️ Arquitetura da Solução

### Localização do Código

**Arquivo**: [`src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py`](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/src/smart_core_assistant_painel/app/trello_sync/services/ticket_sync_service.py)

### Componentes Implementados

#### 1. Métodos Auxiliares de Formatação

##### `_get_status_emoji(status: str) -> str`
Retorna emoji apropriado para status do atendimento.

**Mapeamento**:
| Status | Emoji | Significado |
|--------|-------|-------------|
| `fila` | ⏳ | Aguardando atendimento |
| `em_atendimento` | 💬 | Em conversa ativa |
| `pendencia` | ⏸️ | Pausado/aguardando cliente |
| `resolvido` | ✅ | Finalizado com sucesso |
| `cancelado` | ❌ | Cancelado |
| `transferido` | ↪️ | Em transferência |

##### `_get_prioridade_emoji(prioridade: str) -> str`
Retorna emoji apropriado para nível de prioridade.

**Mapeamento**:
| Prioridade | Emoji | Cor do Label |
|------------|-------|--------------|
| `baixa` | 🟢 | Verde |
| `normal` | 🔵 | Azul |
| `alta` | 🟠 | Laranja |
| `urgente` | 🔴 | Vermelho |

##### `_get_canal_emoji(canal: str) -> str`
Retorna emoji apropriado para canal de comunicação.

**Mapeamento**:
| Canal | Emoji |
|-------|-------|
| WhatsApp | 📱 |
| Telegram | ✈️ |
| E-mail | 📧 |
| Web | 🌐 |
| Outros | 💬 |

##### `_format_time_delta(dt: datetime) -> str`
Formata diferença de tempo de forma humanizada.

**Exemplos**:
- `há 2 dia(s)`
- `há 5 hora(s)`
- `há 30 minuto(s)`
- `há menos de 1 minuto`
- `(não disponível)` quando `dt` é `None`

#### 2. Método de Construção de Descrição

##### `_build_rich_description(atendimento: Atendimento) -> str`
Constrói descrição rica do card com formatação Markdown aprimorada.

**Estrutura da Descrição**:
1. **Título Principal** (# heading) com emoji de status
2. **Seção: Informações do Contato** (sempre)
3. **Seção: Detalhes do Atendimento** (sempre)
4. **Seção: Métricas** (sempre)
5. **Seção: Análise de IA** (condicional)
6. **Seção: Mensagens Recentes** (sempre, máx 5)

---

## 📄 Exemplo de Card Formatado

### Visualização no Trello

```markdown
# 💬 Atendimento #451

**Assunto:** Dúvida sobre Fatura

## 📋 Informações do Contato

**Nome:** Maria Souza
**Telefone:** `5511987654321`
**E-mail:** maria.souza@email.com

## 🎯 Detalhes do Atendimento

**Prioridade:** Alta 🟠
**Canal:** 📱 whatsapp

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

```

---

## 🎨 Recursos de Formatação Utilizados

### Headings Markdown (# ##)
Criam hierarquia visual clara e permitem navegação rápida:
- `#` - Título principal com emoji de status
- `##` - Seções (Contato, Detalhes, Métricas, etc)

### Emojis Estratégicos
Funcionam como "ícones" para identificação visual instantânea:
- **No título**: Status do atendimento (⏳ 💬 ✅ ❌)
- **Nas seções**: Tipo de informação (📋 🎯 ⏱️ 🤖 💬)
- **Nos dados**: Prioridade (🟢 🔵 🟠 🔴), Canal (📱 ✈️)

### Formatação de Texto
- **Negrito (`**texto**`)**: Labels e destaque de informações-chave
- **Code blocks (`` `código` ``)**: Telefones, códigos, valores técnicos
- **Blockquotes (`> texto`)**: Mensagens do histórico
- **Itálico (`*texto*`)**: Metainformações, notas

### Seções Condicionais
Seções só aparecem quando há dados relevantes:
- **Análise de IA**: Só se houver intents/entidades detectadas
- **Tags**: Só se houver tags associadas

### Limitações Inteligentes
- **Mensagens**: Máximo 5 mais recentes
- **Preview de texto**: 200 caracteres por mensagem
- **Intents/Entidades**: Máximo 5 de cada

---

## 💡 Decisões de Design

### Por que Emojis?
- **Universais**: Funcionam em qualquer idioma/dispositivo
- **Visuais**: Identificação instantânea sem ler texto
- **Nativos**: Suportados pelo Trello sem configuração
- **Leves**: Não impactam performance ou tamanho

### Por que Tempo Humanizado?
- **Intuitivo**: "há 3 horas" > "24/11/2024 14:30"
- **Relativo**: Sempre atualizado em relação ao momento atual
- **Contexto**: Facilita identificar atendimentos estagnados

### Por que Seções Condicionais?
- **Limpeza visual**: Evita poluição com seções vazias
- **Relevância**: Mostra só o que importa
- **Flexibilidade**: Adapta-se a diferentes tipos de atendimento

### Por que Limitar Mensagens?
- **Performance**: Descrições muito longas podem travar
- **Foco**: Últimas 5 mensagens geralmente são suficientes
- **Limite do Trello**: 16.384 caracteres na descrição

---

## 🔄 Atualização Automática

### Quando a Descrição é Atualizada?

1. **Criação do card**: Ao criar novo atendimento
2. **Nova mensagem**: Signal `mensagem_created_update_trello_card`
3. **Mudança de atendente**: Signal `atendimento_updated_assign_member_trello`
4. **Mudança de etapa**: Signal `atendimento_etapa_updated_move_card`

### Debouncing (Planejado - Categoria C)

Para evitar muitas chamadas API em conversas rápidas, está planejado implementar debouncing de 30 segundos para atualizações de mensagens.

---

## 🔗 Integração com Outros Recursos

### Labels (Já Implementado)
Os labels de prioridade complementam os emojis:
- Label **Verde** + emoji 🟢 = Baixa prioridade em dois locais
- Label **Vermelho** + emoji 🔴 = Urgente, máxima visibilidade

### Covers (Já Implementado)
A cor da capa do card reflete a cor da etapa:
- Aplicado automaticamente ao mover entre listas
- Mapeamento hex → cores Trello via `_map_hex_to_trello_color()`

### Datas (Já Implementado)
- **Start**: `data_inicio` do atendimento
- **Due**: `data_inicio + 1 dia` (SLA básico)
- Atualizado em cada sync da descrição

### Checklists (Planejado - Categoria B)
Próxima melhoria planejada:
- Checklist com progresso do fluxo
- Etapas anteriores marcadas como completas
- Visual do andamento do atendimento

---

## 📊 Impacto e Métricas

### Código
- **+212 linhas**: Métodos auxiliares + refatoração
- **-66 linhas**: Lógica antiga removida
- **Saldo**: +146 linhas (25% de aumento no arquivo)

### Legibilidade
- **Antes**: Texto linear sem hierarquia
- **Depois**: 7 seções organizadas com headings

### Escaneabilidade
- **Antes**: Scan completo necessário
- **Depois**: Emojis permitem identificação em <1 segundo

### Profissionalismo
- **Antes**: Aparência básica/técnica
- **Depois**: Visual moderno e polido

---

## 🧪 Testando as Melhorias

### Pré-requisitos
- Board Trello configurado e sincronizado
- Cluster Django Q rodando (`uv run task cluster`)
- Ao menos um atendimento criado

### Checklist de Validação
- [ ] Título do card contém emoji de status
- [ ] Descrição usa headings (# ##)
- [ ] Seções organizadas e bem formatadas
- [ ] Emojis aparecem corretamente
- [ ] Tempo está humanizado ("há X horas")
- [ ] Mensagens em blockquote (>)
- [ ] Máximo 5 mensagens visíveis
- [ ] Telefone formatado com backticks
- [ ] Seções comerciais só aparecem se houver dados
- [ ] Tags aparecem quando existentes

### Casos de Teste

**Teste 1**: Atendimento sem atendente  
→ Espera-se "⏳ Não atribuído" na seção Métricas

**Teste 2**: Atendimento urgente  
→ Espera-se emoji 🔴 e label vermelho

**Teste 3**: Múltiplas mensagens (>5)  
→ Espera-se apenas 5 mais recentes

**Teste 4**: Atendimento recém-criado  
→ Espera-se "há menos de 1 minuto"

---

## 🚀 Melhorias Futuras

### Categoria B: Recursos Nativos (Média Prioridade)

#### Checklists de Progresso
Criar checklist automático mostrando andamento no fluxo:
```
✅ Triagem Inicial
✅ Análise de IA
⬜ Aguardando Atendente
⬜ Em Atendimento
⬜ Finalizado
```

#### Labels Expandidos
Adicionar labels para:
- **Canal**: Cores frias (lime, sky)
- **Tags especiais**: VIP (purple), Primeira Compra (pink)

### Categoria C: Otimizações (Baixa Prioridade)

#### Cache de Labels
Implementar `@lru_cache` para evitar chamadas repetidas de `ensure_labels()`.

#### Debouncing de Atualizações
Agrupar atualizações de mensagens com delay de 30s para reduzir requests API.

---

## 📚 Referências

- [Trello REST API - Cards](https://developer.atlassian.com/cloud/trello/rest/api-group-cards/)
- [Trello Markdown Guide](https://support.atlassian.com/trello/docs/how-to-format-your-text-in-trello/)
- [Limitações Versão Gratuita](https://trello.com/pricing)

---

## 📝 Changelog

### v1.0 - 24/11/2024
- ✅ Implementados métodos auxiliares de emojis
- ✅ Implementado método de formatação de tempo humanizado
- ✅ Refatorado `_build_rich_description()` com nova estrutura
- ✅ Adiciona headings Markdown (# ##)
- ✅ Organização por seções lógicas
- ✅ Formatação profissional (negrito, code, blockquotes)
- ✅ Limite de 5 mensagens recentes
- ✅ Seções condicionais (comercial, IA)
