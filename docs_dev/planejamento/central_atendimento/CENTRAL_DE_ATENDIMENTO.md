# Central de Atendimento - Documentação Completa

## 📋 Sumário Executivo

Este documento consolida toda a documentação de planejamento para o desenvolvimento da Central de Atendimento do Smart Core Assistant. A solução implementa fluxos de atendimento personalizados por departamento, substituindo o sistema fixo atual por uma arquitetura flexível e escalável baseada em Django.

### 🎯 Objetivo Principal
Criar uma central de atendimento multicanal onde um chatbot realiza a triagem inicial e transfere para atendimento humano quando necessário, com fluxos totalmente personalizáveis por departamento através de uma interface Kanban.

### 🏗️ Abordagem Técnica
- **Arquitetura Monolítica Django** para aproveitar estrutura existente
- **Django REST Framework** para APIs RESTful
- **Django Channels** para comunicação em tempo real via WebSockets
- **Interface Kanban** com drag-and-drop e atualizações em tempo real

---

## 1. Arquitetura do Sistema

### 1.1. Componentes Principais

#### Backend Django
- **App `atendimentos`**: Models, services, APIs e consumers
- **App `clientes`**: Gestão de clientes e contatos
- **App `operacional`**: Departamentos e atendentes

#### Tecnologias Integradas
- **Django REST Framework**: APIs para consumo do frontend
- **Django Channels**: WebSockets para atualizações em tempo real
- **Django Signals**: Eventos internos para sincronização
- **PostgreSQL**: Banco de dados relacional com JSON fields
- **Redis**: Cache para performance

#### Frontend SPA
- Aplicação de página única (React/Vue.js)
- Consumo da API RESTful
- Conexão via WebSocket para updates em tempo real
- Componentes Kanban reativos

### 1.2. Fluxo de Comunicação

```
[Cliente] → [Webhook Externo] → [API Django] → [Lógica de Negócio] 
    ↓
[Banco PostgreSQL] ← [Django ORM] ← [Services] ← [Signals]
    ↓
[WebSocket Groups] → [Frontend Kanban] → [Interface Atendente]
```

---

## 2. Modelagem de Dados

### 2.1. Estrutura Personalizável de Fluxos

O sistema utiliza uma arquitetura dinâmica onde cada departamento define seu próprio fluxo de trabalho através de etapas personalizáveis:

#### FluxoAtendimento
```python
class FluxoAtendimento(models.Model):
    """Define o fluxo de trabalho personalizado para um departamento."""
    departamento = models.OneToOneField(Departamento, ...)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
```

#### EtapaFluxo
```python
class EtapaFluxo(models.Model):
    """Representa cada coluna no kanban de um departamento."""
    fluxo = models.ForeignKey(FluxoAtendimento, related_name="etapas", ...)
    nome = models.CharField(max_length=50)
    descricao = models.CharField(max_length=200, blank=True)
    ordem = models.PositiveIntegerField()
    cor = models.CharField(max_length=7, default="#6B7280")  # Hex color
    tipo_etapa = models.CharField(max_length=20, choices=TipoEtapa.choices)
    permite_atribuicao = models.BooleanField(default=True)
    regras_transicao = models.JSONField(default=dict)
```

#### TipoEtapa (Enum)
```python
class TipoEtapa(models.TextChoices):
    FILA = "fila", "Fila de Entrada"
    TRABALHO = "trabalho", "Em Trabalho"
    ESPERA = "espera", "Aguardando Resposta"
    FINALIZACAO = "finalizacao", "Finalização"
```

#### MovimentoFluxo
```python
class MovimentoFluxo(models.Model):
    """Histórico de movimentações entre etapas."""
    atendimento = models.ForeignKey(Atendimento, ...)
    etapa_origem = models.ForeignKey(EtapaFluxo, related_name="movimentos_saida", ...)
    etapa_destino = models.ForeignKey(EtapaFluxo, related_name="movimentos_entrada", ...)
    atendente = models.ForeignKey(AtendenteHumano, null=True, ...)
    data_movimento = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True)
    duracao_segundos = models.PositiveIntegerField(null=True)
```

### 2.2. Estrutura dos Models Dinâmicos

O sistema utiliza uma estrutura de models que permite total flexibilidade na definição de fluxos de trabalho por departamento, com controle de atribuição manual realizado pelos próprios atendentes.

**Funcionamento do Sistema:**
1. **Novo atendimento** entra na etapa do tipo `FILA`
2. **Atendente visualiza** todos os atendimentos em fila
3. **Ao mover da FILA para TRABALHO**, sistema automaticamente atribui ao atendente que realizou a ação
4. **Movimento entre etapas de TRABALHO** mantém a atribuição
5. **Retorno para FILA** remove a atribuição (atendimento fica disponível para outros)

---

### 2.3. Análise Detalhada dos Models

#### 1. FluxoAtendimento - O "Container" do Departamento

```python
class FluxoAtendimento(models.Model):
    departamento = models.OneToOneField(Departamento, ...)
    nome = models.CharField(max_length=100)  # Ex: "Fluxo Comercial V2"
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
```

**Por que existe?**
- **Isolamento**: Cada departamento tem seu próprio fluxo, sem interferir nos outros
- **Versionamento**: Permite criar "Fluxo Comercial V2" e migrar gradualmente
- **Controle**: Um departamento pode ter fluxo desativado sem afetar outros

**Exemplo Prático:**
```
Departamento Comercial → FluxoAtendimento(id=1, nome="Fluxo Comercial")
Departamento Financeiro → FluxoAtendimento(id=2, nome="Fluxo Financeiro") 
Departamento Suporte → FluxoAtendimento(id=3, nome="Fluxo Suporte Técnico")
```

#### 2. EtapaFluxo - As "Colunas" do Kanban

```python
class EtapaFluxo(models.Model):
    fluxo = models.ForeignKey(FluxoAtendimento, related_name="etapas", ...)
    nome = models.CharField(max_length=50)  # Ex: "Aguardando Pagamento"
    ordem = models.PositiveIntegerField()   # Ordem: 3ª coluna
    cor = models.CharField(max_length=7)    # Cor: "#FF6B6B"
    tipo_etapa = models.CharField(...)      # Tipo: ESPERA
    permite_atribuicao = models.BooleanField(default=True)
    regras_transicao = models.JSONField(default=dict)
```

**Por que existe?**
- **Flexibilidade Total**: Cada departamento define suas próprias colunas
- **Visual Personalizado**: Cores diferentes para cada tipo de etapa
- **Regras Específicas**: Cada etapa pode ter regras diferentes

**Exemplo Comparativo:**

