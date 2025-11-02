# Exemplo Detalhado: Atributos dos Models para Gestão de Filtros

Este documento mostra como configurar os atributos dos models para implementar filtros e gestão específica para cada fluxo de atendimento, com foco no exemplo do departamento comercial.

## 📋 Estrutura Base: Atendimento

### Campos Principais para Filtros

```python
class Atendimento(models.Model):
    # ... campos existentes ...
    
    # Campos específicos para filtros comerciais
    valor_orcamento: models.DecimalField[
        Decimal | None
    ] = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Valor do orçamento solicitado"
    )
    
    moeda: models.CharField[str] = models.CharField(
        max_length=3,
        choices=[("BRL", "Real"), ("USD", "Dólar"), ("EUR", "Euro")],
        default="BRL",
        help_text="Moeda do orçamento"
    )
    
    produto_servico: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Produto ou serviço principal"
    )
    
    categoria_venda: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("produto", "Produto"),
            ("servico", "Serviço"),
            ("assinatura", "Assinatura"),
            ("consultoria", "Consultoria"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Categoria da venda"
    )
    
    origem_lead: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("site", "Site"),
            ("redes_sociais", "Redes Sociais"),
            ("indicacao", "Indicação"),
            ("telefone", "Telefone"),
            ("email", "E-mail"),
            ("evento", "Evento"),
            ("parceiro", "Parceiro"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Origem do lead"
    )
    
    estagio_negocio: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("prospeccao", "Prospecção"),
            ("qualificacao", "Qualificação"),
            ("proposta", "Proposta"),
            ("negociacao", "Negociação"),
            ("fechamento", "Fechamento"),
            ("pos_venda", "Pós-venda")
        ],
        blank=True,
        null=True,
        help_text="Estágio do negócio"
    )
    
    probabilidade_fechamento: models.IntegerField[int | None] = models.IntegerField(
        blank=True,
        null=True,
        choices=[(i, f"{i}%") for i in range(0, 101, 10)],
        help_text="Probabilidade de fechamento (%)"
    )
    
    data_fechamento_prevista: models.DateField[datetime.date | None] = models.DateField(
        blank=True,
        null=True,
        help_text="Data prevista para fechamento"
    )
    
    motivo_perda: models.CharField[str | None] = models.CharField(
        max_length=100,
        choices=[
            ("preco", "Preço"),
            ("concorrencia", "Concorrência"),
            ("timing", "Timing"),
            ("orcamento", "Sem orçamento"),
            ("decisao", "Decisão interna"),
            ("sem_interesse", "Sem interesse"),
            ("outro", "Outro")
        ],
        blank=True,
        null=True,
        help_text="Motivo da perda do negócio"
    )
    
    # Campos para filtros avançados
    tags_comerciais: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags específicas do comercial (ex: ['cliente-vip', 'recorrente'])"
    )
    
    segmento_cliente: models.CharField[str | None] = models.CharField(
        max_length=50,
        choices=[
            ("pequeno", "Pequeno Porte"),
            ("medio", "Médio Porte"),
            ("grande", "Grande Porte"),
            ("enterprise", "Enterprise"),
            ("startup", "Startup")
        ],
        blank=True,
        null=True,
        help_text="Segmento/tamanho do cliente"
    )
    
    # Campos para análise e métricas
    data_proposta_enviada: models.DateTimeField[datetime.datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data de envio da proposta"
    )
    
    valor_proposta: models.DecimalField[Decimal | None] = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Valor da proposta enviada"
    )
    
    quantidade_followups: models.PositiveIntegerField[int] = models.PositiveIntegerField(
        default=0,
        help_text="Número de follow-ups realizados"
    )
    
    proximo_followup: models.DateTimeField[datetime.datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data do próximo follow-up agendado"
    )
    
    class Meta:
        # Índices para otimização de filtros
        indexes = [
            models.Index(fields=["departamento", "etapa_atual"]),
            models.Index(fields=["categoria_venda", "estagio_negocio"]),
            models.Index(fields=["origem_lead", "probabilidade_fechamento"]),
            models.Index(fields=["data_fechamento_prevista", "valor_orcamento"]),
            models.Index(fields=["segmento_cliente", "moeda"]),
            models.Index(fields=["data_proposta_enviada", "valor_proposta"]),
        ]
```

## 🎯 Configuração do Fluxo Comercial

### Exemplo Completo de Configuração

