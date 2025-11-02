# Exemplos de Configuração: Financeiro e Suporte Técnico

Este documento mostra exemplos detalhados de como configurar os atributos dos models e filtros para os departamentos financeiro e suporte técnico.

## 💳 Departamento Financeiro

### Campos Específicos para Filtros

```python
class Atendimento(models.Model):
    # ... campos existentes ...
    
    # Campos específicos para financeiro
    tipo_solicitacao: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("emprestimo", "Empréstimo"),
            ("financiamento", "Financiamento"),
            ("cartao_credito", "Cartão de Crédito"),
            ("consignado", "Consignado"),
            ("refinanciamento", "Refinanciamento"),
            ("antecipacao", "Antecipação de Recebíveis"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Tipo de solicitação financeira"
    )
    
    valor_solicitado: models.DecimalField[Decimal | None] = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Valor solicitado pelo cliente"
    )
    
    valor_aprovado: models.DecimalField[Decimal | None] = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Valor aprovado após análise"
    )
    
    prazo_meses: models.PositiveIntegerField[int | None] = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Prazo em meses"
    )
    
    taxa_juros: models.DecimalField[Decimal | None] = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Taxa de juros (%) ao mês"
    )
    
    score_credito: models.IntegerField[int | None] = models.IntegerField(
        blank=True,
        null=True,
        help_text="Score de crédito (0-1000)"
    )
    
    status_analise: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("aguardando_documento", "Aguardando Documento"),
            ("em_analise", "Em Análise"),
            ("aprovado", "Aprovado"),
            ("reprovado", "Reprovado"),
            ("pendente_aprovacao", "Pendente Aprovação"),
            ("cancelado", "Cancelado")
        ],
        blank=True,
        null=True,
        help_text="Status da análise de crédito"
    )
    
    documentos_requeridos: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de documentos requeridos"
    )
    
    documentos_recebidos: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de documentos já recebidos"
    )
    
    risco_cliente: models.CharField[str | None] = models.CharField(
        max_length=20,
        choices=[
            ("baixo", "Baixo Risco"),
            ("medio", "Médio Risco"),
            ("alto", "Alto Risco"),
            ("muito_alto", "Muito Alto Risco")
        ],
        blank=True,
        null=True,
        help_text="Classificação de risco do cliente"
    )
    
    data_limite_documento: models.DateField[datetime.date | None] = models.DateField(
        blank=True,
        null=True,
        help_text="Data limite para envio de documentos"
    )
    
    tipo_pessoa: models.CharField[str | None] = models.CharField(
        max_length=20,
        choices=[
            ("fisica", "Pessoa Física"),
            ("juridica", "Pessoa Jurídica"),
            ("mei", "MEI"),
            ("epp", "EPP"),
            ("me", "Microempresa")
        ],
        blank=True,
        null=True,
        help_text="Tipo de pessoa (física/jurídica)"
    )
    
    garantia: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("imovel", "Imóvel"),
            ("veiculo", "Veículo"),
            ("garantidor", "Garantidor"),
            ("fianca_bancaria", "Fiança Bancária"),
            ("sem_garantia", "Sem Garantia")
        ],
        blank=True,
        null=True,
        help_text="Tipo de garantia"
    )
    
    # Campos para análise e métricas
    data_aprovacao: models.DateTimeField[datetime.datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data da aprovação"
    )
    
    analista_responsavel: models.ForeignKey[Optional["operacional.Atendente"]] = models.ForeignKey(
        "operacional.Atendente",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="analises_credito",
        help_text="Analista responsável pela análise"
    )
    
    motivo_reprovacao: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo da reprovação"
    )
```

### Configuração do Fluxo Financeiro