| Departamento Comercial | Departamento Suporte |
|------------------------|----------------------|
| 📥 Solicitação (fila) | 🆕 Novo Chamado (fila) |
| 📞 Em Contato (trabalho) | 🔬 Diagnóstico (trabalho) |
| 💳 Aguardando Pagamento (espera) | 🛠️ Em Reparo (trabalho) |
| ✅ Concluído (finalização) | ✅ Resolvido (finalização) |

#### 3. TipoEtapa - A "Classificação Inteligente"

```python
class TipoEtapa(models.TextChoices):
    FILA = "fila", "Fila de Entrada"        # Todos podem ver/mover
    TRABALHO = "trabalho", "Em Trabalho"     # Apenas atendente atribuído pode mover
    ESPERA = "espera", "Aguardando Resposta" # Apenas atendente atribuído pode mover
    FINALIZACAO = "finalizacao", "Finalização" # Etapa terminal
```

**Por que existe?**
- **Permissões Automáticas**: O sistema sabe quem pode ver/mover o quê
- **Lógica de Negócio**: Comportamentos diferentes por tipo
- **Métricas Específicas**: Calcular tempo diferente para cada tipo

**Regras por Tipo:**
```python
if etapa.tipo_etapa == TipoEtapa.FILA:
    # Todos os atendentes do departamento podem ver
    # Ao mover para TRABALHO, atribui automaticamente ao atendente
    
elif etapa.tipo_etapa == TipoEtapa.TRABALHO:
    # Apenas o atendente atribuído pode ver/mover
    # Calcula tempo de produtividade do atendente
    
elif etapa.tipo_etapa == TipoEtapa.ESPERA:
    # Esperando ação externa (cliente, fornecedor, etc.)
    # Não conta contra produtividade do atendente
    # Apenas atendente atribuído pode mover
    
elif etapa.tipo_etapa == TipoEtapa.FINALIZACAO:
    # Etapa terminal - não pode voltar
    # Gera métricas finais do atendimento
```

#### 4. MovimentoFluxo - O "Rastro Digital"

```python
class MovimentoFluxo(models.Model):
    atendimento = models.ForeignKey(Atendimento, ...)
    etapa_origem = models.ForeignKey(EtapaFluxo, related_name="movimentos_saida", ...)
    etapa_destino = models.ForeignKey(EtapaFluxo, related_name="movimentos_entrada", ...)
    atendente = models.ForeignKey(AtendenteHumano, null=True, ...)
    data_movimento = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True)
    duracao_segundos = models.PositiveIntegerField(null=True)
```

**Por que existe?**
- **Auditoria Completa**: Quem moveu, quando, por quê
- **Métricas Precisas**: Tempo exato em cada etapa
- **Análise de Performance**: Identificar gargalos e produtividade
- **Responsabilidade**: Rastrear decisões e atribuições

**Exemplo de Histórico:**
```python
# Histórico completo do Atendimento #123
Movimento 1: 📥 Fila → 📞 Em Contato 
    (João moveu, "Assumindo caso da fila", atribuído para João)
Movimento 2: 📞 Em Contato → 💳 Aguardando Pagamento 
    (João moveu, "Cliente solicitou boleto", mantido com João)
Movimento 3: 💳 Aguardando Pagamento → ✅ Concluído 
    (João moveu, "Pagamento confirmado", mantido com João)

# Métricas geradas:
# - Tempo na Fila: 5 minutos (antes da atribuição)
# - Tempo em Contato: 2 horas 
# - Tempo Aguardando Pagamento: 24 horas
# - Tempo Total: 26h 5min
# - Produtividade do João: 1 atendimento concluído em 26h
```

---

### 2.4. Fluxo de Atribuição Manual na Prática

#### Cenário 1: Atendente Assume Novo Caso

```python
# 1. Atendente João vê card na fila "📥 Solicitação"
# 2. João arrasta card para "📞 Em Contato" (primeira etapa TRABALHO)

# Sistema executa automaticamente:
movimento = MovimentoFluxo.objects.create(
    atendimento=atendimento_123,
    etapa_origem=etapa_fila,          # "📥 Solicitação"
    etapa_destino=etapa_contato,       # "📞 Em Contato"
    atendente=joao_silva,              # Quem moveu
    motivo="Assumindo caso da fila"
)

# Atendimento atualizado:
atendimento_123.etapa_atual = etapa_contato
atendimento_123.atendente_humano = joao_silva  # 🔥 ATRIBUIÇÃO AUTOMÁTICA
atendimento_123.save()
```

#### Cenário 2: Movimento Entre Etapas de Trabalho

```python
# 1. João move de "📞 Em Contato" para "💳 Aguardando Pagamento"

movimento = MovimentoFluxo.objects.create(
    atendimento=atendimento_123,
    etapa_origem=etapa_contato,       # "📞 Em Contato"
    etapa_destino=etapa_pagamento,    # "💳 Aguardando Pagamento"
    atendente=joao_silva,              # Mantém atribuído para João
    motivo="Enviando boleto para cliente"
)

# Atendimento mantém atribuição:
atendimento_123.etapa_atual = etapa_pagamento
# atendimento_123.atendente_humano = joao_silva (mantido)
atendimento_123.save()
```

#### Cenário 3: Devolução para Fila (Reatribuição)

```python
# 1. João move de "💳 Aguardando Pagamento" para "📥 Solicitação"

movimento = MovimentoFluxo.objects.create(
    atendimento=atendimento_123,
    etapa_origem=etapa_pagamento,    # "💳 Aguardando Pagamento"
    etapa_destino=etapa_fila,        # "📥 Solicitação"
    atendente=joao_silva,            # João que devolveu
    motivo="Cliente pediu pra reagendar"
)

# Atendimento perde atribuição:
atendimento_123.etapa_atual = etapa_fila
atendimento_123.atendente_humano = None  # 🔥 REMOVE ATRIBUIÇÃO
atendimento_123.save()
```

---

### 2.5. Características do Sistema

#### ✅ Funcionalidades Operacionais
1. **Código Simplificado** - Algoritmos diretos de movimentação e atribuição
2. **Controle do Atendente** - Cada um escolhe seus casos baseado em especialidade/carga
3. **Visibilidade Transparente** - Todos veem a fila e podem decidir quem assume
4. **Flexibilidade Natural** - Atendentes podem negociar entre si quem pega qual caso

#### ✅ Benefícios Operacionais
1. **Produtividade Focada** - Atendentes concentram-se nos casos que dominam
2. **Especialização Natural** - Casos complexos direcionam-se aos especialistas
3. **Ambiente Colaborativo** - Processos de atribuição baseados em negociação
4. **Escala Adaptativa** - Novos atendentes integram-se ao fluxo naturalmente