```python
def configurar_fluxo_comercial(departamento: Departamento) -> FluxoAtendimento:
    """Configuração detalhada do fluxo comercial com filtros específicos."""
    
    fluxo = FluxoAtendimento.objects.create(
        departamento=departamento,
        nome="Fluxo Comercial Avançado",
        descricao="Fluxo completo com gestão de leads, propostas e fechamento"
    )
    
    # Configuração das etapas com filtros específicos
    etapas_config = [
        {
            "nome": "📥 Novo Lead",
            "descricao": "Leads recém-chegados para qualificação",
            "ordem": 1,
            "cor": "#3B82F6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["origem_lead", "categoria_venda"],
            "regras_transicao": {
                "tempo_maximo_espera": 24,  # horas
                "notificar_gestor": True,
                "acao_expiracao": "atribuir_automaticamente"
            },
            "filtros_disponiveis": [
                {"campo": "origem_lead", "tipo": "choice", "label": "Origem do Lead"},
                {"campo": "categoria_venda", "tipo": "choice", "label": "Categoria"},
                {"campo": "segmento_cliente", "tipo": "choice", "label": "Segmento"},
                {"campo": "valor_orcamento", "tipo": "range", "label": "Valor Estimado"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "origem_lead",
                "mostrar_campos": ["valor_orcamento", "segmento_cliente"]
            }
        },
        {
            "nome": "🔍 Qualificação",
            "descricao": "Análise e qualificação do lead",
            "ordem": 2,
            "cor": "#8B5CF6",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["estagio_negocio", "probabilidade_fechamento"],
            "regras_transicao": {
                "minimo_probabilidade": 30,
                "exigir_qualificacao": True
            },
            "filtros_disponiveis": [
                {"campo": "probabilidade_fechamento", "tipo": "range", "label": "Probabilidade (%)"},
                {"campo": "estagio_negocio", "tipo": "choice", "label": "Estágio"},
                {"campo": "data_fechamento_prevista", "tipo": "date_range", "label": "Previsão de Fechamento"},
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Responsável"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "probabilidade_fechamento",
                "grupo_por": "segmento_cliente",
                "mostrar_campos": ["probabilidade_fechamento", "data_fechamento_prevista", "valor_orcamento"]
            }
        },
        {
            "nome": "📄 Proposta Enviada",
            "descricao": "Proposta comercial enviada para análise",
            "ordem": 3,
            "cor": "#EC4899",
            "tipo_etapa": TipoEtapa.ESPERA,
            "permite_atribuicao": False,
            "automatico": True,
            "campos_obrigatorios": ["data_proposta_enviada", "valor_proposta"],
            "regras_transicao": {
                "tempo_maximo_espera": 72,
                "lembrar_cliente": True,
                "intervalo_lembrete": 24,
                "maximo_lembretes": 3
            },
            "filtros_disponiveis": [
                {"campo": "valor_proposta", "tipo": "range", "label": "Valor da Proposta"},
                {"campo": "data_proposta_enviada", "tipo": "date_range", "label": "Data Envio"},
                {"campo": "proximo_followup", "tipo": "date", "label": "Próximo Follow-up"},
                {"campo": "quantidade_followups", "tipo": "number", "label": "Qtd. Follow-ups"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "data_proposta_enviada",
                "grupo_por": "atendente_humano",
                "mostrar_campos": ["valor_proposta", "data_proposta_enviada", "quantidade_followups"]
            }
        },
        {
            "nome": "🤝 Negociação",
            "descricao": "Em negociação ativa com o cliente",
            "ordem": 4,
            "cor": "#F59E0B",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["data_fechamento_prevista"],
            "regras_transicao": {
                "probabilidade_minima": 50,
                "exigir_prazo": True
            },
            "filtros_disponiveis": [
                {"campo": "probabilidade_fechamento", "tipo": "range", "label": "Probabilidade (%)"},
                {"campo": "data_fechamento_prevista", "tipo": "date_range", "label": "Previsão Fechamento"},
                {"campo": "valor_proposta", "tipo": "range", "label": "Valor"},
                {"campo": "moeda", "tipo": "choice", "label": "Moeda"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "data_fechamento_prevista",
                "grupo_por": "probabilidade_fechamento",
                "mostrar_campos": ["probabilidade_fechamento", "data_fechamento_prevista", "valor_proposta"]
            }
        },
        {
            "nome": "✅ Ganho",
            "descricao": "Negócio fechado com sucesso",
            "ordem": 5,
            "cor": "#10B981",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["valor_proposta", "data_fechamento_prevista"],
            "regras_transicao": {
                "finalizar_atendimento": True,
                "gerar_comissao": True,
                "notificar_gestor": True
            },
            "filtros_disponiveis": [
                {"campo": "valor_proposta", "tipo": "range", "label": "Valor Ganho"},
                {"campo": "data_fechamento_prevista", "tipo": "date_range", "label": "Data Ganho"},
                {"campo": "atendente_humano", "tipo": "atendente", "label": "Vendedor"},
                {"campo": "segmento_cliente", "tipo": "choice", "label": "Segmento"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_fechamento_prevista",
                "grupo_por": "atendente_humano",
                "mostrar_campos": ["valor_proposta", "data_fechamento_prevista", "probabilidade_fechamento"]
            }
        },
        {
            "nome": "❌ Perdido",
            "descricao": "Negócio não concretizado",
            "ordem": 6,
            "cor": "#EF4444",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["motivo_perda"],
            "regras_transicao": {
                "finalizar_atendimento": True,
                "exigir_motivo": True,
                "notificar_gestor": True
            },
            "filtros_disponiveis": [
                {"campo": "motivo_perda", "tipo": "choice", "label": "Motivo da Perda"},
                {"campo": "valor_proposta", "tipo": "range", "label": "Valor Perdido"},
                {"campo": "data_proposta_enviada", "tipo": "date_range", "label": "Período"},
                {"campo": "quantidade_followups", "tipo": "number", "label": "Follow-ups Realizados"}
            ],
            "visualizacao_padrao": {
                "ordenar_por": "-data_inicio",
                "grupo_por": "motivo_perda",
                "mostrar_campos": ["motivo_perda", "valor_proposta", "quantidade_followups"]
            }
        }
    ]
    
    # Criar as etapas com configuração completa
    for etapa_data in etapas_config:
        extrair_filtros = etapa_data.pop("filtros_disponiveis", [])
        extrair_visualizacao = etapa_data.pop("visualizacao_padrao", {})
        
        etapa = EtapaFluxo.objects.create(fluxo=fluxo, **etapa_data)
        
        # Salvar configurações de filtros e visualização
        etapa.regras_transicao.update({
            "filtros_disponiveis": extrair_filtros,
            "visualizacao_padrao": extrair_visualizacao
        })
        etapa.save()
    
    return fluxo
```