```python
def configurar_fluxo_financeiro(departamento: Departamento) -> FluxoAtendimento:
    """Configuração detalhada do fluxo financeiro."""
    
    fluxo = FluxoAtendimento.objects.create(
        departamento=departamento,
        nome="Fluxo Financeiro Completo",
        descricao="Gestão completa de solicitações financeiras"
    )
    
    etapas_config = [
        {
            "nome": "📝 Nova Solicitação",
            "descricao": "Novas solicitações recebidas para análise",
            "ordem": 1,
            "cor": "#3B82F6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["tipo_solicitacao", "valor_solicitado", "tipo_pessoa"],
            "filtros_disponiveis": [
                {"campo": "tipo_solicitacao", "tipo": "choice", "label": "Tipo de Solicitação"},
                {"campo": "valor_solicitado", "tipo": "range", "label": "Valor Solicitado"},
                {"campo": "tipo_pessoa", "tipo": "choice", "label": "Tipo de Pessoa"},
                {"campo": "score_credito", "tipo": "range", "label": "Score de Crédito"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "tipo_solicitacao",
                "mostrar_campos": ["valor_solicitado", "tipo_pessoa", "score_credito"]
            }
        },
        {
            "nome": "🔍 Análise de Crédito",
            "descricao": "Análise detalhada do perfil de crédito",
            "ordem": 2,
            "cor": "#6366F1",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["score_credito", "risco_cliente"],
            "regras_transicao": {
                "exigir_analista": True,
                "tempo_maximo_analise": 48  # horas
            },
            "filtros_disponiveis": [
                {"campo": "risco_cliente", "tipo": "choice", "label": "Risco"},
                {"campo": "score_credito", "tipo": "range", "label": "Score"},
                {"campo": "analista_responsavel", "tipo": "atendente", "label": "Analista"},
                {"campo": "tipo_pessoa", "tipo": "choice", "label": "Tipo de Pessoa"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "score_credito",
                "grupo_por": "risco_cliente",
                "mostrar_campos": ["score_credito", "risco_cliente", "valor_solicitado"]
            }
        },
        {
            "nome": "📧 Aguardando Documentos",
            "descricao": "Aguardando envio de documentos pelo cliente",
            "ordem": 3,
            "cor": "#F59E0B",
            "tipo_etapa": TipoEtapa.ESPERA,
            "permite_atribuicao": False,
            "automatico": True,
            "campos_obrigatorios": ["documentos_requeridos", "data_limite_documento"],
            "regras_transicao": {
                "lembrar_cliente": True,
                "intervalo_lembrete": 24,
                "maximo_lembretes": 3,
                "notificar_analista": True
            },
            "filtros_disponiveis": [
                {"campo": "data_limite_documento", "tipo": "date_range", "label": "Prazo Documento"},
                {"campo": "documentos_recebidos", "tipo": "list", "label": "Documentos Recebidos"},
                {"campo": "documentos_requeridos", "tipo": "list", "label": "Documentos Requeridos"},
                {"campo": "analista_responsavel", "tipo": "atendente", "label": "Analista"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "data_limite_documento",
                "grupo_por": "analista_responsavel",
                "mostrar_campos": ["data_limite_documento", "documentos_recebidos", "valor_solicitado"]
            }
        },
        {
            "nome": "⚡ Processamento Final",
            "descricao": "Processamento final da aprovação",
            "ordem": 4,
            "cor": "#EC4899",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["valor_aprovado", "prazo_meses"],
            "regras_transicao": {
                "validar_limites": True,
                "exigir_aprovacao_gestor": True
            },
            "filtros_disponiveis": [
                {"campo": "valor_aprovado", "tipo": "range", "label": "Valor Aprovado"},
                {"campo": "prazo_meses", "tipo": "range", "label": "Prazo (meses)"},
                {"campo": "taxa_juros", "tipo": "range", "label": "Taxa de Juros"},
                {"campo": "garantia", "tipo": "choice", "label": "Garantia"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_aprovacao",
                "grupo_por": "status_analise",
                "mostrar_campos": ["valor_aprovado", "taxa_juros", "prazo_meses"]
            }
        },
        {
            "nome": "✅ Aprovado",
            "descricao": "Solicitação aprovada e liberada",
            "ordem": 5,
            "cor": "#10B981",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["data_aprovacao", "valor_aprovado"],
            "regras_transicao": {
                "finalizar_atendimento": True,
                "gerar_contrato": True,
                "notificar_cliente": True
            },
            "filtros_disponiveis": [
                {"campo": "valor_aprovado", "tipo": "range", "label": "Valor Aprovado"},
                {"campo": "data_aprovacao", "tipo": "date_range", "label": "Data Aprovação"},
                {"campo": "analista_responsavel", "tipo": "atendente", "label": "Analista"},
                {"campo": "prazo_meses", "tipo": "range", "label": "Prazo (meses)"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_aprovacao",
                "grupo_por": "analista_responsavel",
                "mostrar_campos": ["valor_aprovado", "prazo_meses", "taxa_juros"]
            }
        },
        {
            "nome": "❌ Reprovado",
            "descricao": "Solicitação negada",
            "ordem": 6,
            "cor": "#EF4444",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["motivo_reprovacao"],
            "regras_transicao": {
                "finalizar_atendimento": True,
                "exigir_motivo": True,
                "notificar_cliente": True
            },
            "filtros_disponiveis": [
                {"campo": "motivo_reprovacao", "tipo": "text", "label": "Motivo"},
                {"campo": "risco_cliente", "tipo": "choice", "label": "Risco"},
                {"campo": "score_credito", "tipo": "range", "label": "Score"},
                {"campo": "analista_responsavel", "tipo": "atendente", "label": "Analista"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "risco_cliente",
                "mostrar_campos": ["motivo_reprovacao", "score_credito", "valor_solicitado"]
            }
        }
    ]
    
    # Criar as etapas
    for etapa_data in etapas_config:
        extrair_filtros = etapa_data.pop("filtros_disponiveis", [])
        extrair_visualizacao = etapa_data.pop("visualizacao_padrao", {})
        
        etapa = EtapaFluxo.objects.create(fluxo=fluxo, **etapa_data)
        
        etapa.regras_transicao.update({
            "filtros_disponiveis": extrair_filtros,
            "visualizacao_padrao": extrair_visualizacao
        })
        etapa.save()
    
    return fluxo
```

