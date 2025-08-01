import json
from typing import List, Type

from loguru import logger
from pydantic import BaseModel, Field


class PydanticModelFactory:
    """
    Factory para criar dinamicamente a classe PydanticModel baseada em
    configurações JSON de intent_types e entity_types.
    """

    @staticmethod
    def _extract_types_from_json(types_json: str) -> List[str]:
        """
        Extrai os tipos individuais de um JSON de configuração.

        Args:
            types_json: JSON string com a estrutura de tipos

        Returns:
            Lista com todos os tipos disponíveis
        """
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return []

        types_list: List[str] = []

        # Se há uma chave "intent_types" ou "entity_types", usar seus valores
        if "intent_types" in data:
            data = data["intent_types"]
        elif "entity_types" in data:
            data = data["entity_types"]

        for category_dict in data.values():
            if isinstance(category_dict, dict):
                types_list.extend(category_dict.keys())

        return types_list

    @staticmethod
    def _generate_documentation_section(types_json: str, section_title: str) -> str:
        """
        Gera uma seção da documentação baseada no JSON de configuração.

        Args:
            types_json: JSON string com a estrutura de tipos
            section_title: Título da seção (ex: "1. INTENTS", "2. ENTITIES")

        Returns:
            String formatada com a documentação da seção
        """
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return f"       {section_title}: Erro ao processar configuração\n"

        documentation = f"    {section_title}:\n"

        # Se há uma chave "intent_types" ou "entity_types", usar seus valores
        if "intent_types" in data:
            data = data["intent_types"]
        elif "entity_types" in data:
            data = data["entity_types"]

        for category_key, category_dict in data.items():
            if isinstance(category_dict, dict):
                # Converter category_key para formato de título
                category_title = category_key.replace("_", " ").upper()
                documentation += f"       {category_title}:\n"

                for type_key, description in category_dict.items():
                    documentation += f"       - {type_key}: {description}\n"

                documentation += "\n"

        return documentation

    @staticmethod
    def _generate_fixed_entities_section() -> str:
        """
        Gera a seção de entidades fixas para cadastro no banco de dados.

        Returns:
            String formatada com entidades fixas
        """
        fixed_entities = """
    3. ENTIDADES FIXAS (dados para cadastro no banco) - extraia quando identificadas claramente:
       CONTATO:
       - nome_contato: Nome completo da pessoa que participou da conversa e deve ser cadastrado como contato no sistema, exemplo: Ana Souza
       - cargo_contato: Cargo ou função profissional mencionada pelo contato durante a conversa, exemplo: Gerente de Projetos
       - departamento_contato: Departamento ou setor referente ao contato, conforme mencionado na conversa, exemplo: Financeiro
       - email_contato: Endereço de e-mail fornecido pelo contato na conversa, exemplo: ana.souza@email.com
       - rg_contato: Número do Registro Geral (RG) do contato informado na conversa, exemplo: MG-12.345.678
       - observacoes_contato: Informações adicionais ou comentários relevantes sobre o contato capturados durante a conversa, exemplo: Prefiro conversar à tarde

       CLIENTE:
       - tipo_cliente: Tipo de cliente identificado na conversa, podendo ser 'pessoa física' ou 'pessoa jurídica', exemplo: juridica
       - nome_fantasia_cliente: Nome comum ou comercial da empresa mencionado na conversa, usado para cadastro simplificado, exemplo: Microsoft
       - razao_social_cliente: Nome legal ou razão social oficial da empresa, se mencionado na conversa, exemplo: Microsoft Corporation
       - cnpj_cliente: Número do Cadastro Nacional de Pessoa Jurídica (CNPJ) informado na conversa, em formato válido, exemplo: 12.345.678/0001-99
       - cpf_cliente: Número do Cadastro de Pessoa Física (CPF) informado na conversa, em formato válido (utilizado quando o cliente for pessoa física), exemplo: 123.456.789-09
       - telefone_cliente: Número de telefone fixo ou corporativo da empresa informado na conversa, incluindo código de área, exemplo: (11) 3333-4444
       - site_cliente: Endereço do website ou URL oficial da empresa mencionada na conversa, exemplo: https://www.microsoft.com
       - ramo_atividade_cliente: Ramo de atividade ou setor em que a empresa atua, conforme citado durante a conversa, exemplo: Tecnologia da Informação
       - observacoes_cliente: Informações adicionais relevantes sobre a empresa capturadas durante a conversa, exemplo: Cliente desde 2020
       - cep_cliente: Código de Endereçamento Postal (CEP) do endereço da empresa informado na conversa, exemplo: 01234-567
       - logradouro_cliente: Nome da rua, avenida ou logradouro onde a empresa está situada, conforme informação na conversa, exemplo: Avenida Paulista
       - numero_cliente: Número do endereço da empresa informado na conversa, exemplo: 1000
       - complemento_cliente: Complemento do endereço, como sala, andar ou bloco, informado durante a conversa, exemplo: Sala 101
       - bairro_cliente: Nome do bairro onde a empresa está localizada, conforme mencionado na conversa, exemplo: Bela Vista
       - cidade_cliente: Nome da cidade onde a empresa está sediada, conforme identificado na conversa, exemplo: São Paulo
       - uf_cliente: Sigla da unidade federativa (estado) da empresa informada na conversa, exemplo: SP
       - pais_cliente: Nome do país onde a empresa está localizada, conforme mencionado, exemplo: Brasil

       ATENDIMENTO:
       - tags_atendimento: Lista de tags ou palavras-chave que categorizam o atendimento, extraídas da conversa, exemplo: ["orcamento", "urgente"]
       - avaliacao_atendimento: Avaliação numérica do atendimento, variando de 1 (pior) até 5 (melhor), conforme opinião do contato, exemplo: 4
       - feedback_atendimento: Comentário qualitativo ou crítica fornecida pelo contato sobre o atendimento recebido, exemplo: Atendimento muito bom e rápido

        """
        return fixed_entities

    @staticmethod
    def _generate_examples_section(
        intent_types_json: str, entity_types_json: str
    ) -> str:
        """
        Gera a seção de exemplos da documentação.

        Args:
            intent_types_json: JSON com tipos de intent
            entity_types_json: JSON com tipos de entity

        Returns:
            String formatada com exemplos
        """
        examples = """
    EXEMPLOS DE ANÁLISE:

    EXEMPLO 1: "Olá, tudo bem? meu nome é Paulo Silva, trabalho na Microsoft como Gerente de TI"
    - intent: [
        {"type": "saudacao", "value": "Olá, tudo bem?"},
        {"type": "apresentacao", "value": "meu nome é Paulo Silva, trabalho na Microsoft como Gerente de TI"}
      ]
    - entities: [
        {"type": "nome_contato", "value": "Paulo Silva"},
        {"type": "nome_fantasia_cliente", "value": "Microsoft"},
        {"type": "cargo_contato", "value": "Gerente de TI"},
        {"type": "tipo_cliente", "value": "pessoa jurídica"}
      ]

    EXEMPLO 2: "Oi! Meu CPF é 123.456.789-09. Preciso urgentemente falar com supervisor sobre o pedido #PED123 que está atrasado. Paguei R$ 1.500 no cartão em 3x mas não recebi ainda. Meu email é paulo@email.com"
    - intent: [
        {"type": "saudacao", "value": "Oi!"},
        {"type": "escalar_supervisor", "value": "falar com supervisor"},
        {"type": "reclamacao", "value": "está atrasado"},
        {"type": "urgente", "value": "urgentemente"},
        {"type": "consulta", "value": "não recebi ainda"}
      ]
    - entities: [
        {"type": "cpf_cliente", "value": "123.456.789-09"},
        {"type": "id_pedido", "value": "PED123"},
        {"type": "valor_total", "value": "R$ 1.500"},
        {"type": "forma_pagamento", "value": "cartão"},
        {"type": "numero_parcelas", "value": "3x"},
        {"type": "status_pedido", "value": "atrasado"},
        {"type": "email_contato", "value": "paulo@email.com"},
        {"type": "tipo_cliente", "value": "pessoa física"}
      ]

    EXEMPLO 3: "Isso mesmo" (sem contexto histórico suficiente)
    - intent: []
    - entities: []

    EXEMPLO 4: "Perfeito! Muito obrigado pelo atendimento, nota 5!"
    - intent: [
        {"type": "confirmacao", "value": "Perfeito!"},
        {"type": "agradecimento", "value": "Muito obrigado pelo atendimento"}
      ]
    - entities: [
        {"type": "avaliacao_atendimento", "value": "5"},
        {"type": "feedback_atendimento", "value": "Perfeito! Muito obrigado pelo atendimento"}
      ]

    EXEMPLO 5: "Empresa ABC Ltda, CNPJ 12.345.678/0001-99, situada na Av. Brasil, 1000 - Centro, São Paulo/SP, CEP 01000-000. Site: www.abc.com.br"
    - intent: [
        {"type": "informacao", "value": "dados da empresa"}
      ]
    - entities: [
        {"type": "razao_social_cliente", "value": "ABC Ltda"},
        {"type": "cnpj_cliente", "value": "12.345.678/0001-99"},
        {"type": "logradouro_cliente", "value": "Av. Brasil"},
        {"type": "numero_cliente", "value": "1000"},
        {"type": "bairro_cliente", "value": "Centro"},
        {"type": "cidade_cliente", "value": "São Paulo"},
        {"type": "uf_cliente", "value": "SP"},
        {"type": "cep_cliente", "value": "01000-000"},
        {"type": "site_cliente", "value": "www.abc.com.br"},
        {"type": "tipo_cliente", "value": "pessoa jurídica"}
      ]

    REGRAS IMPORTANTES:
    - PRIORIDADE: Sempre extraia dados para as ENTIDADES FIXAS quando identificadas (Contato, Cliente, Atendimento)
    - Combine entidades dinâmicas e fixas para máxima captura de informações
    - Use o histórico da conversa para resolver referências implícitas quando o contexto for claro
    - É PERFEITAMENTE NORMAL retornar listas vazias quando não há identificações claras
    - Seja conservador: prefira precisão a recall
    - Para dados de cadastro, seja mais liberal na extração desde que haja evidências claras
    - Distinga entre pessoa física e jurídica pelo contexto (CPF vs CNPJ, nome vs razão social)
        """
        return examples

    @classmethod
    def create_pydantic_model(
        cls, intent_types_json: str, entity_types_json: str
    ) -> Type[BaseModel]:
        """
        Cria dinamicamente uma classe PydanticModel baseada nas configurações JSON.

        Args:
            intent_types_json: JSON com os tipos de intent
            entity_types_json: JSON com os tipos de entity

        Returns:
            Classe PydanticModel gerada dinamicamente
        """
        # Gerar documentação dinamicamente
        intent_docs = cls._generate_documentation_section(
            intent_types_json,
            "1. INTENTS (intenções do usuário) - identifique quando presentes",
        )
        entity_docs = cls._generate_documentation_section(
            entity_types_json,
            "2. ENTITIES DINÂMICAS (informações específicas da conversa) - extraia quando presentes",
        )
        fixed_entities_docs = cls._generate_fixed_entities_section()
        examples_docs = cls._generate_examples_section(
            intent_types_json, entity_types_json
        )

        # Documentação completa
        full_documentation = f"""
    Analise a mensagem do contato considerando o histórico fornecido e extraia intents e entities relevantes.

    PRINCÍPIO FUNDAMENTAL: Seja conservador e preciso para entidades dinâmicas, mas mais liberal para dados de
    cadastro (ENTIDADES FIXAS) quando houver evidências claras. É perfeitamente normal retornar listas vazias
    quando não há identificações claras.

    INSTRUÇÕES PARA ANÁLISE:
{intent_docs}
{entity_docs}
{fixed_entities_docs}
{examples_docs}
        """

        # Log da documentação completa gerada
        logger.info("=== DOCUMENTAÇÃO PYDANTIC MODEL FACTORY ===")
        logger.info("Documentação completa gerada para análise de mensagens:")
        logger.info(f"\n{full_documentation.strip()}")
        logger.info("=" * 50)

        # Criar classes Item
        class IntentItem(BaseModel):
            type: str
            value: str

        class EntityItem(BaseModel):
            type: str
            value: str

        # Criar a classe PydanticModel dinamicamente
        class PydanticModel(BaseModel):
            __doc__ = full_documentation.strip()

            intent: List[IntentItem] = Field(
                default_factory=list,
                description="Lista de intenções extraídas da mensagem - pode ser vazia quando não identificadas claramente",
            )
            entities: List[EntityItem] = Field(
                default_factory=list,
                description="Lista de entidades extraídas da mensagem - pode ser vazia quando não identificadas",
            )

            def add_intent(self, tipo: str, conteudo: str) -> None:
                self.intent.append(IntentItem(type=tipo, value=conteudo))

            def add_entity(self, tipo: str, valor: str) -> None:
                self.entities.append(EntityItem(type=tipo, value=valor))

            def get_intents_by_type(self, tipo: str) -> List[str]:
                return [item.value for item in self.intent if item.type == tipo]

            def get_entities_by_type(self, tipo: str) -> List[str]:
                return [item.value for item in self.entities if item.type == tipo]

        return PydanticModel


def create_dynamic_pydantic_model(
    intent_types_json: str, entity_types_json: str
) -> Type[BaseModel]:
    """
    Função utilitária para criar uma PydanticModel dinâmica.

    Args:
        intent_types_json: JSON com os tipos de intent
        entity_types_json: JSON com os tipos de entity

    Returns:
        Classe PydanticModel gerada dinamicamente

    Example:
        >>> intent_json = '{"comunicacao_basica": {"saudacao": "cumprimentos"}}'
        >>> entity_json = '{"identificacao_pessoal": {"contato": "nome do contato"}}'
        >>> Model = create_dynamic_pydantic_model(intent_json, entity_json)
        >>> instance = Model(intent=[{"type": "saudacao", "value": "Olá"}], entities=[])
    """
    logger.info("🏭 CRIANDO PYDANTIC MODEL DINÂMICO...")
    logger.debug(f"Intent Types JSON recebido: {intent_types_json}")
    logger.debug(f"Entity Types JSON recebido: {entity_types_json}")

    model = PydanticModelFactory.create_pydantic_model(
        intent_types_json, entity_types_json
    )

    logger.success("✅ Pydantic Model dinâmico criado com sucesso!")
    return model
