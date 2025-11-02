# Planejamento de Utilização e Interface (UI/UX) - Painel Kanban com Fluxos Personalizados

Este documento descreve a visão e o funcionamento do painel da central de atendimento, que será estruturado no formato de um quadro Kanban com **fluxos totalmente personalizáveis por departamento**, proporcionando uma experiência de usuário intuitiva, visual e eficiente para os atendentes e gestores.

## 1. Arquitetura de Fluxos Personalizados

### 1.1. Conceitos Fundamentais

A nova arquitetura substitui o `StatusAtendimento` fixo por um sistema dinâmico onde cada departamento pode definir seu próprio fluxo de trabalho:

- **FluxoAtendimento:** Define o conjunto de etapas para um departamento
- **EtapaFluxo:** Representa cada coluna/status no kanban de um departamento
- **MovimentoFluxo:** Registra a transição de um atendimento entre etapas

### 1.2. Modelos de Dados

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
    """Representa uma etapa/coluna no fluxo kanban de um departamento."""
    fluxo = models.ForeignKey(FluxoAtendimento, related_name="etapas", ...)
    nome = models.CharField(max_length=50)
    descricao = models.CharField(max_length=200, blank=True)
    ordem = models.PositiveIntegerField()
    cor = models.CharField(max_length=7, default="#6B7280")  # Hex color
    tipo_etapa = models.CharField(
        max_length=20,
        choices=TipoEtapa.choices,
        default=TipoEtapa.TRABALHO
    )
    permite_atribuicao = models.BooleanField(default=True)
    automatico = models.BooleanField(default=False)
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

## 2. Exemplos de Fluxos por Departamento

### 2.1. Departamento Comercial
```
1. 📥 Solicitação de Orçamento (Fila)
2. 📞 Em Contato (Trabalho)
3. 💳 Aguardando Pagamento (Espera)
4. 📋 Pedido Confirmado (Trabalho)
5. ✅ Concluído (Finalização)
6. ❌ Perdido (Finalização)
```

### 2.2. Departamento Financeiro
```
1. 📝 Nova Solicitação (Fila)
2. 🔍 Análise de Crédito (Trabalho)
3. 📧 Aguardando Documentos (Espera)
4. ⚡ Processando Pagamento (Trabalho)
5. ✅ Pagamento Confirmado (Finalização)
6. ❌ Cancelado (Finalização)
```

### 2.3. Departamento Suporte Técnico
```
1. 🆕 Novo Chamado (Fila)
2. 🔬 Diagnóstico (Trabalho)
3. 🛠️ Em Reparo (Trabalho)
4. ⏳ Aguardando Peças (Espera)
5. 🧪 Testes (Trabalho)
6. ✅ Resolvido (Finalização)
7. 🔄 Escalado (Fila - Nível 2)
```

### 2.4. Departamento Chatbot
```
1. 🤖 Atendimento Ativo (Trabalho)
2. ✅ Resolvido (Bot) (Finalização)
3. ↪️ Transferido (Finalização - Indica transferência)
```

## 3. Visão Geral do Painel Kanban

O objetivo é centralizar o fluxo de trabalho em telas distintas e otimizadas para cada perfil, com **fluxos dinâmicos baseados no departamento**.

### 3.1. Painel Operacional (Departamentos Humanos)

Cada departamento terá seu próprio quadro com as etapas definidas em seu fluxo personalizado:

- **Estrutura Dinâmica:** As colunas do kanban são geradas automaticamente com base nas `EtapaFluxo` do departamento
- **Filtro por Atendente:** Cada atendente visualiza apenas os atendimentos atribuídos a ele (exceto etapas do tipo FILA)
- **Visão Gerencial:** Gestores podem ver todos os atendimentos do departamento ou filtrar por atendentes específicos

### 3.2. Painel de Monitoramento (Departamento do Chatbot)

Painel exclusivo para gestores acompanharem a performance do bot:

- **Atendimentos Ativos (Bot):** Etapa "🤖 Atendimento Ativo"
- **Finalizados (Bot):** Etapa "✅ Resolvido (Bot)"
- **Transferências:** Etapa "↪️ Transferido" (indica transferências para departamentos humanos)

## 4. Estrutura do Card de Atendimento

Cada card no quadro Kanban representará um único atendimento e exibirá informações essenciais:

- **Nome do Cliente:** Identificação clara do contato
- **Protocolo/ID do Atendimento:** Para referência rápida
- **Assunto/Última Mensagem:** Um trecho da última interação para dar contexto
- **Tempo na Etapa:** Há quanto tempo o atendimento está na etapa atual
- **Tags de Prioridade/Assunto:** Indicadores visuais (ex: "Urgente", "Vendas")
- **Atendente Atual:** Nome do atendente responsável (quando aplicável)
- **Indicador Visual:** Cor da etapa atual para fácil identificação

