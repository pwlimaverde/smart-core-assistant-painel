"""Fábrica para criar dinamicamente modelos Pydantic para análise de mensagens.

Este módulo contém a lógica para gerar uma classe Pydantic dinamicamente
com base em configurações JSON de tipos de intenção e entidade, que é usada
para estruturar a saída de um modelo de linguagem.

Classes:
    PydanticModelFactory: A fábrica principal para criar o modelo Pydantic.

Funções:
    create_dynamic_pydantic_model: Uma função utilitária para invocar a fábrica.
"""
import json
from typing import List, Type

from pydantic import BaseModel, Field


class PydanticModelFactory:
    """Fábrica para criar dinamicamente a classe PydanticModel.

    Baseado em configurações JSON de `intent_types` e `entity_types`.
    """

    @staticmethod
    def _extract_types_from_json(types_json: str) -> List[str]:
        """Extrai os tipos individuais de um JSON de configuração.

        Args:
            types_json (str): String JSON com a estrutura de tipos.

        Returns:
            List[str]: Uma lista com todos os tipos disponíveis.
        """
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return []

        types_list: List[str] = []
        if "intent_types" in data:
            data = data["intent_types"]
        elif "entity_types" in data:
            data = data["entity_types"]

        for category_dict in data.values():
            types_list.extend(category_dict.keys())

        return types_list

    @staticmethod
    def _generate_documentation_section(types_json: str, section_title: str) -> str:
        """Gera uma seção da documentação baseada no JSON de configuração.

        Args:
            types_json (str): String JSON com a estrutura de tipos.
            section_title (str): O título da seção (ex: "1. INTENTS").

        Returns:
            str: Uma string formatada com a documentação da seção.
        """
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return f"       {section_title}: Erro ao processar configuração\n"

        documentation = f"    {section_title}:\n"
        if "intent_types" in data:
            data = data["intent_types"]
        elif "entity_types" in data:
            data = data["entity_types"]

        for category_key, category_dict in data.items():
            category_title = category_key.replace("_", " ").upper()
            documentation += f"       {category_title}:\n"
            for type_key, description in category_dict.items():
                documentation += f"       - {type_key}: {description}\n"
            documentation += "\n"

        return documentation

    @staticmethod
    def _generate_fixed_entities_section() -> str:
        """Gera a seção de entidades fixas para a documentação.

        Returns:
            str: Uma string formatada com as entidades fixas.
        """
        return """
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

    @staticmethod
    def _generate_examples_section(
        intent_types_json: str, entity_types_json: str
    ) -> str:
        """Gera a seção de exemplos da documentação.

        Args:
            intent_types_json (str): JSON com tipos de intenção.
            entity_types_json (str): JSON com tipos de entidade.

        Returns:
            str: Uma string formatada com exemplos.
        """
        return """
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
    """

    @classmethod
    def create_pydantic_model(
        cls, intent_types_json: str, entity_types_json: str
    ) -> Type[BaseModel]:
        """Cria dinamicamente uma classe PydanticModel baseada nas configurações JSON.

        Args:
            intent_types_json (str): JSON com os tipos de intenção.
            entity_types_json (str): JSON com os tipos de entidade.

        Returns:
            Type[BaseModel]: A classe PydanticModel gerada dinamicamente.
        """
        intent_docs = cls._generate_documentation_section(
            intent_types_json, "1. INTENTS (intenções do usuário)"
        )
        entity_docs = cls._generate_documentation_section(
            entity_types_json, "2. ENTITIES DINÂMICAS (informações específicas)"
        )
        fixed_entities_docs = cls._generate_fixed_entities_section()
        examples_docs = cls._generate_examples_section(
            intent_types_json, entity_types_json
        )

        full_documentation = f"""Analise a mensagem do contato e extraia intents e entities.
{intent_docs}{entity_docs}{fixed_entities_docs}{examples_docs}
        """

        class IntentItem(BaseModel):
            """Representa uma intenção extraída."""
            type: str
            value: str

        class EntityItem(BaseModel):
            """Representa uma entidade extraída."""
            type: str
            value: str

        class PydanticModel(BaseModel):
            """Modelo para estruturar a análise de intenções e entidades."""
            __doc__ = full_documentation.strip()

            intent: List[IntentItem] = Field(default_factory=list)
            entities: List[EntityItem] = Field(default_factory=list)

            def add_intent(self, tipo: str, conteudo: str) -> None:
                """Adiciona uma intenção à lista."""
                self.intent.append(IntentItem(type=tipo, value=conteudo))

            def add_entity(self, tipo: str, valor: str) -> None:
                """Adiciona uma entidade à lista."""
                self.entities.append(EntityItem(type=tipo, value=valor))

        return PydanticModel


def create_dynamic_pydantic_model(
    intent_types_json: str, entity_types_json: str
) -> Type[BaseModel]:
    """Função utilitária para criar uma PydanticModel dinâmica.

    Args:
        intent_types_json (str): JSON com os tipos de intenção.
        entity_types_json (str): JSON com os tipos de entidade.

    Returns:
        Type[BaseModel]: A classe PydanticModel gerada dinamicamente.
    """
    return PydanticModelFactory.create_pydantic_model(
        intent_types_json, entity_types_json
    )