## 🔧 Serviço de Filtros Avançados

```python
class FiltroAtendimentoService:
    """Serviço para aplicar filtros dinâmicos baseados na configuração da etapa."""
    
    @staticmethod
    def aplicar_filtros_dinamicos(
        queryset: QuerySet[Atendimento],
        etapa: EtapaFluxo,
        filtros_aplicados: dict,
        usuario: Optional["User"] = None
    ) -> QuerySet[Atendimento]:
        """
        Aplica filtros dinâmicos baseados na configuração da etapa.
        """
        # Obter configuração de filtros da etapa
        config_filtros = etapa.regras_transicao.get("filtros_disponiveis", [])
        
        for filtro_config in config_filtros:
            campo = filtro_config["campo"]
            tipo_filtro = filtro_config["tipo"]
            
            if campo in filtros_aplicados:
                valor = filtros_aplicados[campo]
                
                if tipo_filtro == "choice":
                    if isinstance(valor, list):
                        queryset = queryset.filter(**{f"{campo}__in": valor})
                    else:
                        queryset = queryset.filter(**{campo: valor})
                
                elif tipo_filtro == "range":
                    if isinstance(valor, dict):
                        if valor.get("min"):
                            queryset = queryset.filter(**{f"{campo}__gte": valor["min"]})
                        if valor.get("max"):
                            queryset = queryset.filter(**{f"{campo}__lte": valor["max"]})
                
                elif tipo_filtro == "date_range":
                    if isinstance(valor, dict):
                        if valor.get("start"):
                            queryset = queryset.filter(**{f"{campo}__date__gte": valor["start"]})
                        if valor.get("end"):
                            queryset = queryset.filter(**{f"{campo}__date__lte": valor["end"]})
                
                elif tipo_filtro == "date":
                    queryset = queryset.filter(**{f"{campo}__date": valor})
                
                elif tipo_filtro == "number":
                    queryset = queryset.filter(**{campo: valor})
                
                elif tipo_filtro == "atendente":
                    # Filtra por atendente específico
                    queryset = queryset.filter(atendente_humano__id=valor)
        
        return queryset
    
    @staticmethod
    def get_opcoes_filtro(
        etapa: EtapaFluxo,
        usuario: Optional["User"] = None
    ) -> dict:
        """
        Retorna opções dinâmicas para filtros baseadas nos dados existentes.
        """
        queryset = etapa.atendimentos.all()
        
        opcoes = {}
        config_filtros = etapa.regras_transicao.get("filtros_disponiveis", [])
        
        for filtro_config in config_filtros:
            campo = filtro_config["campo"]
            tipo_filtro = filtro_config["tipo"]
            
            if tipo_filtro == "choice":
                # Para choices, buscar valores únicos existentes
                valores = queryset.exclude(**{campo: None}).values_list(campo, flat=True).distinct()
                
                if campo == "origem_lead":
                    choices = dict(Atendimento._meta.get_field(campo).choices)
                    opcoes[campo] = [
                        {"value": val, "label": choices.get(val, val)}
                        for val in valores if val
                    ]
                else:
                    opcoes[campo] = [
                        {"value": val, "label": val}
                        for val in valores if val
                    ]
            
            elif tipo_filtro == "range":
                # Para ranges, buscar min e max existentes
                campo_model = Atendimento._meta.get_field(campo)
                if hasattr(campo_model, 'max_digits'):  # DecimalField
                    valores = queryset.aggregate(
                        min=models.Min(campo),
                        max=models.Max(campo)
                    )
                    opcoes[campo] = {
                        "min": float(valores["min"]) if valores["min"] else 0,
                        "max": float(valores["max"]) if valores["max"] else 1000000,
                        "step": 0.01
                    }
                else:  # IntegerField
                    valores = queryset.aggregate(
                        min=models.Min(campo),
                        max=models.Max(campo)
                    )
                    opcoes[campo] = {
                        "min": valores["min"] or 0,
                        "max": valores["max"] or 100,
                        "step": 1
                    }
            
            elif tipo_filtro == "atendente":
                # Para atendentes, buscar atendentes da etapa
                atendentes = queryset.values_list(
                    "atendente_humano__id",
                    "atendente_humano__nome"
                ).distinct()
                
                opcoes[campo] = [
                    {"value": id_atendente, "label": nome_atendente}
                    for id_atendente, nome_atendente in atendentes
                    if id_atendente and nome_atendente
                ]
        
        return opcoes
    
    @staticmethod
    def get_visualizacao_padrao(etapa: EtapaFluxo) -> dict:
        """
        Retorna configuração de visualização padrão para a etapa.
        """
        return etapa.regras_transicao.get("visualizacao_padrao", {
            "ordenar_por": "-data_inicio",
            "grupo_por": None,
            "mostrar_campos": ["assunto", "data_inicio"]
        })
```

