from typing import List, Literal

from pydantic import BaseModel, Field

# Definir os tipos Literal como aliases de tipo
IntentType = Literal[
    # Comunicação básica
    "saudacao",
    "despedida",
    "agradecimento",
    # Busca de informação
    "pergunta",
    "esclarecimento",
    "consulta",
    # Ações comerciais
    "solicitacao_servico",
    "cotacao",
    "pedido",
    "cancelamento",
    # Feedback e suporte
    "reclamacao",
    "elogio",
    "sugestao",
    "relato_problema",
    # Confirmações e validações
    "confirmacao",
    "negacao",
    "aceitacao",
    # Informações fornecidas
    "apresentacao",
    "informacao",
    "instrucao",
    # Urgência e priorização
    "urgente",
    "agendamento",
    "acompanhamento",
    # Controle de atendimento
    "transferir_humano",
    "escalar_supervisor",
    "pausar_atendimento",
    "finalizar_atendimento",
    # Autenticação e segurança
    "login",
    "validar_identidade",
    "reset_senha",
    "recuperar_acesso",
    # Gerenciamento de dados
    "atualizar_dados",
    "excluir_dados",
    "consultar_historico",
    "exportar_dados",
]

EntityType = Literal[
    # Identificação pessoal
    "cliente",
    "contato",
    "email",
    "telefone",
    # Produtos e serviços
    "tipo_produto",
    "produto",
    "servico",
    "marca",
    # Quantidades e medidas
    "quantidade",
    "preco",
    "desconto",
    # Tempo e localização
    "prazo",
    "data",
    "horario",
    "local",
    "cidade",
    # Características técnicas
    "cor",
    "tamanho",
    "material",
    "modelo",
    # Identificadores de sistema
    "numero_protocolo",
    "id_pedido",
    "codigo_cliente",
    "numero_ticket",
    "codigo_produto",
    # Documentos e identificação
    "cpf",
    "cnpj",
    "rg",
    "numero_conta",
    "codigo_transacao",
    # Dados financeiros
    "forma_pagamento",
    "numero_parcelas",
    "vencimento",
    "valor_total",
    "juros",
    # Status e estados
    "status_pedido",
    "situacao_cliente",
    "nivel_prioridade",
    "tipo_cliente",
    "canal_origem",
    # Dados de entrega/logística
    "cep",
    "endereco",
    "transportadora",
    "codigo_rastreamento",
    # Informações técnicas/suporte
    "versao_sistema",
    "codigo_erro",
    "categoria_problema",
    "departamento",
]


class IntentItem(BaseModel):
    type: IntentType
    value: str


class EntityItem(BaseModel):
    type: EntityType
    value: str