#### ✅ Métricas Disponíveis
1. **Tempo em Fila** - Período de espera antes da atribuição
2. **Produtividade Individual** - Casos assumidos e resolvidos por atendente
3. **Tempo de Atendimento** - Desde atribuição até conclusão
4. **Taxa de Devolução** - Frequência de retorno para fila

---

### 2.6. Implementação do Sistema

```python
# Lógica de movimentação e atribuição
def mover_atendimento_para_trabalho(atendimento, etapa_destino, atendente):
    # Atribuição automática ao mover de FILA para TRABALHO
    if etapa_origem.tipo_etapa == TipoEtapa.FILA and etapa_destino.tipo_etapa == TipoEtapa.TRABALHO:
        atendimento.atendente_humano = atendente
    elif etapa_destino.tipo_etapa == TipoEtapa.FILA:
        atendimento.atendente_humano = None  # Remove atribuição
    
    atendimento.etapa_atual = etapa_destino
    atendimento.save()
    
    # Criar registro de movimento
    MovimentoFluxo.objects.create(
        atendimento=atendimento,
        etapa_origem=etapa_origem,
        etapa_destino=etapa_destino,
        atendente=atendente
    )
```

### 2.7. Modelos Principais

#### Atendimento (Atualizado)
```python
class Atendimento(models.Model):
    # Campos existentes
    cliente = models.ForeignKey("clientes.Cliente", ...)
    atendente_humano = models.ForeignKey("operacional.AtendenteHumano", null=True, ...)
    data_inicio = models.DateTimeField(...)
    data_fim = models.DateTimeField(null=True, ...)
    data_ultima_mensagem = models.DateTimeField(...)
    ativo = models.BooleanField(default=True)
    
    # Novo campo para fluxo personalizado
    etapa_atual = models.ForeignKey(EtapaFluxo, null=True, ...)
    
    # Campos específicos por departamento (exemplos)
    valor_orcamento = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    produto_servico = models.CharField(max_length=100, blank=True)
    categoria_venda = models.CharField(max_length=50, blank=True)
    prioridade = models.CharField(max_length=20, choices=Prioridade.choices)
    tags = models.JSONField(default=list)
```

#### AtendenteHumano (Atualizado)
```python
class AtendenteHumano(models.Model):
    user = models.ForeignKey("auth.User", ...)
    departamento = models.ForeignKey("operacional.Departamento", ...)
    nome_completo = models.CharField(max_length=255)
    max_atendimentos_simultaneos = models.PositiveIntegerField(default=3)
    horario_trabalho = models.CharField(max_length=255, blank=True)
    data_ultima_atribuicao = models.DateTimeField(null=True)
    disponivel = models.BooleanField(default=True)
    especialidades = models.TextField(blank=True)
```

#### Cliente
```python
class Cliente(models.Model):
    nome_social = models.CharField(max_length=255)
    cpf = models.CharField(max_length=11, unique=True)
    data_nascimento = models.DateField(null=True)
    ativo = models.BooleanField(default=True)
```

#### Departamento
```python
class Departamento(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    
    # Relacionamento com fluxo personalizado
    fluxo = models.OneToOneField(FluxoAtendimento, null=True, ...)
```

---

## 3. Exemplos de Fluxos por Departamento

### 3.1. Departamento Comercial
```
1. 📥 Solicitação de Orçamento (Fila)
2. 📞 Em Contato (Trabalho)
3. 💳 Aguardando Pagamento (Espera)
4. 📋 Pedido Confirmado (Trabalho)
5. ✅ Concluído (Finalização)
6. ❌ Perdido (Finalização)
```

**Campos Específicos:**
- `valor_orcamento`: Valor do orçamento
- `moeda`: BRL/USD/EUR
- `produto_servico`: Produto/serviço principal
- `categoria_venda`: Produto/Serviço/Assinatura

### 3.2. Departamento Financeiro
```
1. 📝 Nova Solicitação (Fila)
2. 🔍 Análise de Crédito (Trabalho)
3. 📧 Aguardando Documentos (Espera)
4. ⚡ Processando Pagamento (Trabalho)
5. ✅ Pagamento Confirmado (Finalização)
6. ❌ Cancelado (Finalização)
```

**Campos Específicos:**
- `tipo_transacao`: Pagamento/Estorno/Reembolso
- `valor_transacao`: Valor da transação
- `metodo_pagamento`: Cartão/Boleto/Pix
- `status_financeiro`: Processado/Pendente/Falha

### 3.3. Departamento Suporte Técnico
```
1. 🆕 Novo Chamado (Fila)
2. 🔬 Diagnóstico (Trabalho)
3. 🛠️ Em Reparo (Trabalho)
4. ⏳ Aguardando Peças (Espera)
5. 🧪 Testes (Trabalho)
6. ✅ Resolvido (Finalização)
7. 🔄 Escalado (Fila - Nível 2)
```

**Campos Específicos:**
- `categoria_problema`: Hardware/Software/Rede
- `nivel_severidade`: Baixo/Médio/Alto/Crítico
- `equipamento_afetado`: Descrição do equipamento
- `tempo_resposta_sla`: SLA em minutos

### 3.4. Departamento Chatbot
```
1. 🤖 Atendimento Ativo (Trabalho)
2. ✅ Resolvido (Bot) (Finalização)
3. ↪️ Transferido (Finalização)
```

**Funcionalidades:**
- Análise de intenção em tempo real
- Mapeamento intenção → departamento
- Transferência automática baseada em regras

---

## 4. Lógica de Negócio

### 4.1. Transferência: Chatbot para Departamento

#### Fluxo de Triagem
1. **Análise de Intenção**: Chatbot analisa mensagens para identificar intenção principal
   - Exemplo: "não consigo pagar minha fatura" → `PAGAMENTOS_ERRO`
   
2. **Mapeamento de Intenção**: Configuração que mapeia intenções para departamentos
   ```
   PAGAMENTOS_ERRO → Departamento "Financeiro"
   PRODUTO_DUVIDA → Departamento "Vendas"
   SUPORTE_TECNICO → Departamento "Suporte"
   ```

3. **Decisão de Transferência**: Bot inicia transferência quando:
   - Solicitação ultrapassa capacidade de resolução
   - Intenção claramente pertence a time humano
   - Cliente solicita explicitamente "falar com humano"

4. **Execução da Transferência**:
   - Status alterado para etapa inicial do departamento destino
   - `atendimento.departamento` preenchido
   - `atendimento.atendente_humano` permanece `NULL`
   - Notificação via WebSocket para painel do departamento
   - Mensagem de confirmação ao cliente

### 4.2. Atribuição Manual: Controle pelo Atendente

#### Abordagem Simplificada

A atribuição de atendimentos é feita manualmente pelos próprios atendentes através de ações intuitivas no painel Kanban, eliminando complexidade desnecessária do sistema.