## 🛠️ Departamento Suporte Técnico

### Campos Específicos para Filtros

```python
class Atendimento(models.Model):
    # ... campos existentes ...
    
    # Campos específicos para suporte técnico
    categoria_problema: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("hardware", "Hardware"),
            ("software", "Software"),
            ("rede", "Rede"),
            ("impressao", "Impressão"),
            ("email", "E-mail"),
            ("internet", "Internet"),
            ("sistema_interno", "Sistema Interno"),
            ("mobile", "Mobile"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Categoria do problema"
    )
    
    subcategoria_problema: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Subcategoria específica do problema"
    )
    
    gravidade: models.CharField[str | None] = models.CharField(
        max_length=20,
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
            ("critica", "Crítica")
        ],
        blank=True,
        null=True,
        help_text="Nível de gravidade do problema"
    )
    
    impacto: models.CharField[str | None] = models.CharField(
        max_length=20,
        choices=[
            ("individual", "Individual"),
            ("equipe", "Equipe"),
            ("departamento", "Departamento"),
            ("empresa", "Empresa")
        ],
        blank=True,
        null=True,
        help_text="Nível de impacto do problema"
    )
    
    urgencia: models.CharField[str | None] = models.CharField(
        max_length=20,
        choices=[
            ("baixa", "Baixa"),
            ("media", "Média"),
            ("alta", "Alta"),
            ("imediata", "Imediata")
        ],
        blank=True,
        null=True,
        help_text="Nível de urgência"
    )
    
    sla_horas: models.PositiveIntegerField[int | None] = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="SLA em horas para resolução"
    )
    
    nivel_suporte: models.PositiveIntegerField[int] = models.PositiveIntegerField(
        default=1,
        help_text="Nível de suporte (1, 2, 3)"
    )
    
    tipo_dispositivo: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("desktop", "Desktop"),
            ("notebook", "Notebook"),
            ("servidor", "Servidor"),
            ("mobile", "Dispositivo Móvel"),
            ("impressora", "Impressora"),
            ("roteador", "Roteador"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Tipo de dispositivo afetado"
    )
    
    sistema_operacional: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("windows_10", "Windows 10"),
            ("windows_11", "Windows 11"),
            ("macos", "macOS"),
            ("linux", "Linux"),
            ("ios", "iOS"),
            ("android", "Android"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Sistema operacional"
    )
    
    descricao_tecnica: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição técnica detalhada do problema"
    )
    
    passos_reproduzir: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Passos para reproduzir o problema"
    )
    
    solucao_aplicada: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Solução aplicada para resolver o problema"
    )
    
    conhecimento_base: models.URLField[str | None] = models.URLField(
        blank=True,
        null=True,
        help_text="Link para artigo na base de conhecimento"
    )
    
    tempo_resolucao: models.DurationField[datetime.timedelta | None] = models.DurationField(
        blank=True,
        null=True,
        help_text="Tempo total para resolução do problema"
    )
    
    satisfacao_cliente: models.IntegerField[int | None] = models.IntegerField(
        blank=True,
        null=True,
        choices=[(i, f"{i} estrelas") for i in range(1, 6)],
        help_text="Avaliação de satisfação do cliente (1-5)"
    )
    
    motivo_reabertura: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Motivo da reabertura do chamado"
    )
    
    numero_reaberturas: models.PositiveIntegerField[int] = models.PositiveIntegerField(
        default=0,
        help_text="Número de vezes que o chamado foi reaberto"
    )
    
    # Campos para hardware específico
    numero_serie: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de série do equipamento"
    )
    
    patrimonio: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Número do patrimônio"
    )
    
    # Campos para software
    versao_software: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Versão do software/problema"
    )
    
    modulo_afetado: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Módulo do sistema afetado"
    )
    
    tags_tecnicas: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags técnicas para categorização"
    )
    
    class Meta:
        # Índices para otimização de filtros
        indexes = [
            models.Index(fields=["categoria_problema", "gravidade", "nivel_suporte"]),
            models.Index(fields=["impacto", "urgencia", "nivel_suporte"]),
            models.Index(fields=["sla_horas", "nivel_suporte"]),
            models.Index(fields=["tipo_dispositivo", "sistema_operacional"]),
            models.Index(fields=["data_inicio", "nivel_suporte"]),
        ]
```