class PydanticModel(BaseModel):
    """
    Analise a mensagem do cliente e extraia intents e entities relevantes.

    INSTRUÇÕES PARA ANÁLISE:
    1. INTENTS (intenções do usuário) - SEMPRE identifique pelo menos uma:

       COMUNICAÇÃO BÁSICA:
       - saudacao: cumprimentos e apresentações
       - despedida: finalizações de conversa
       - agradecimento: expressões de gratidão

       BUSCA DE INFORMAÇÃO:
       - pergunta: solicitações de informação
       - esclarecimento: pedidos de clarificação
       - consulta: verificações de status ou disponibilidade

       AÇÕES COMERCIAIS:
       - solicitacao_servico: pedidos de serviços ou produtos
       - cotacao: solicitações de orçamento ou preço
       - pedido: ordens de compra ou contratação
       - cancelamento: solicitações de cancelamento

       FEEDBACK E SUPORTE:
       - reclamacao: queixas ou problemas
       - elogio: comentários positivos ou satisfação
       - sugestao: propostas de melhoria
       - relato_problema: descrição de dificuldades técnicas

       CONFIRMAÇÕES E VALIDAÇÕES:
       - confirmacao: confirmações de ações ou informações
       - negacao: recusas ou negativas
       - aceitacao: concordâncias ou aprovações

       INFORMAÇÕES FORNECIDAS:
       - apresentacao: ato de se identificar ou apresentar (frases como "meu nome é...", "eu sou...")
       - informacao: dados ou detalhes fornecidos sobre produtos, serviços, situações
       - instrucao: orientações ou direcionamentos

       URGÊNCIA E PRIORIZAÇÃO:
       - urgente: solicitações com alta prioridade
       - agendamento: marcação de compromissos ou reuniões
       - acompanhamento: verificação de andamento de processos

       CONTROLE DE ATENDIMENTO:
       - transferir_humano: solicitações para falar com atendente
       - escalar_supervisor: pedidos para falar com supervisor
       - pausar_atendimento: pausar o atendimento temporariamente
       - finalizar_atendimento: encerrar o atendimento

       AUTENTICAÇÃO E SEGURANÇA:
       - login: tentativas de acesso ao sistema
       - validar_identidade: verificações de identidade
       - reset_senha: solicitações de redefinição de senha
       - recuperar_acesso: recuperação de acesso ao sistema

       GERENCIAMENTO DE DADOS:
       - atualizar_dados: atualização de informações
       - excluir_dados: exclusão de informações
       - consultar_historico: consulta ao histórico
       - exportar_dados: exportação de dados

    2. ENTITIES (informações específicas) - extraia quando presentes:
       IDENTIFICAÇÃO PESSOAL:
       - cliente: SEMPRE extraia nomes próprios de pessoas mencionados na mensagem ("Paulo", "Maria", "João", "Sr. Silva")
       - contato: informações de contato geral (empresas, organizações)
       - email: endereços de email
       - telefone: números de telefone

       PRODUTOS E SERVIÇOS:
       - tipo_produto: categoria ou tipo de produto
       - produto: nome específico do produto
       - servico: tipo de serviço solicitado
       - marca: marca ou fabricante

       QUANTIDADES E MEDIDAS:
       - quantidade: número ou volume de itens
       - preco: valor monetário ou orçamento
       - desconto: percentual ou valor de desconto

       TEMPO E LOCALIZAÇÃO:
       - prazo: período ou data limite
       - data: data específica
       - horario: horário específico
       - local: endereço ou localização
       - cidade: nome da cidade

       CARACTERÍSTICAS TÉCNICAS:
       - cor: cor do produto
       - tamanho: dimensões ou tamanho
       - material: tipo de material
       - modelo: modelo específico

       IDENTIFICADORES DE SISTEMA:
       - numero_protocolo: número de protocolo de atendimento
       - id_pedido: identificador do pedido
       - codigo_cliente: código de identificação do cliente
       - numero_ticket: número do ticket de suporte
       - codigo_produto: código do produto

       DOCUMENTOS E IDENTIFICAÇÃO:
       - cpf: CPF do cliente
       - cnpj: CNPJ da empresa
       - rg: RG do cliente
       - numero_conta: número da conta
       - codigo_transacao: código da transação

       DADOS FINANCEIROS:
       - forma_pagamento: meio de pagamento
       - numero_parcelas: quantidade de parcelas
       - vencimento: data de vencimento
       - valor_total: valor total da transação
       - juros: taxa de juros

       STATUS E ESTADOS:
       - status_pedido: situação atual do pedido
       - situacao_cliente: status do cliente
       - nivel_prioridade: nível de prioridade do atendimento
       - tipo_cliente: categoria do cliente
       - canal_origem: canal de origem do contato

       DADOS DE ENTREGA/LOGÍSTICA:
       - cep: código postal
       - endereco: endereço completo
       - transportadora: empresa de transporte
       - codigo_rastreamento: código de rastreamento

       INFORMAÇÕES TÉCNICAS/SUPORTE:
       - versao_sistema: versão do sistema
       - codigo_erro: código de erro
       - categoria_problema: categoria do problema
       - departamento: departamento responsável

    EXEMPLO 1: "Olá, tudo bem? meu nome é Paulo"
    - intent: [
        {"type": "saudacao", "value": "Olá, tudo bem?"},
        {"type": "apresentacao", "value": "meu nome é Paulo"}
      ]
    - entities: [
        {"type": "cliente", "value": "Paulo"}
      ]

    EXEMPLO 2: "Oi! Meu CPF é 123.456.789-00. Preciso urgentemente falar com supervisor sobre o pedido #PED123 que está atrasado. Paguei R$ 1.500 no cartão em 3x mas não recebi ainda"
    - intent: [
        {"type": "saudacao", "value": "Oi!"},
        {"type": "escalar_supervisor", "value": "falar com supervisor"},
        {"type": "reclamacao", "value": "está atrasado"},
        {"type": "urgente", "value": "urgentemente"},
        {"type": "consulta", "value": "não recebi ainda"}
      ]
    - entities: [
        {"type": "cpf", "value": "123.456.789-00"},
        {"type": "id_pedido", "value": "PED123"},
        {"type": "valor_total", "value": "R$ 1.500"},
        {"type": "forma_pagamento", "value": "cartão"},
        {"type": "numero_parcelas", "value": "3x"},
        {"type": "status_pedido", "value": "atrasado"}
      ]

    REGRA IMPORTANTE:
    - SEMPRE extraia nomes próprios como entidade "cliente", mesmo quando a pessoa se apresenta
    - A intenção "apresentacao" captura o ATO de se apresentar
    - A entidade "cliente" captura o NOME mencionado
    - Ambos podem coexistir na mesma mensagem

    IMPORTANTE: NUNCA retorne listas vazias. Sempre identifique pelo menos uma intenção.
    """
    intent: List[IntentItem] = Field(
        default_factory=list,
        description="Lista de intenções extraídas da mensagem - NUNCA vazia"
    )
    entities: List[EntityItem] = Field(
        default_factory=list,
        description="Lista de entidades extraídas da mensagem"
    )

    def add_intent(self, tipo: IntentType, conteudo: str) -> None:
        self.intent.append(IntentItem(type=tipo, value=conteudo))

    def add_entity(self, tipo: EntityType, valor: str) -> None:
        self.entities.append(EntityItem(type=tipo, value=valor))

    def get_intents_by_type(self, tipo: IntentType) -> List[str]:
        return [item.value for item in self.intent if item.type == tipo]

    def get_entities_by_type(self, tipo: EntityType) -> List[str]:
        return [item.value for item in self.entities if item.type == tipo]