#### Fluxo de Atribuição Manual

1. **Visualização da Fila**:
   - Todos os atendentes do departamento visualizam cards na etapa tipo `FILA`
   - Cards exibem informações essenciais: cliente, assunto, tempo de espera, tags
   - Atendentes podem avaliar qual caso assumir baseado em especialidade/carga atual

2. **Atribuição por Movimentação**:
   - Atendente arrasta card da `FILA` para primeira etapa de `TRABALHO`
   - Sistema **automaticamente atribui** o atendimento ao atendente que realizou a ação
   - Atendimento passa a ser visível apenas para o atendente atribuído

3. **Movimentação Interna**:
   - Atendentes movem cards entre etapas de `TRABALHO` e `ESPERA`
   - Atribuição é mantida durante todo o ciclo de trabalho
   - Sistema registra cada movimento no histórico

4. **Devolução para Fila**:
   - Atendente pode devolver caso para a `FILA` se necessário
   - Sistema **automaticamente remove** a atribuição
   - Atendimento fica disponível para outros atendentes assumirem

#### Regras de Permissão por Tipo de Etapa

```python
if etapa.tipo_etapa == TipoEtapa.FILA:
    # Todos os atendentes do departamento podem ver e mover
    # Ao mover para TRABABALHO → atribuir ao atendente que moveu
    
elif etapa.tipo_etapa == TipoEtapa.TRABALHO:
    # Apenas o atendente atribuído pode ver e mover
    # Mantém atribuição durante todo o ciclo
    
elif etapa.tipo_etapa == TipoEtapa.ESPERA:
    # Apenas o atendente atribuído pode ver e mover
    # Não conta contra produtividade (aguardando ação externa)
    
elif etapa.tipo_etapa == TipoEtapa.FINALIZACAO:
    # Apenas atendente atribuído pode finalizar
    # Gera métricas finais do atendimento
```

#### Benefícios da Atribuição Manual

**Para os Atendentes:**
- **Controle Real**: Escolhem casos baseados em especialidade e interesse
- **Flexibilidade**: Podem negociar entre si quem assume cada caso
- **Autonomia**: Sem atribuições "forçadas" pelo sistema
- **Especialização**: Casos complexos naturalmente vão para especialistas

**Para o Negócio:**
- **Simplicidade**: Código mais simples e fácil de manter
- **Produtividade**: Atendentes focam nos casos que dominam
- **Escalabilidade**: Novos atendentes entram no fluxo naturalmente
- **Clima Organizacional**: Menos conflitos sobre atribuição

### 4.3. Transferência: Humano para Humano

#### Fluxo de Transferência
1. **Gatilho**: Atendente clica "Transferir" no card
2. **Seleção de Destino** (Modal UI):
   - Departamento: Move para fila do novo departamento
   - Atendente Específico: Atribuição direta se disponível
3. **Execução**:
   - Registrar nota interna da transferência
   - Desvincular atendente atual
   - Atualizar departamento se necessário
   - Status volta para etapa de fila
4. **Notificações**:
   - Atendimento aparece no kanban do novo departamento
   - Sistema dispara atribuição automática se necessário

---

## 5. Interface do Usuário - Kanban

### 5.1. Estrutura do Painel

#### Componente Principal: PainelKanban
- Recebe `departamentoId` como parâmetro
- Renderiza colunas dinamicamente baseadas em `EtapaFluxo`
- Conecta via WebSocket para atualizações em tempo real
- Implementa drag-and-drop entre etapas

#### Componente CardAtendimento
Informações exibidas:
- Nome do Cliente
- Protocolo/ID do Atendimento
- Assunto/Última Mensagem
- Tempo na etapa atual
- Tags de prioridade/assunto
- Atendente atual (quando aplicável)
- Indicador visual da etapa (cor)

### 5.2. Permissões de Visualização

#### Para Atendentes
- **Etapas FILA**: Visíveis para todos (podem assumir)
- **Etapas TRABALHO**: Apenas seus próprios atendimentos
- **Etapas ESPERA**: Seus atendimentos + visão gerencial
- **Etapas FINALIZAÇÃO**: Apenas movimentação para arquivamento

#### Para Gestores
- Visão completa de todos os atendimentos do departamento
- Filtros por atendente, prioridade, tempo, tags
- Acesso a métricas e relatórios

### 5.3. Funcionalidades Interativas

#### Drag-and-Drop
- Movimentação visual entre colunas
- Validação de regras antes do movimento
- Atualização em tempo real via WebSocket

#### Modal de Transferência
- Seleção de departamento ou atendente específico
- Campo para nota interna obrigatória
- Preview do impacto da transferência

#### Sistema de Filtros Avançados
```javascript
// Exemplo de filtros disponíveis
{
  prioridade: ["Alta", "Média"],
  tempo_na_etapa: { min: 30, max: 120 }, // minutos
  tags: ["Urgente", "VIP"],
  atendente: "João Silva",
  valor_orcamento: { min: 1000, max: 5000 }
}
```

---

## 6. Serviços e API

### 6.1. Serviço Principal: FluxoAtendimentoService

```python
class FluxoAtendimentoService:
    """Gerencia operações com fluxos de atendimento."""
    
    @staticmethod
    def mover_atendimento(
        atendimento: Atendimento,
        etapa_destino: EtapaFluxo,
        atendente_movendo: AtendenteHumano,
        motivo: Optional[str] = None
    ) -> MovimentoFluxo:
        """Move atendimento para nova etapa com atribuição automática simplificada."""
        etapa_origem = atendimento.etapa_atual
        
        # Atribuição simplifica: só ao mover de FILA para TRABALHO
        if etapa_origem.tipo_etapa == TipoEtapa.FILA and etapa_destino.tipo_etapa == TipoEtapa.TRABALHO:
            atendimento.atendente_humano = atendente_movendo
        elif etapa_destino.tipo_etapa == TipoEtapa.FILA:
            # Remove atribuição ao voltar para fila
            atendimento.atendente_humano = None
        # Para outros movimentos, mantém atribuição atual
        
        atendimento.etapa_atual = etapa_destino
        atendimento.save()
        
        # Criar registro de movimento
        return MovimentoFluxo.objects.create(
            atendimento=atendimento,
            etapa_origem=etapa_origem,
            etapa_destino=etapa_destino,
            atendente=atendente_movendo,
            motivo=motivo or f"Movido de {etapa_origem.nome} para {etapa_destino.nome}"
        )
        
    @staticmethod
    def validar_movimentacao(
        atendimento: Atendimento,
        etapa_destino: EtapaFluxo,
        atendente: AtendenteHumano
    ) -> Tuple[bool, List[str]]:
        """Valida se movimento é permitido segundo regras do tipo de etapa."""
        erros = []
        
        # Regras por tipo de etapa
        if atendimento.etapa_atual.tipo_etapa == TipoEtapa.FILA:
            # Todos podem mover da fila
            pass
        elif atendimento.etapa_atual.tipo_etapa in [TipoEtapa.TRABALHO, TipoEtapa.ESPERA]:
            # Apenas atendente atribuído pode mover
            if atendimento.atendente_humano != atendente:
                erros.append("Apenas o atendente atribuído pode mover este atendimento")
        
        # Validação de etapa destino
        if etapa_destino.tipo_etapa == TipoEtapa.FINALIZACAO:
            # Verificar campos obrigatórios antes de finalizar
            if not atendimento.resolucao:
                erros.append("Resolução é obrigatória para finalizar atendimento")
                
        return len(erros) == 0, erros
```

