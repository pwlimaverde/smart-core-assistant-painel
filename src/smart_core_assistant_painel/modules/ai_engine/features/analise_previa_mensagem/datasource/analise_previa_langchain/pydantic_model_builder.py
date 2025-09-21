from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel, Field

try:
    # Literal está disponível no typing padrão
    from typing import Literal  # type: ignore
except Exception:  # pragma: no cover
    # Fallback defensivo (não esperado neste projeto)
    Literal = None  # type: ignore


def _get_fixed_entity_types() -> set[str]:
    """Retorna o conjunto de entidades fixas aceitas pelo sistema.

    Estas entidades fazem parte da estrutura de tabelas internas e devem
    ser aceitas mesmo que não constem na configuração dinâmica.
    """
    return {
        "nome_contato",
        "cargo_contato",
        "departamento_contato",
        "email_contato",
        "rg_contato",
        "observacoes_contato",
        "tipo_cliente",
        "nome_fantasia_cliente",
        "razao_social_cliente",
        "cnpj_cliente",
        "cpf_cliente",
        "telefone_cliente",
        "site_cliente",
        "ramo_atividade_cliente",
        "observacoes_cliente",
        "cep_cliente",
        "logradouro_cliente",
        "numero_cliente",
        "complemento_cliente",
        "bairro_cliente",
        "cidade_cliente",
        "uf_cliente",
        "pais_cliente",
        "tags_atendimento",
        "avaliacao_atendimento",
        "feedback_atendimento",
    }


def _fixed_entities_doc_section() -> str:
    """Retorna a seção de documentação das entidades fixas.

    Esta seção orienta o LLM sobre os campos específicos que devem ser
    extraídos quando identificados na conversa.
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
   - bairro_cliente: Nome do bairro onde a empresa está localizado, conforme mencionado na conversa, exemplo: Bela Vista
   - cidade_cliente: Nome da cidade onde a empresa está sediada, conforme identificado na conversa, exemplo: São Paulo
   - uf_cliente: Sigla da unidade federativa (estado) da empresa informada na conversa, exemplo: SP
   - pais_cliente: Nome do país onde a empresa está localizada, conforme mencionado, exemplo: Brasil

   ATENDIMENTO:
   - tags_atendimento: lista de tags ou palavras-chave que categorizam o atendimento, extraídas da conversa, exemplo: [\"orcamento\", \"urgente\"]
   - avaliacao_atendimento: Avaliação numérica do atendimento, variando de 1 (pior) até 5 (melhor), conforme opinião do contato, exemplo: 4
   - feedback_atendimento: Comentário qualitativo ou crítica fornecida pelo contato sobre o atendimento recebido, exemplo: Atendimento muito bom e rápido
"""


def _extract_allowed_values(
    items_json: Optional[List[Dict[str, Any]]],
    key_name: str,
) -> Tuple[Tuple[str, ...], str]:
    """Extrai os valores permitidos (tipos) a partir do JSON de configuração.

    - Se não houver itens, retorna tupla vazia e uma descrição genérica.
    - A chave `key_name` será usada como rótulo na descrição.
    """
    if not items_json:
        return tuple(), (
            f"Lista de {key_name} permitidos não fornecida. Aceita string."
        )

    allowed: List[str] = []
    for item in items_json:
        # Aceita `type`, `label` ou `nome` como possíveis campos do tipo
        value = (
            item.get("type")
            or item.get("label")
            or item.get("nome")
            or item.get("name")
        )
        if not value:
            continue
        value_str = str(value).strip()
        if value_str and value_str not in allowed:
            allowed.append(value_str)

    if not allowed:
        return tuple(), (
            f"Lista de {key_name} permitidos vazia. Aceita string livre."
        )

    joined = ", ".join(f"'{v}'" for v in allowed)
    desc = f"{key_name.capitalize()} permitidos: {joined}."
    return tuple(allowed), desc


