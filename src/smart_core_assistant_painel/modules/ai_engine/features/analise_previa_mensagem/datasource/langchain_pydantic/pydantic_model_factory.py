'''Fábrica para criar dinamicamente modelos Pydantic para análise de mensagens.

Este módulo contém a lógica para gerar uma classe Pydantic dinamicamente
com base em configurações JSON de tipos de intenção e entidade, que é usada
para estruturar a saída de um modelo de linguagem.

Classes:
    PydanticModelFactory: A fábrica principal para criar o modelo Pydantic.

Funções:
    create_dynamic_pydantic_model: Uma função utilitária para invocar a fábrica.
'''

import json
from enum import Enum
from typing import Type

from pydantic import BaseModel, Field, field_validator


class PydanticModelFactory:
    '''Fábrica para criar dinamicamente a classe PydanticModel.

    Baseado em configurações JSON de `intent_types` e `entity_types`.
    '''

    @staticmethod
    def _extract_types_from_json(types_json: str) -> list[str]:
        '''Extrai os tipos individuais de um JSON de configuração.

        Args:
            types_json (str): String JSON com a estrutura de tipos.

        Returns:
            list[str]: Uma lista com todos os tipos disponíveis.
        '''
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return []

        types_list: list[str] = []
        if 'intent_types' in data:
            data = data['intent_types']
        elif 'entity_types' in data:
            data = data['entity_types']

        for category_dict in data.values():
            types_list.extend(category_dict.keys())

        return types_list

    @staticmethod
    def _sanitize_enum_name(value: str) -> str:
        '''Sanitiza a string para ser usada como nome de membro Enum.

        - Converte para maiúsculas
        - Substitui caracteres não alfanuméricos por underscore
        '''
        result = []
        for ch in value.upper():
            if ch.isalnum():
                result.append(ch)
            else:
                result.append('_')
        name = ''.join(result)
        # Evita começar com dígito
        if name and name[0].isdigit():
            name = f'T_{name}'
        return name or 'UNKNOWN'

    @classmethod
    def _make_enum(cls, name: str, values: list[str]) -> Type[Enum]:
        '''Cria dinamicamente uma Enum com valores fornecidos.

        Args:
            name (str): Nome da Enum a ser criada.
            values (list[str]): Lista de valores permitidos.

        Returns:
            Type[Enum]: Classe Enum gerada dinamicamente.
        '''
        if not values:
            # Fallback para uma enum genérica com um valor livre
            return Enum(name, {'ANY': '__any__'})

        mapping: dict[str, str] = {}
        for v in values:
            mapping[cls._sanitize_enum_name(v)] = v
        return Enum(name, mapping)

    @staticmethod
    def _generate_documentation_section(
        types_json: str, section_title: str
    ) -> str:
        '''Gera uma seção da documentação baseada no JSON de configuração.

        Args:
            types_json (str): String JSON com a estrutura de tipos.
            section_title (str): O título da seção (ex: '1. INTENTS').

        Returns:
            str: Uma string formatada com a documentação da seção.
        '''
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return f'       {section_title}: Erro ao processar configuração\n'

        documentation = f'    {section_title}:\n'
        # Lista oficial de tipos (resumo no topo da seção)
        allowed_types: list[str] = []

        if 'intent_types' in data:
            data = data['intent_types']
        elif 'entity_types' in data:
            data = data['entity_types']

        for category_key, category_dict in data.items():
            allowed_types.extend(list(category_dict.keys()))

        if allowed_types:
            documentation += '       LISTA OFICIAL DE TYPES PERMITIDOS:\n'
            for t in allowed_types:
                documentation += f'       - {t}\n'
            documentation += '\n'

        # Descrição detalhada por categoria e type
        for category_key, category_dict in data.items():
            category_title = category_key.replace('_', ' ').upper()
            documentation += f'       {category_title}:\n'
            for type_key, description in category_dict.items():
                documentation += f'       - {type_key}: {description}\n'
            documentation += '\n'

        return documentation

    @staticmethod
    def _generate_fixed_entities_section() -> str:
        '''Gera a seção de entidades fixas para a documentação.

        Returns:
            str: Uma string formatada com as entidades fixas.
        '''
        return '''
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
       - tags_atendimento: lista de tags ou palavras-chave que categorizam o atendimento, extraídas da conversa, exemplo: ["orcamento", "urgente"]
       - avaliacao_atendimento: Avaliação numérica do atendimento, variando de 1 (pior) até 5 (melhor), conforme opinião do contato, exemplo: 4
       - feedback_atendimento: Comentário qualitativo ou crítica fornecida pelo contato sobre o atendimento recebido, exemplo: Atendimento muito bom e rápido
        '''

    @staticmethod
    def _extract_examples_from_description(description: str) -> list[str]:
        '''Extrai exemplos de uma descrição de type com a seção 'Exemplos:'.

        Apenas linhas que sucedem 'Exemplos:' e começam com '-' serão consideradas.
        A extração para quando encontra uma linha vazia ou uma linha que não começa com '-'.
        '''
        examples: list[str] = []
        if not description:
            return examples
        lines = description.splitlines()
        inside = False
        for raw in lines:
            line = raw.strip()
            if not inside:
                if line.startswith('Exemplos:'):
                    inside = True
                continue
            # Estamos dentro da seção de exemplos
            if not line:
                break
            if line.startswith('-'):
                ex = line.lstrip('-').strip()
                if ex:
                    examples.append(ex)
            else:
                break
        return examples

    @staticmethod
    def _generate_examples_section(
        intent_types_json: str, entity_types_json: str
    ) -> str:
        '''Gera a seção de exemplos da documentação.

        Args:
            intent_types_json (str): JSON com tipos de intenção.
            entity_types_json (str): JSON com tipos de entidade.

        Returns:
            str: Uma string formatada com exemplos coerentes com os types permitidos.
        '''
        # Monta exemplos exclusivamente a partir das descrições dos intents (seção 'Exemplos:')
        try:
            intents_data = json.loads(intent_types_json)
        except json.JSONDecodeError:
            intents_data = {}

        if 'intent_types' in intents_data:
            intents_data = intents_data['intent_types']

        examples_lines: list[str] = ["    EXEMPLOS DE ANÁLISE:\n"]
        example_idx: int = 1

        # Percorre categorias e types, coletando até 1 exemplo por intent para evitar verbosidade
        for _category_key, category_dict in (intents_data or {}).items():
            for type_key, description in category_dict.items():
                extracted = PydanticModelFactory._extract_examples_from_description(str(description))
                if not extracted:
                    continue
                # Usa apenas o primeiro exemplo para compor um caso simples
                ex_text = extracted[0]
                examples_lines.append(
                    f"\n    EXEMPLO {example_idx}: '{ex_text}'\n"
                    "    - intent: [\n"
                    f"        {{'type': '{type_key}', 'value': '{ex_text}'}}\n"
                    "      ]\n"
                    "    - entities: []\n"
                )
                example_idx += 1

        # Regras gerais de extração
        examples_lines.append(
            "\n    REGRAS IMPORTANTES:\n"
            "    - Dê prioridade a atribuir intents quando houver correspondência clara com os types permitidos.\n"
            "    - Extraia apenas informações explícitas no texto, sem inferências.\n"
            "    - Mantenha o texto original encontrado como value, sem reescrever.\n"
            "    - Se realmente nada for encontrado para intent ou entities, retorne listas vazias.\n"
        )

        return "\n".join(examples_lines)

    @staticmethod
    def _generate_strict_rules_section(
        allowed_intents: list[str], allowed_entities: list[str]
    ) -> str:
        '''Gera uma seção curta com regras obrigatórias para a LLM.

        Essa seção enfatiza a escolha estrita dos types válidos.
        '''
        rules = [
            'USE EXATAMENTE UM DOS TYPES LISTADOS COMO VÁLIDOS.',
            'NÃO invente novos types. Se não houver um type aplicável, deixe a lista vazia.',
            'Pode haver múltiplos intents e múltiplas entities na mesma mensagem.',
            'Priorize intents quando a mensagem contiver exatamente o nome de um intent permitido.',
            'Use o histórico do atendimento SOMENTE como critério de desempate quando houver ambiguidade.',
            'Os campos "type" devem corresponder exatamente a um dos valores permitidos (case-sensitive).',
            'Formato de saída: intent e entities são listas de objetos {type, value}.',
        ]

        text = '    REGRAS OBRIGATÓRIAS:\n'
        for r in rules:
            text += f'    - {r}\n'

        # Acrescenta listas resumidas de types validos (reforço)
        if allowed_intents:
            text += '\n    INTENTS PERMITIDAS (valores exatos):\n'
            for t in allowed_intents:
                text += f'    - {t}\n'
        if allowed_entities:
            text += '\n    ENTITIES DINÂMICAS PERMITIDAS (valores exatos):\n'
            for t in allowed_entities:
                text += f'    - {t}\n'

        text += '\n'
        return text

    @staticmethod
    def _generate_keyword_policy_section(intent_types_json: str) -> str:
        '''Gera a seção de decisão por palavras-chave baseada nos exemplos do JSON.

        Para cada intent com exemplos declarados, lista os exemplos como guia.
        '''
        header = '    POLÍTICA DE DECISÃO POR PALAVRAS-CHAVE (guia rápido):\n'
        lines: list[str] = []
        try:
            intents_data = json.loads(intent_types_json)
        except json.JSONDecodeError:
            intents_data = {}
        if 'intent_types' in (intents_data or {}):
            intents_data = intents_data['intent_types']

        for _category_key, category_dict in (intents_data or {}).items():
            for type_key, description in category_dict.items():
                exs = PydanticModelFactory._extract_examples_from_description(str(description))
                if not exs:
                    continue
                snippet = '; '.join(f"'{e}'" for e in exs[:3])
                lines.append(
                    f"    - {type_key}: Exemplos: {snippet}.\n"
                )

        return header + (''.join(lines)) + '\n'

    @classmethod
    def create_pydantic_model(
        cls, intent_types_json: str, entity_types_json: str
    ) -> Type[BaseModel]:
        '''Cria dinamicamente uma classe PydanticModel baseada nas configurações JSON.

        Args:
            intent_types_json (str): JSON com os tipos de intenção.
            entity_types_json (str): JSON com os tipos de entidade.

        Returns:
            Type[BaseModel]: A classe PydanticModel gerada dinamicamente.
        '''
        # Extrai listas de types válidos
        intent_types = cls._extract_types_from_json(intent_types_json)
        entity_types = cls._extract_types_from_json(entity_types_json)

        # Gera documentação detalhada
        intent_docs = cls._generate_documentation_section(
            intent_types_json, '1. INTENTS (intenções do usuário)'
        )
        entity_docs = cls._generate_documentation_section(
            entity_types_json,
            '2. ENTITIES DINÂMICAS (informações específicas)',
        )
        strict_rules = cls._generate_strict_rules_section(
            intent_types, entity_types
        )
        fixed_entities_docs = cls._generate_fixed_entities_section()
        examples_docs = cls._generate_examples_section(
            intent_types_json, entity_types_json
        )

        # Seção de decisão por palavras-chave derivada dos exemplos do JSON
        keyword_section = cls._generate_keyword_policy_section(intent_types_json)

        full_documentation = f'''Analise a mensagem do contato e extraia intents e entities.
{strict_rules}{keyword_section}{intent_docs}{entity_docs}{fixed_entities_docs}{examples_docs}
        '''

        # Coleções de validação (mantidas como strings para alinhar com os testes)
        allowed_intents_set = set(intent_types)
        allowed_entities_set = set(entity_types)

        class IntentItem(BaseModel):
            '''Representa uma intenção extraída.

            O campo 'type' aceita SOMENTE valores da lista oficial de intents.
            '''

            type: str
            value: str

            # Validador para garantir que o 'type' é permitido
            @field_validator('type')
            def validate_type(cls, v: str) -> str:  # noqa: D401
                # Validação explícita contra a lista de intents permitidas
                if allowed_intents_set and v not in allowed_intents_set:
                    raise ValueError(
                        'type inválido para intent; use um dos valores '
                        'permitidos.'
                    )
                return v

        class EntityItem(BaseModel):
            '''Representa uma entidade extraída.

            O campo 'type' aceita SOMENTE valores da lista oficial de entities.
            '''

            type: str
            value: str

            @field_validator('type')
            def validate_type(cls, v: str) -> str:  # noqa: D401
                if allowed_entities_set and v not in allowed_entities_set:
                    raise ValueError(
                        'type inválido para entity; use um dos valores '
                        'permitidos.'
                    )
                return v

        class PydanticModel(BaseModel):
            '''Modelo para estruturar a análise de intenções e entidades.'''

            __doc__ = full_documentation.strip()

            intent: list[IntentItem] = Field(default_factory=list)
            entities: list[EntityItem] = Field(default_factory=list)

            def add_intent(self, tipo: str, conteudo: str) -> None:
                '''Adiciona uma intenção à lista.

                Observação: Esta função aceita string e valida contra a lista
                de intents permitidas via Pydantic.
                '''
                # A validação é aplicada ao instanciar IntentItem
                self.intent.append(IntentItem(type=tipo, value=conteudo))

            def add_entity(self, tipo: str, valor: str) -> None:
                '''Adiciona uma entidade à lista.

                Observação: Esta função aceita string e valida contra a lista
                de entities permitidas via Pydantic.
                '''
                self.entities.append(EntityItem(type=tipo, value=valor))

            def get_intents_by_type(self, tipo: str) -> list[str]:
                '''Retorna valores das intents filtradas por tipo.

                Esta função percorre a lista de intents e retorna somente os
                valores (campo 'value') cujo tipo (campo 'type') corresponde
                ao parâmetro informado.
                '''
                return [item.value for item in self.intent if item.type == tipo]

            def get_entities_by_type(self, tipo: str) -> list[str]:
                '''Retorna valores das entities filtradas por tipo.

                Percorre a lista de entities e retorna os valores ('value')
                cujo tipo ('type') seja igual ao parâmetro fornecido.
                '''
                return [
                    item.value for item in self.entities if item.type == tipo
                ]

        return PydanticModel


def create_dynamic_pydantic_model(
    intent_types_json: str, entity_types_json: str
) -> Type[BaseModel]:
    '''Função utilitária para criar uma PydanticModel dinâmica.

    Args:
        intent_types_json (str): JSON com os tipos de intenção.
        entity_types_json (str): JSON com os tipos de entidade.

    Returns:
        Type[BaseModel]: A classe PydanticModel gerada dinamicamente.
    '''
    return PydanticModelFactory.create_pydantic_model(
        intent_types_json, entity_types_json
    )