### 6.2. Serviço do Kanban

```python
class KanbanService:
    """Alimenta o frontend com dados do painel Kanban."""
    
    @staticmethod
    def get_dados_kanban(
        departamento: Departamento,
        atendente: Optional[AtendenteHumano] = None,
        filtros: Optional[Dict] = None
    ) -> Dict:
        """Retorna dados estruturados para o Kanban com controle de visão por atendente."""
        fluxo = departamento.fluxo
        etapas = fluxo.etapas.all().order_by('ordem')
        
        dados = {"etapas": []}
        
        for etapa in etapas:
            atendimentos = fluxo.get_atendimentos_por_etapa(etapa, atendente)
            
            # Aplicar filtros se fornecidos
            if filtros:
                atendimentos = aplicar_filtros_dinamicos(atendimentos, filtros)
            
            dados["etapas"].append({
                "id": etapa.id,
                "nome": etapa.nome,
                "tipo": etapa.tipo_etapa,
                "cor": etapa.cor,
                "ordem": etapa.ordem,
                "permite_atribuicao": etapa.permite_atribuicao,
                "atendimentos": [
                    {
                        "id": str(att.id),
                        "cliente_nome": att.cliente.nome_social,
                        "protocolo": str(att.id)[:8],
                        "assunto": att.get_ultima_mensagem()[:100],
                        "tempo_na_etapa": calcular_tempo_etapa(att),
                        "atendente": att.atendente_humano.nome_completo if att.atendente_humano else None,
                        "prioridade": att.prioridade,
                        "tags": att.tags
                    }
                    for att in atendimentos
                ]
            })
            
        return dados
        
    @staticmethod
    def get_atendimentos_por_etapa(
        etapa: EtapaFluxo,
        atendente: Optional[AtendenteHumano] = None
    ) -> QuerySet[Atendimento]:
        """Retorna atendimentos em uma etapa específica com controle de visão."""
        queryset = Atendimento.objects.filter(
            etapa_atual=etapa,
            ativo=True
        ).select_related('cliente', 'atendente_humano')
        
        # Controle de visão por tipo de etapa
        if etapa.tipo_etapa == TipoEtapa.FILA:
            # Todos os atendentes do departamento podem ver
            pass
        elif etapa.tipo_etapa in [TipoEtapa.TRABALHO, TipoEtapa.ESPERA]:
            # Apenas atendente atribuído pode ver (exceto gestores)
            if atendente and not atendente.user.is_superuser:
                queryset = queryset.filter(atendente_humano=atendente)
                
        return queryset
        
    @staticmethod
    def aplicar_filtros_dinamicos(
        queryset: QuerySet,
        filtros: Dict
    ) -> QuerySet:
        """Aplica filtros baseados no departamento e campos dinâmicos."""
        if filtros.get('prioridade'):
            queryset = queryset.filter(prioridade__in=filtros['prioridade'])
            
        if filtros.get('atendente_id'):
            queryset = queryset.filter(atendente_humano_id=filtros['atendente_id'])
            
        if filtros.get('tempo_minimo'):
            # Lógica para filtrar por tempo mínimo na etapa
            pass
            
        if filtros.get('tags'):
            queryset = queryset.filter(tags__overlap=filtros['tags'])
            
        return queryset
```

### 6.3. Endpoints da API

#### Endpoint Principal do Kanban
```
GET /api/departamentos/{id}/kanban/
Response:
{
  "etapas": [
    {
      "id": 1,
      "nome": "Fila de Entrada",
      "tipo": "fila",
      "cor": "#6B7280",
      "atendimentos": [...]
    }
  ]
}
```

#### Movimentação de Atendimento (Atribuição Automática)
```
POST /api/atendimentos/{id}/mover/
Body:
{
  "etapa_destino_id": 5,
  "motivo": "Cliente confirmou interesse"
}
# Sistema automaticamente atribui ao atendente que moveu se for de FILA para TRABALHO
```

#### Transferência entre Departamentos
```
POST /api/atendimentos/{id}/transferir/
Body:
{
  "tipo": "departamento", // ou "atendente"
  "destino_id": 3,
  "nota_interna": "Caso complexo, necessita especialista"
}
# Remove atribuição atual e move para fila do novo destino
```

---

## 7. Comunicação em Tempo Real

### 7.1. Configuração WebSocket (Django Channels)

#### Consumer Principal
```python
class KanbanConsumer(AsyncWebsocketConsumer):
    """Gerencia conexões WebSocket do painel Kanban."""
    
    async def connect(self):
        """Conecta ao grupo do departamento."""
        self.departamento_id = self.scope["url_route"]["kwargs"]["departamento_id"]
        self.group_name = f"kanban_{self.departamento_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
    async def atendimento_atualizado(self, event):
        """Recebe atualizações de atendimento."""
        await self.send(text_data=json.dumps({
            "type": "ATENDIMENTO_ATUALIZADO",
            "data": event["data"]
        }))
```

#### Integração com Signals
```python
@receiver(post_save, sender=Atendimento)
def notificar_atualizacao_atendimento(sender, instance, created, **kwargs):
    """Dispara notificação WebSocket após alteração."""
    if instance.departamento:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"kanban_{instance.departamento.id}",
            {
                "type": "atendimento.atualizado",
                "data": serialize_atendimento(instance)
            }
        )
```

### 7.2. Eventos em Tempo Real

#### Tipos de Eventos
- `ATENDIMENTO_CRIADO`: Novo atendimento na fila
- `ATENDIMENTO_ATUALIZADO`: Mudança de etapa/atendente
- `ATENDIMENTO_TRANSFERIDO`: Movimento entre departamentos
- `ATENDENTE_DISPONIVEL`: Atendente mudou status
- `NOVA_MENSAGEM`: Mensagem recebida/enviada