## 📊 Exemplo de Uso no Frontend

```javascript
// Exemplo de como o frontend consumiria esses filtros
const usarFiltrosKanban = (etapaId, usuarioId) => {
  const [filtros, setFiltros] = useState({});
  const [opcoes, setOpcoes] = useState({});
  const [visualizacao, setVisualizacao] = useState({});
  
  useEffect(() => {
    // Carregar configuração da etapa
    fetch(`/api/etapas/${etapaId}/config/`)
      .then(res => res.json())
      .then(data => {
        setOpcoes(data.opcoes_filtro);
        setVisualizacao(data.visualizacao_padrao);
      });
  }, [etapaId]);
  
  const aplicarFiltro = (campo, valor) => {
    setFiltros(prev => ({
      ...prev,
      [campo]: valor
    }));
  };
  
  return {
    filtros,
    opcoes,
    visualizacao,
    aplicarFiltro
  };
};

// Componente de filtro dinâmico
const FiltroDinamico = ({ config, valor, onChange }) => {
  switch (config.tipo) {
    case 'choice':
      return (
        <Select
          options={opcoes[config.campo]}
          value={valor}
          onChange={onChange}
          placeholder={config.label}
          isMulti={config.multiple || false}
        />
      );
    
    case 'range':
      return (
        <RangeSlider
          min={opcoes[config.campo].min}
          max={opcoes[config.campo].max}
          step={opcoes[config.campo].step}
          value={valor}
          onChange={onChange}
          label={config.label}
        />
      );
    
    case 'date_range':
      return (
        <DateRangePicker
          value={valor}
          onChange={onChange}
          label={config.label}
        />
      );
    
    default:
      return null;
  }
};
```

## 🎯 Resumo dos Campos Principais

### Filtros Essenciais para Comercial
1. **origem_lead**: De onde veio o cliente
2. **categoria_venda**: Tipo de produto/serviço
3. **valor_orcamento**: Faixa de valor
4. **probabilidade_fechamento**: Chance de sucesso
5. **estagio_negocio**: Fase do funil de vendas
6. **segmento_cliente**: Tamanho do cliente
7. **data_fechamento_prevista**: Previsão de fechamento

### Campos para Análise
1. **valor_proposta**: Valor real enviado
2. **quantidade_followups**: Número de contatos
3. **motivo_perda**: Análise de perdas
4. **tags_comerciais**: Classificação customizada

Essa estrutura permite filtragens potentes e visualizações personalizadas para cada etapa do fluxo comercial, mantendo flexibilidade e performance.