def _extract_examples(items_json: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """Gera exemplos de saída baseado no JSON de configuração.

    Cada exemplo tem formato: {"type": <tipo>, "value": <exemplo>}
    """
    examples: List[Dict[str, str]] = []
    if not items_json:
        return examples

    for item in items_json:
        t = (
            item.get("type")
            or item.get("label")
            or item.get("nome")
            or item.get("name")
        )
        # Busca exemplos em campos comuns
        raw_examples: Union[str, List[str], None] = (
            item.get("exemplos")
            or item.get("examples")
            or item.get("example")
            or item.get("amostras")
        )
        example_value = None
        if isinstance(raw_examples, list) and raw_examples:
            example_value = str(raw_examples[0])
        elif isinstance(raw_examples, str) and raw_examples.strip():
            example_value = raw_examples.strip()
        else:
            # fallback: usa descrição como valor de exemplo
            desc = (
                item.get("descricao")
                or item.get("description")
                or item.get("observacao")
                or item.get("obs")
                or ""
            )
            example_value = str(desc)[:60] if desc else "exemplo"

        if t:
            examples.append({"type": str(t), "value": str(example_value)})

    return examples


def _build_docstring(
    intent_json: Optional[List[Dict[str, Any]]],
    entity_json: Optional[List[Dict[str, Any]]],
) -> str:
    """Constrói docstring dinâmica com listas de intents e entidades.

    Essa docstring será usada como fallback para o prompt do sistema.
    """
    parts: List[str] = [
        "INSTRUÇÕES PARA EXTRAÇÃO DE INTENÇÕES E ENTIDADES:",
        "\n- A saída DEVE ser um JSON válido seguindo o schema descrito.",
        (
            "- Liste intents e entidades com pares {type, value} adequados "
            "ao conteúdo."
        ),
    ]

    if intent_json:
        parts.append("\nINTENTS DISPONÍVEIS:")
        for item in intent_json:
            name = (
                item.get("type")
                or item.get("label")
                or item.get("nome")
                or item.get("name")
                or "(sem-nome)"
            )
            desc = (
                item.get("descricao")
                or item.get("description")
                or ""
            )
            parts.append(f"- {name}: {desc}")

    if entity_json:
        parts.append("\nENTIDADES DISPONÍVEIS:")
        for item in entity_json:
            name = (
                item.get("type")
                or item.get("label")
                or item.get("nome")
                or item.get("name")
                or "(sem-nome)"
            )
            desc = (
                item.get("descricao")
                or item.get("description")
                or ""
            )
            parts.append(f"- {name}: {desc}")

    # Inclui seção de entidades fixas para orientar o LLM
    parts.append("\n" + _fixed_entities_doc_section())

    return "\n".join(parts)


def build_analise_previa_model(
    *,
    intent_types_json: Optional[List[Dict[str, Any]]],
    entity_types_json: Optional[List[Dict[str, Any]]],
) -> Type[BaseModel]:
    """Cria dinamicamente o modelo Pydantic usado como structured output.

    - Os campos usam descrições e exemplos derivados do JSON de configuração.
    - O campo `type` aceita apenas os valores válidos, via Literal.
    """
    # Intents: tipos e descrição
    intent_allowed, intent_desc = _extract_allowed_values(
        intent_types_json, "intents"
    )
    intent_examples = _extract_examples(intent_types_json)

    # Entities: tipos e descrição (inclui entidades fixas)
    entity_allowed, entity_desc = _extract_allowed_values(
        entity_types_json, "entidades"
    )
    fixed_entities = sorted(_get_fixed_entity_types())
    # União preservando a ordem original dos dinâmicos
    entity_allowed_set = set(entity_allowed)
    extended_entity_allowed_list: List[str] = list(entity_allowed)
    for ft in fixed_entities:
        if ft not in entity_allowed_set:
            extended_entity_allowed_list.append(ft)
    extended_entity_allowed = tuple(extended_entity_allowed_list)

    entity_examples = _extract_examples(entity_types_json)

    # Definição de tipos para campos `type`
    if intent_allowed and 'Literal' in globals() and Literal is not None:
        IntentType = Literal[intent_allowed]  # type: ignore
    else:
        IntentType = str  # type: ignore

    if extended_entity_allowed and 'Literal' in globals() and Literal is not None:
        EntityType = Literal[extended_entity_allowed]  # type: ignore
    else:
        EntityType = str  # type: ignore

    class IntentItem(BaseModel):
        """Par {type, value} representando uma intenção identificada."""

        # Comentários em português descrevendo a validação dinâmica
        type: Annotated[
            IntentType,  # type: ignore
            Field(
                description=intent_desc,
                examples=[e.get("type", "") for e in intent_examples] or [
                    "intent_exemplo"
                ],
            ),
        ]
        value: Annotated[
            str,
            Field(
                description=(
                    "Valor textual representando a intenção extraída do "
                    "conteúdo."
                ),
                examples=[e.get("value", "") for e in intent_examples]
                or ["quero cancelar meu plano"],
            ),
        ]

    class EntityItem(BaseModel):
        """Par {type, value} representando uma entidade identificada."""

        type: Annotated[
            EntityType,  # type: ignore
            Field(
                description=entity_desc,
                examples=[e.get("type", "") for e in entity_examples] or [
                    "cpf"
                ],
            ),
        ]
        value: Annotated[
            str,
            Field(
                description=(
                    "Valor textual da entidade encontrada no conteúdo "
                    "(normalizada quando aplicável)."
                ),
                examples=[e.get("value", "") for e in entity_examples]
                or ["123.456.789-00"],
            ),
        ]

    class AnalysisOutput(BaseModel):
        """Modelo de saída estruturada para análise prévia da mensagem."""

        intent: Annotated[
            List[IntentItem],
            Field(
                description=(
                    "Lista de intenções detectadas no conteúdo fornecido."
                ),
                examples=[intent_examples] if intent_examples else [
                    [{"type": "saudacao", "value": "olá"}]
                ],
            ),
        ]
        entities: Annotated[
            List[EntityItem],
            Field(
                description=(
                    "Lista de entidades extraídas a partir do conteúdo "
                    "analisado."
                ),
                examples=[entity_examples] if entity_examples else [
                    [{"type": "cpf", "value": "123.456.789-00"}]
                ],
            ),
        ]

    # Injeta docstring dinâmica como fallback de prompt
    AnalysisOutput.__doc__ = _build_docstring(
        intent_types_json, entity_types_json
    )

    # Expõe os conjuntos de valores permitidos para uso na normalização
    # em tempo de execução (antes da validação Pydantic).
    AnalysisOutput.__intent_allowed__ = intent_allowed  # type: ignore[attr-defined]
    AnalysisOutput.__entity_allowed__ = extended_entity_allowed  # type: ignore[attr-defined]

    return AnalysisOutput