#### Estrutura do Evento
```json
{
  "type": "ATENDIMENTO_ATUALIZADO",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "id": "uuid",
    "etapa_anterior": { "id": 1, "nome": "Fila" },
    "etapa_atual": { "id": 2, "nome": "Em Trabalho" },
    "atendente": { "id": 5, "nome": "João Silva" },
    "motivo": "Cliente confirmou pedido"
  }
}
```

---

## 8. Notificações e SLA

### 8.1. Sistema de Notificações

O sistema foca em notificações informativas e alertas de SLA para acompanhar o fluxo manual dos atendimentos.

#### Tipos de Notificações
```python
class NotificacaoService:
    """Gerencia notificações do sistema de atendimento."""
    
    @staticmethod
    def enviar_notificacao_movimento(movimento: MovimentoFluxo) -> None:
        """Envia notificações baseadas em movimentos manuais."""
        if movimento.etapa_destino.tipo_etapa == TipoEtapa.FILA:
            # Notificar todos os atendentes do departamento sobre novo caso na fila
            enviar_notificacao_grupo(
                grupo=f"departamento_{movimento.atendimento.departamento.id}",
                mensagem=f"Novo caso na fila: {movimento.atendimento.cliente.nome_social}",
                tipo="nova_fila"
            )
            
    @staticmethod
    def verificar_alertas_sla() -> None:
        """Verifica violações de SLA e envia alertas."""
        violacoes = SLAService.verificar_violacoes_sla()
        for violacao in violacoes:
            enviar_notificacao_usuario(
                usuario=violacao['atendimento'].atendente_humano.user,
                mensagem=f"SLA violado: {violacao['atendimento'].cliente.nome_social}",
                tipo="sla_violado"
            )
```

#### Configuração de Notificações (JSON)
```json
{
  "notificacoes": {
    "nova_fila": {
      "destino": ["todos_atendentes"],
      "canais": ["websocket", "email"]
    },
    "atribuido": {
      "destino": ["atendente"],
      "canais": ["websocket", "push"]
    },
    "transferencia": {
      "destino": ["departamento_destino", "atendente_origem"],
      "canais": ["websocket"]
    },
    "sla_violado": {
      "destino": ["atendente", "gestor"],
      "canais": ["websocket", "email"]
    },
    "nova_mensagem": {
      "destino": ["atendente"],
      "canais": ["websocket"]
    }
  }
}
```

### 8.2. SLA e Métricas

#### Cálculo de SLA por Etapa
```python
class SLAService:
    """Gerencia cálculos de SLA e métricas com foco na abordagem manual."""
    
    @staticmethod
    def calcular_tempo_etapa(atendimento: Atendimento) -> int:
        """Calcula tempo em segundos na etapa atual."""
        try:
            ultimo_movimento = atendimento.movimentofluxo_set.latest('data_movimento')
            return int((timezone.now() - ultimo_movimento.data_movimento).total_seconds())
        except MovimentoFluxo.DoesNotExist:
            return int((timezone.now() - atendimento.data_inicio).total_seconds())
        
    @staticmethod
    def calcular_tempo_em_fila(atendimento: Atendimento) -> int:
        """Calcula tempo em segundos na fila antes da atribuição."""
        # Encontra o primeiro movimento de atribuição
        movimentos = atendimento.movimentofluxo_set.all().order_by('data_movimento')
        for movimento in movimentos:
            if movimento.etapa_destino.tipo_etapa == TipoEtapa.TRABALHO:
                return int((movimento.data_movimento - atendimento.data_inicio).total_seconds())
        return 0
        
    @staticmethod
    def verificar_violacoes_sla(departamento: Departamento) -> List[Dict]:
        """Identifica atendimentos que violaram SLA."""
        violacoes = []
        for atendimento in departamento.atendimentos.filter(ativo=True):
            tempo_na_etapa = SLAService.calcular_tempo_etapa(atendimento)
            etapa = atendimento.etapa_atual
            
            # SLA para etapa atual
            sla = etapa.regras_transicao.get("sla_minutos")
            if sla and tempo_na_etapa > sla * 60:
                violacoes.append({
                    "atendimento": atendimento,
                    "etapa": etapa,
                    "tempo_excedido": tempo_na_etapa - sla * 60,
                    "tipo": "etapa_atual"
                })
                
            # SLA específico para fila (tempo de espera)
            if etapa.tipo_etapa == TipoEtapa.FILA:
                sla_fila = etapa.regras_transicao.get("sla_fila_minutos", 30)
                if tempo_na_etapa > sla_fila * 60:
                    violacoes.append({
                        "atendimento": atendimento,
                        "etapa": etapa,
                        "tempo_excedido": tempo_na_etapa - sla_fila * 60,
                        "tipo": "fila"
                    })
                    
        return violacoes
        
    @staticmethod
    def gerar_metricas_atendente(atendente: AtendenteHumano, periodo_dias: int = 30) -> Dict:
        """Gera métricas de produtividade para um atendente."""
        data_inicio = timezone.now() - timedelta(days=periodo_dias)
        
        atendimentos = Atendimento.objects.filter(
            atendente_humano=atendente,
            data_inicio__gte=data_inicio
        ).prefetch_related('movimentofluxo_set')
        
        metricas = {
            "atendimentos_assumidos": 0,
            "atendimentos_concluidos": 0,
            "tempo_medio_atendimento": 0,
            "tempo_medio_em_fila": 0,
            "taxa_devolucao": 0
        }
        
        for att in atendimentos:
            # Primeiro movimento de atribuição
            primeira_atribuicao = att.movimentofluxo_set.filter(
                etapa_destino__tipo_etapa=TipoEtapa.TRABALHO
            ).first()
            
            if primeira_atribuicao:
                metricas["atendimentos_assumidos"] += 1
                
                # Tempo em fila antes da atribuição
                tempo_fila = (primeira_atribuicao.data_movimento - att.data_inicio).total_seconds()
                metricas["tempo_medio_em_fila"] += tempo_fila
                
            # Verificar se foi concluído
            if att.etapa_atual.tipo_etapa == TipoEtapa.FINALIZACAO:
                metricas["atendimentos_concluidos"] += 1
                
                # Tempo total de atendimento
                tempo_total = 0
                for movimento in att.movimentofluxo_set.all():
                    if movimento.etapa_destino.tipo_etapa in [TipoEtapa.TRABALHO, TipoEtapa.ESPERA]:
                        tempo_total += movimento.duracao_segundos or 0
                metricas["tempo_medio_atendimento"] += tempo_total
                
        # Calcular médias
        if metricas["atendimentos_assumidos"] > 0:
            metricas["tempo_medio_em_fila"] /= metricas["atendimentos_assumidos"]
        if metricas["atendimentos_concluidos"] > 0:
            metricas["tempo_medio_atendimento"] /= metricas["atendimentos_concluidos"]
            
        # Taxa de devolução
        devolucoes = atendimentos.filter(etapa_atual__tipo_etapa=TipoEtapa.FILA).count()
        metricas["taxa_devolucao"] = (devolucoes / metricas["atendimentos_assumidos"] * 100) if metricas["atendimentos_assumidos"] > 0 else 0
        
        return metricas
```