## 5. Fluxos de Utilização e Transição

### 5.1. Fluxo 1: Chatbot para Humano

1. **Início (Painel do Chatbot):**
   - Novo atendimento começa na etapa "🤖 Atendimento Ativo"
   - Bot processa a interação automaticamente

2. **Transferência pelo Bot:**
   - Bot identifica necessidade de transferência humana
   - Sistema move atendimento para etapa "↪️ Transferido"
   - Atendimento é atribuído ao departamento apropriado
   - Card entra na primeira etapa do fluxo do departamento destino (geralmente tipo FILA)

3. **Chegada (Painel Humano):**
   - Card aparece automaticamente na etapa de entrada do departamento
   - Atendentes disponíveis visualizam e podem assumir o atendimento

### 5.2. Fluxo 2: Atribuição e Atendimento Humano

1. **Atribuição de Atendimento:**
   - **Automática:** Sistema atribui ao atendente com menor carga
   - **Manual:** Atendente arrasta card da etapa FILA para uma etapa de TRABALHO
   - Sistema registra `atendente_humano` e movimento no histórico

2. **Interação e Progressão:**
   - Atendente move o card entre as etapas conforme processo
   - Cada movimento é registrado em `historico_movimentos`
   - Notificações podem ser configuradas para transições específicas

### 5.3. Fluxo 3: Transferência entre Departamentos

1. **Início da Transferência:**
   - Atendente clica em "Transferir" no card de atendimento
   - Sistema abre modal com opções de departamento e atendente

2. **Seleção de Destino:**
   - **Departamento:** Move para etapa inicial do fluxo do novo departamento
   - **Atendente Específico:** Move para primeira etapa de TRABALHO do atendente

3. **Execução da Transferência:**
   - Sistema remove atribuição do atendente atual
   - Atendimento é movido para novo departamento
   - Card aparece no kanban do novo departamento
   - Histórico completo é mantido

## 6. Regras de Negócio e Validações

### 6.1. Permissões de Movimentação

- **Etapas FILA:** Visíveis para todos os atendentes do departamento
- **Etapas TRABALHO:** Visíveis apenas para o atendente atribuído
- **Etapas ESPERA:** Visíveis para o atendente atribuído e gestores
- **Etapas FINALIZAÇÃO:** Apenas movimentação para arquivamento

### 6.2. Validações de Transição

- **Verificação de Atribuição:** Não permitir mover para etapa de trabalho sem atendente
- **Validação de Campos:** Exigir campos específicos em determinadas transições
- **Regras de SLA:** Alertar se tempo em etapa excede limite configurado
- **Verificação de Dependências:** Não permitir finalizar se etapas obrigatórias não foram concluídas

### 6.3. Automações Configuráveis

- **Movimento Automático:** Transferir automaticamente após X tempo em espera
- **Notificações:** Alertar atendentes sobre novos atendimentos em fila
- **Escalonamento:** Mover para etapa superior se não respondido em tempo hábil
- **Relatórios:** Gerar métricas por etapa e tempo de permanência

## 7. Interface do Administrador

### 7.1. Configuração de Fluxos

- **Editor Visual:** Interface drag-and-drop para criar/editar etapas
- **Configuração de Regras:** Definir condições e ações para cada etapa
- **Preview do Kanban:** Visualizar como ficará o painel dos atendentes
- **Importação/Exportação:** Permitir backup e replicação de fluxos

### 7.2. Monitoramento em Tempo Real

- **Dashboard Métrico:** Tempo médio por etapa, gargalos identificados
- **Heatmap:** Visualização de concentração de atendimentos por etapa
- **Alertas Configuráveis:** Notificações sobre anomalias no fluxo
- **Relatórios Personalizados:** Exportação de dados por período e departamento

## 8. Vantagens da Nova Abordagem

- **Flexibilidade Total:** Cada departamento otimiza seu próprio fluxo
- **Evolução Contínua:** Fluxos podem ser ajustados sem impacto no sistema
- **Métricas Precisas:** Análise detalhada do tempo em cada etapa
- **Experiência Otimizada:** Atendentes trabalham com processos familiares de sua área
- **Escalabilidade:** Novos departamentos podem ser adicionados facilmente
- **Governança:** Controle centralizado com autonomia departamental
- **Integração:** API robusta para integração com sistemas externos

## 9. Roadmap de Implementação

### Fase 1: Estrutura Base
1. Implementar novos modelos de dados
2. Criar migrations preservando dados existentes
3. Desenvolver interface administrativa para fluxos

### Fase 2: Frontend Kanban
1. Implementar componente kanban dinâmico
2. Integrar com backend de movimentação
3. Desenvolver sistema de filtros e buscas