### Configuração do Fluxo Suporte Técnico

```python
def configurar_fluxo_suporte_tecnico(departamento: Departamento) -> FluxoAtendimento:
    """Configuração detalhada do fluxo de suporte técnico."""
    
    fluxo = FluxoAtendimento.objects.create(
        departamento=departamento,
        nome="Fluxo Suporte Técnico Multinível",
        descricao="Gestão completa de chamados técnicos em múltiplos níveis"
    )
    
    etapas_config = [
        {
            "nome": "🆕 Novo Chamado",
            "descricao": "Novos chamados recebidos para triagem",
            "ordem": 1,
            "cor": "#3B82F6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["categoria_problema", "gravidade", "impacto"],
            "regras_transicao": {
                "calcular_prioridade": True,
                "definir_sla_automatico": True,
                "classificar_nivel_automatico": True
            },
            "filtros_disponiveis": [
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "gravidade", "tipo": "choice", "label": "Gravidade"},
                {"campo": "impacto", "tipo": "choice", "label": "Impacto"},
                {"campo": "urgencia", "tipo": "choice", "label": "Urgência"},
                {"campo": "nivel_suporte", "tipo": "choice", "label": "Nível Suporte"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "categoria_problema",
                "mostrar_campos": ["gravidade", "impacto", "nivel_suporte", "sla_horas"]
            }
        },
        {
            "nome": "🔬 Triagem",
            "descricao": "Análise inicial e classificação do chamado",
            "ordem": 2,
            "cor": "#6366F1",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["nivel_suporte", "sla_horas"],
            "regras_transicao": {
                "validar_informacoes": True,
                "reclassificar_se_necessario": True
            },
            "filtros_disponiveis": [
                {"campo": "nivel_suporte", "tipo": "choice", "label": "Nível"},
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "tipo_dispositivo", "tipo": "choice", "label": "Dispositivo"},
                {"campo": "sistema_operacional", "tipo": "choice", "label": "SO"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "sla_horas",
                "grupo_por": "gravidade",
                "mostrar_campos": ["nivel_suporte", "sla_horas", "tipo_dispositivo"]
            }
        },
        {
            "nome": "🛠️ Em Andamento N1",
            "descricao": "Solução sendo trabalhada pelo suporte nível 1",
            "ordem": 3,
            "cor": "#10B981",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "regras_transicao": {
                "tempo_maximo_n1": 4,  # horas
                "escalamento_automatico": True
            },
            "filtros_disponiveis": [
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Técnico"},
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "gravidade", "tipo": "choice", "label": "Gravidade"},
                {"campo": "sla_horas", "tipo": "range", "label": "SLA Restante"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "atendente_humano",
                "mostrar_campos": ["sla_horas", "gravidade", "categoria_problema"]
            }
        },
        {
            "nome": "⏳ Aguardando Cliente",
            "descricao": "Aguardando informações ou acesso do cliente",
            "ordem": 4,
            "cor": "#F59E0B",
            "tipo_etapa": TipoEtapa.ESPERA,
            "permite_atribuicao": False,
            "automatico": True,
            "regras_transicao": {
                "lembrar_cliente": True,
                "intervalo_lembrete": 24,
                "maximo_espera": 72,  # horas
                "retorno_automatico": True
            },
            "filtros_disponiveis": [
                {"campo": "data_limite_documento", "tipo": "date_range", "label": "Prazo Cliente"},
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Técnico"},
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "gravidade", "tipo": "choice", "label": "Gravidade"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "data_limite_documento",
                "grupo_por": "atendente_humano",
                "mostrar_campos": ["data_limite_documento", "gravidade", "numero_reaberturas"]
            }
        },
        {
            "nome": "🔄 Escalado N2",
            "descricao": "Chamado escalado para suporte nível 2",
            "ordem": 5,
            "cor": "#8B5CF6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "automatico": True,
            "regras_transicao": {
                "notificar_n2": True,
                "transferir_historico": True,
                "priorizar_automatico": True
            },
            "filtros_disponiveis": [
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "subcategoria_problema", "tipo": "text", "label": "Subcategoria"},
                {"campo": "tipo_dispositivo", "tipo": "choice", "label": "Dispositivo"},
                {"campo": "sistema_operacional", "tipo": "choice", "label": "SO"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "categoria_problema",
                "mostrar_campos": ["gravidade", "numero_reaberturas", "descricao_tecnica"]
            }
        },
        {
            "nome": "🧪 Testes",
            "descricao": "Testando a solução aplicada",
            "ordem": 6,
            "cor": "#EC4899",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["solucao_aplicada"],
            "regras_transicao": {
                "validar_com_cliente": True,
                "documentar_solucao": True
            },
            "filtros_disponiveis": [
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Técnico"},
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "solucao_aplicada", "tipo": "text", "label": "Solução"},
                {"campo": "conhecimento_base", "tipo": "url", "label": "KB"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "atendente_humano",
                "mostrar_campos": ["solucao_aplicada", "conhecimento_base", "tempo_resolucao"]
            }
        },
        {
            "nome": "✅ Resolvido",
            "descricao": "Problema resolvido com sucesso",
            "ordem": 7,
            "cor": "#059669",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["solucao_aplicada", "satisfacao_cliente"],
            "regras_transicao": {
                "finalizar_atendimento": True,
                "calcular_metricas": True,
                "enviar_pesquisa_satisfacao": True
            },
            "filtros_disponiveis": [
                {"campo": "satisfacao_cliente", "tipo": "range", "label": "Satisfação"},
                {"campo": "tempo_resolucao", "tipo": "range", "label": "Tempo Resolução"},
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Técnico"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "satisfacao_cliente",
                "mostrar_campos": ["satisfacao_cliente", "tempo_resolucao", "categoria_problema"]
            }
        },
        {
            "nome": "❌ Fechado sem Solução",
            "descricao": "Chamado fechado sem resolução",
            "ordem": 8,
            "cor": "#EF4444",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["motivo_reabertura"],
            "regras_transicao": {
                "finalizar_atendimento": True,
                "exigir_motivo": True,
                "notificar_gestor": True
            },
            "filtros_disponiveis": [
                {"campo": "motivo_reabertura", "tipo": "text", "label": "Motivo"},
                {"campo": "categoria_problema", "tipo": "choice", "label": "Categoria"},
                {"campo": "numero_reaberturas", "tipo": "range", "label": "Reaberturas"},
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Técnico"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "categoria_problema",
                "mostrar_campos": ["motivo_reabertura", "numero_reaberturas", "gravidade"]
            }
        }
    ]
    
    # Criar as etapas
    for etapa_data in etapas_config:
        extrair_filtros = etapa_data.pop("filtros_disponiveis", [])
        extrair_visualizacao = etapa_data.pop("visualizacao_padrao", {})
        
        etapa = EtapaFluxo.objects.create(fluxo=fluxo, **etapa_data)
        
        etapa.regras_transicao.update({
            "filtros_disponiveis": extrair_filtros,
            "visualizacao_padrao": extrair_visualizacao
        })
        etapa.save()
    
    return fluxo
```

## 🎯 Resumo dos Principais Campos por Departamento

### Financeiro
- **Essenciais**: tipo_solicitacao, valor_solicitado, tipo_pessoa, score_credito
- **Análise**: risco_cliente, status_analise, documentos_requeridos
- **Controle**: data_limite_documento, analista_responsavel, motivo_reprovacao

### Suporte Técnico
- **Classificação**: categoria_problema, gravidade, impacto, urgencia
- **Técnico**: tipo_dispositivo, sistema_operacional, descricao_tecnica
- **Métricas**: sla_horas, tempo_resolucao, satisfacao_cliente, numero_reaberturas

Essa estrutura permite filtros potentes e específicos para cada tipo de negócio, mantendo a flexibilidade para personalização futura.