---

## 9. Roadmap de Implementação

### Fase 1: Estrutura Base (Semanas 1-2)
- [x] Modelagem de dados completa
- [ ] Migrations preservando dados existentes
- [ ] Serviços básicos de movimentação
- [ ] Interface administrativa para fluxos
- [ ] Setup do ambiente de desenvolvimento

### Fase 2: Backend Core (Semanas 3-4)
- [ ] Implementar `FluxoAtendimentoService`
- [ ] Desenvolver APIs RESTful
- [ ] Configurar Django Channels
- [ ] Implementar signals e notificações
- [ ] Criar testes unitários (80% coverage)

### Fase 3: Frontend Kanban (Semanas 5-6)
- [ ] Componente kanban dinâmico
- [ ] Integração com backend
- [ ] Sistema de filtros e buscas
- [ ] Update em tempo real via WebSocket
- [ ] Interface de transferência

### Fase 4: Automações e Métricas (Semanas 7-8)
#### Notificações e Métricas
- [ ] Sistema de notificações por movimento
- [ ] Alertas de violação de SLA
- [ ] Dashboard analítico com métricas de atendentes
- [ ] Relatórios de produtividade individual
- [ ] Métricas de tempo em fila vs tempo de atendimento

### Fase 5: Otimização (Semanas 9-10)
- [ ] Performance e cache
- [ ] Testes de carga e estresse
- [ ] Documentação completa
- [ ] Treinamento de usuários
- [ ] Deploy em produção

---

## 10. Checklist de Desenvolvimento

### 10.1. Backend

#### Models e Migrations
- [ ] Implementar `FluxoAtendimento`
- [ ] Implementar `EtapaFluxo` com `TipoEtapa`
- [ ] Implementar `MovimentoFluxo`
- [ ] Atualizar `Atendimento` com `etapa_atual`
- [ ] Atualizar `AtendenteHumano` com `data_ultima_atribuicao`
- [ ] Criar migration preservando dados existentes

#### Services
- [ ] `FluxoAtendimentoService.mover_atendimento()` (com atribuição automática ao mover de FILA para TRABALHO)
- [ ] `FluxoAtendimentoService.validar_movimentacao()` (regras por tipo de etapa)
- [ ] `KanbanService.get_dados_kanban()` (com controle de visão por atendente)
- [ ] `KanbanService.get_atendimentos_por_etapa()` (filtro por tipo de etapa)
- [ ] `KanbanService.aplicar_filtros_dinamicos()` (filtros específicos por departamento)
- [ ] `NotificacaoService.enviar_notificacao_movimento()` (notificações por movimento)
- [ ] `SLAService.calcular_tempo_etapa()` (cálculo de tempo em etapa)
- [ ] `SLAService.verificar_violacoes_sla()` (alertas de SLA)
- [ ] `SLAService.gerar_metricas_atendente()` (métricas de produtividade)

#### APIs
- [ ] `KanbanView.get()` - Dados do painel
- [ ] `MoverAtendimentoView.post()` - Movimentação
- [ ] `MoverAtendimentoView.post()` - Movimentação com atribuição automática simplificada
- [ ] `TransferirAtendimentoView.post()` - Transferência
- [ ] `FluxoViewSet` - CRUD de fluxos
- [ ] `EtapaViewSet` - CRUD de etapas

#### WebSocket
- [ ] `KanbanConsumer.connect()`
- [ ] `KanbanConsumer.disconnect()`
- [ ] `KanbanConsumer.atendimento_atualizado()`
- [ ] Signal handler para `post_save` do `Atendimento`
- [ ] Signal handler para `post_save` do `MovimentoFluxo`

### 10.2. Frontend

#### Componentes React/Vue
- [ ] `KanbanBoard` - Painel principal
- [ ] `KanbanColumn` - Coluna do kanban
- [ ] `AtendimentoCard` - Card de atendimento
- [ ] `TransferModal` - Modal de transferência
- [ ] `FilterPanel` - Painel de filtros
- [ ] `MetricsDashboard` - Dashboard métrico

#### Funcionalidades
- [ ] Drag-and-drop entre colunas
- [ ] Filtros dinâmicos por departamento
- [ ] Conexão WebSocket para updates
- [ ] Notificações em tempo real
- [ ] Responsividade mobile

### 10.3. Testes

#### Backend Tests
- [ ] Unit tests para models (95% coverage)
- [ ] Unit tests para services (90% coverage)
- [ ] Integration tests para APIs
- [ ] Tests para WebSocket consumers
- [ ] Tests para automações

#### Frontend Tests
- [ ] Component tests para Kanban (incluindo drag-and-drop)
- [ ] Integration tests para APIs (com regras de permissão)
- [ ] E2E tests para fluxo manual completo (fila → trabalho → conclusão)
- [ ] Performance tests para grandes volumes de atendimentos
- [ ] Tests de notificações em tempo real

---

## 11. Métricas de Sucesso

### 11.1. Indicadores Operacionais (KPIs)

#### Tempo e Eficiência
- **Tempo Médio em Fila**: Redução de 40% (atendimento assume casos mais rápidos)
- **Tempo Médio por Etapa**: Redução de 20%
- **Tempo Total de Atendimento**: Redução de 25%
- **Taxa de Primeira Resposta**: Melhoria 30%
- **SLA Compliance**: Aumentar para 95%

#### Produtividade
- **Atendimentos por Hora**: Aumento 15%
- **Taxa de Transferência**: Redução 10%
- **Taxa de Resolução no Primeiro Contato**: Aumentar 40%
- **Ocupação de Atendentes**: Otimizar para 75-85%

### 11.2. Indicadores de Qualidade

#### Satisfação
- **NPS dos Clientes**: Aumentar 20 pontos
- **Satisfação dos Atendentes**: Aumentar 30%
- **Taxa de Retorno**: Redução 15%
- **Qualidade das Respostas**: Melhoria 25%

#### Adoção
- **Taxa de Adoção da Ferramenta**: 95% em 2 meses (interface mais intuitiva)
- **Frequência de Uso Diária**: 98% dos atendentes
- **Redução de Erros**: Diminuição 60% (sem complexidade de atribuição automática)
- **Tempo de Treinamento**: Redução 70% (fluxo mais simples)
- **Satisfação dos Atendentes**: Aumentar 40% (mais controle e autonomia)