### Fase 3: Automações e Métricas
1. Implementar sistema de regras e automações
2. Desenvolver dashboard analítico
3. Configurar sistema de notificações

### Fase 4: Otimização
1. Implementar缓存 e otimizações de performance
2. Adicionar funcionalidades avançadas
3. Testes de carga e estresse

## 10. Implementação dos Serviços de Fluxo

### 10.1. Serviço de Gerenciamento de Fluxos

```python
class FluxoAtendimentoService:
    """Serviço responsável por gerenciar operações com fluxos de atendimento."""

    @staticmethod
    def criar_fluxo_padrao(departamento: Departamento) -> FluxoAtendimento:
        """Cria um fluxo padrão para um departamento."""
        
    @staticmethod
    def validar_movimentacao(
        atendimento: Atendimento,
        etapa_destino: EtapaFluxo,
        atendente: Optional[Atendente] = None
    ) -> Tuple[bool, List[str]]:
        """Valida se um atendimento pode ser movido para uma etapa."""
        
    @staticmethod
    def mover_atendimento(
        atendimento: Atendimento,
        etapa_destino: EtapaFluxo,
        atendente: Optional[Atendente] = None,
        motivo: Optional[str] = None
    ) -> MovimentoFluxo:
        """Move um atendimento para uma nova etapa."""
        
    @staticmethod
    def atribuir_atendimento(
        atendimento: Atendimento,
        atendente: Atendente
    ) -> MovimentoFluxo:
        """Atribui um atendimento a um atendente específico."""
```

### 10.2. Serviço de Kanban

```python
class KanbanService:
    """Serviço para alimentar o frontend do painel Kanban."""

    @staticmethod
    def get_dados_kanban(
        departamento: Departamento,
        atendente: Optional[Atendente] = None,
        filtros: Optional[Dict] = None
    ) -> Dict:
        """Retorna dados estruturados para o painel Kanban."""
        
    @staticmethod
    def get_atendimentos_por_etapa(
        etapa: EtapaFluxo,
        atendente: Optional[Atendente] = None
    ) -> QuerySet[Atendimento]:
        """Retorna atendimentos em uma etapa específica."""
        
    @staticmethod
    def atualizar_posicao_atendimento(
        atendimento: Atendimento,
        nova_etapa: EtapaFluxo,
        nova_posicao: int
    ) -> bool:
        """Atualiza a posição do atendimento no kanban."""
```

### 10.3. Serviço de Automação

```python
class AutomacaoFluxoService:
    """Serviço para executar automações baseadas em regras do fluxo."""

    @staticmethod
    def verificar_regras_automaticas(atendimento: Atendimento) -> None:
        """Verifica e executa regras automáticas para um atendimento."""
        
    @staticmethod
    def processar_movimento_automatico(
        atendimento: Atendimento,
        regra: Dict
    ) -> Optional[EtapaFluxo]:
        """Processa uma regra de movimento automático."""
        
    @staticmethod
    def enviar_notificacoes(movimento: MovimentoFluxo) -> None:
        """Envia notificações baseadas em movimentos do fluxo."""
```

### 10.4. API REST Endpoints

```python
# endpoints/fluxos.py
class FluxoViewSet(viewsets.ModelViewSet):
    """API para gerenciar fluxos de atendimento."""
    
class EtapaViewSet(viewsets.ModelViewSet):
    """API para gerenciar etapas do fluxo."""

# endpoints/kanban.py
class KanbanView(APIView):
    """Endpoint para dados do painel Kanban."""
    
    def get(self, request, departamento_id):
        """Retorna dados estruturados para o Kanban."""
        
class MoverAtendimentoView(APIView):
    """Endpoint para mover atendimentos entre etapas."""
    
    def post(self, request, atendimento_id):
        """Move um atendimento para uma nova etapa."""
```

### 10.5. Signals do Django

```python
# signals/fluxos.py
@receiver(post_save, sender=Atendimento)
def processar_novo_atendimento(sender, instance, created, **kwargs):
    """Processa novo atendimento inserindo no fluxo inicial."""
    
@receiver(post_save, sender=MovimentoFluxo)
def processar_movimento_fluxo(sender, instance, created, **kwargs):
    """Processa eventos após movimento no fluxo."""
```

## 10. Considerações Técnicas

- **Performance:** Implementar cache para consultas frequentes de etapas
- **Concorrência:** Mecanismos de bloqueio para movimentações simultâneas
- **Auditoria:** Log completo de todas as movimentações e alterações
- **Backup:** Rotinas de backup específicas para configurações de fluxo
- **API:** Endpoints RESTful para integração com sistemas externos
- **Segurança:** Validação rigorosa de permissões em cada movimentação
- **Migrations:** Scripts para migrar dados existentes do StatusAtendimento para o novo sistema
- **Frontend:** Componentes React/Vue reativos para atualização em tempo real do Kanban