### 11.3. Métricas Técnicas

#### Performance
- **Tempo de Carregamento**: < 2 segundos
- **Latência WebSocket**: < 100ms
- **Uptime**: 99.9%
- **Queries por Segundo**: Suportar 1000+

#### Escalabilidade
- **Atendimentos Simultâneos**: 1000+
- **Departamentos Ativos**: 50+
- **Atendentes Conectados**: 500+
- **Mensagens por Dia**: 100.000+

---

## 12. Considerações Técnicas

### 12.1. Performance

#### Otimizações de Banco
- Índices em campos frequentemente filtrados
- Query optimization com `select_related` e `prefetch_related`
- Partitioning para tabelas grandes (atendimentos, movimentos)
- Cache Redis para consultas frequentes

#### Cache Strategy
```python
# Cache para dados do kanban (5 minutos)
@cache_page(300)
def kanban_view(request, departamento_id):
    pass

# Cache para configurações de fluxo (1 hora)
@cache_page(3600)
def fluxo_config_view(request, departamento_id):
    pass
```

### 12.2. Segurança

#### Permissões
- Role-based access control (RBAC)
- Validação de permissões por movimentação
- Audit trail completo de todas as ações
- Rate limiting para APIs

#### Validações
- Sanitização de dados de entrada
- Validação de regras de negócio
- Verificação de CSRF em todas as requisições
- Encrypted passwords e tokens

### 12.3. Monitoramento

#### Logs Estruturados
```python
logger.info(
    "Atendimento movido",
    extra={
        "atendimento_id": str(atendimento.id),
        "etapa_origem": etapa_origem.id,
        "etapa_destino": etapa_destino.id,
        "atendente_id": atendente.id if atendente else None,
        "tempo_movimento": tempo_seconds,
        "user_id": request.user.id
    }
)
```

#### Alertas
- Monitoramento de performance em tempo real
- Alertas sobre violações de SLA
- Notificações sobre erros críticos
- Dashboard de saúde do sistema

### 12.4. Backup e Recuperação

#### Estratégia de Backup
- Daily backups do PostgreSQL
- Incremental backups para logs
- Backup configurações de Redis
- Retention policy de 90 dias

#### Recovery Plan
- RTO (Recovery Time Objective): 4 horas
- RPO (Recovery Point Objective): 15 minutos
- Testes mensais de disaster recovery
- Documentation atualizada

---

## 13. Próximos Passos Imediatos

### 13.1. Setup do Projeto

1. **Criar Branch Feature**
   ```bash
   git checkout -b feature/fluxos-personalizados-central-atendimento
   ```

2. **Setup Ambiente Dev**
   ```bash
   uv sync --dev
   uv run task migrate
   uv run task createsuperuser
   ```

3. **Configurar Testes**
   ```bash
   uv run task test-docker
   ```

### 13.2. Implementação Inicial

1. **Modelos e Migrations**
   - Implementar novos models
   - Criar migration inicial
   - Testar com dados de exemplo

2. **Services Básicos**
   - Implementar `FluxoAtendimentoService`
   - Criar lógica de movimentação
   - Adicionar validações

3. **APIs Fundamentais**
   - Endpoint para dados do kanban
   - Endpoint para movimentação
   - Testes de integração

### 13.3. Validação

1. **Testes Unitários**
   - Coverage mínimo 80%
   - Testes para todos os services
   - Testes para models

2. **Testes de Integração**
   - Testes para APIs
   - Testes para WebSocket
   - Testes end-to-end

3. **Review de Código**
   - Code review por peer
   - Verificação de padrões
   - Validação de segurança

---

## 14. Conclusão

A implementação de fluxos personalizados na Central de Atendimento representa uma transformação significativa na capacidade do sistema de atender às necessidades específicas de cada departamento. Esta arquitetura flexível permitirá:

### 14.1. Benefícios Principais

- **Flexibilidade Total**: Cada departamento otimiza seu próprio processo
- **Evolução Contínua**: Fluxos ajustáveis sem impacto no sistema
- **Métricas Precisas**: Análise detalhada do tempo em cada etapa
- **Experiência Otimizada**: Atendentes trabalham com processos familiares
- **Escalabilidade**: Novos departamentos adicionados facilmente

### 14.2. Impacto Esperado

Com esta implementação, a Central de Atendimento se tornará uma ferramenta verdadeiramente adaptável aos processos de negócio, em vez de forçar os processos a se adaptarem às limitações tecnológicas. O sistema evoluirá de um modelo rígido para uma plataforma dinâmica que cresce com a organização.

### 14.3. Próxima Fase

Com o planejamento completo e a arquitetura definida, a equipe de desenvolvimento está pronta para iniciar a implementação seguindo o roadmap estabelecido. O sucesso desta iniciativa dependerá da execução disciplinada do plano, da comunicação constante com os stakeholders e da adaptação contínua baseada no feedback dos usuários.

---

## 🔄 **Resumo do Sistema de Atendimento**

### ✅ **Funcionamento da Atribuição**
- **Sistema**: Atribuição manual controlada pelo atendente
- **Característica**: Código simplificado, manutenibilidade otimizada, controle total nas mãos dos usuários

### ✅ **Fluxo Operacional**
1. **Novo atendimento** entra na etapa `FILA` (visível para todos)
2. **Atendente assume caso** ao mover da `FILA` para primeira etapa `TRABALHO`
3. **Sistema atribui automaticamente** ao atendente que realizou a ação
4. **Movimento interno** mantém atribuição (TRABALHO ↔ ESPERA)
5. **Retorno para FILA** remove atribuição (disponível para outros)

### ✅ **Regras por Tipo de Etapa**
- **FILA**: Todos podem ver/mover
- **TRABALHO/ESPERA**: Apenas atendente atribuído pode ver/mover
- **FINALIZAÇÃO**: Apenas atendente atribuído pode finalizar

### ✅ **Métricas Disponíveis**
- **Tempo em Fila**: Período antes da atribuição
- **Produtividade Individual**: Casos assumidos vs concluídos
- **Taxa de Devolução**: Frequência de retorno para fila
- **Tempo de Atendimento**: Desde atribuição até conclusão

### ✅ **Características do Sistema**
- **Implementação**: Desenvolvimento focado e direto
- **Manutenção**: Simplificada com regras claras
- **Interface**: Intuitiva e controlada pelo usuário
- **Autonomia**: Total controle nas mãos dos atendentes

---
**Status Documento**: ✅ Completo e Consolidado  
**Prioridade**: Alta  
**Complexidade**: Média (simplificada)  
**Impacto Esperado**: Transformacional  
**Risco**: Baixo (com planejamento adequado)

