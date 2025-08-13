from typing import Any, List, Optional, cast

from django.core.cache import cache
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.model.message_data import (
    MessageData,
)
from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB

from .models import (
    Atendimento,
    Contato,
    Mensagem,
    TipoRemetente,
    processar_mensagem_whatsapp,
)
from .signals import mensagem_bufferizada
from .wrapper_evolutionapi import SendMessage


def set_wa_buffer(message: MessageData) -> None:
    """
    Adiciona uma mensagem ao buffer existente de WhatsApp.

    Realiza validação de tipo e persiste SEMPRE a lista completa de
    mensagens no cache, evitando regressões de tipo.

    Args:
        message (MessageData): Mensagem para adicionar ao buffer

    Examples:
        >>> set_wa_buffer(new_message)
    """

    # Obtém buffer atual (lista) e acrescenta a nova mensagem
    cache_key = f"wa_buffer_{message.numero_telefone}"
    buffer = cache.get(cache_key, [])
    buffer.append(message)

    # Salva o buffer ATUALIZADO (lista) no cache
    timeout = SERVICEHUB.TIME_CACHE * 3
    cache.set(cache_key, buffer, timeout=timeout)


def clear_wa_buffer(phone: str) -> None:
    """
    Remove completamente o buffer de mensagens WhatsApp para um telefone.

    Args:
        phone (str): Número de telefone normalizado

    Examples:
        >>> clear_wa_buffer("5511999999999")
    """
    cache_key = f"wa_buffer_{phone}"
    timer_key = f"wa_timer_{phone}"

    # Remover tanto o buffer quanto o timer
    cache.delete(cache_key)
    cache.delete(timer_key)


def send_message_response(phone: str) -> None:
    # Obter buffer usando função robusta
    cache_key = f"wa_buffer_{phone}"
    message_data_list: List[MessageData] = cache.get(cache_key, [])

    if not message_data_list:
        logger.warning(
            f"[CACHE] Buffer vazio para {phone} - nenhuma mensagem para processar"
        )
        return

    try:
        message_data = _compile_message_data_list(message_data_list)

        mensagem_id = processar_mensagem_whatsapp(
            numero_telefone=message_data.numero_telefone,
            conteudo=message_data.conteudo,
            message_type=message_data.message_type,
            message_id=message_data.message_id,
            metadados=message_data.metadados,
            nome_perfil_whatsapp=message_data.nome_perfil_whatsapp,
            from_me=message_data.from_me,
        )

        # Validar se a mensagem foi realmente criada
        try:
            mensagem = Mensagem.objects.get(id=mensagem_id)
        except Mensagem.DoesNotExist:
            logger.error(f"Mensagem criada (ID: {mensagem_id}) não encontrada no banco")
            return

        # Analise previa do conteudo da mensagem por agente de IA, detectando
        # intent e extraindo entidades
        try:
            _analisar_conteudo_mensagem(mensagem_id)
        except Exception as e:
            logger.error(f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")

        # Verificação de direcionamento do atendimento
        try:
            atendimento_obj: Atendimento = cast(Atendimento, mensagem.atendimento)
            is_bot_responder = _pode_bot_responder_atendimento(atendimento_obj)
            if is_bot_responder:
                SendMessage().send_message(
                    instance=message_data.instance,
                    body={
                        "number": message_data.numero_telefone,
                        "text": (
                            "Obrigado pela sua mensagem, em breve um atendente "
                            "entrará em contato."
                        ),
                    },
                )
            else:
                logger.info(
                    f"Mensagem direcionada para atendente humano: {mensagem_id}"
                )

        except Exception as e:
            logger.error(
                f"Erro ao verificar direcionamento da mensagem {mensagem_id}: {e}"
            )

        # Limpar cache usando função robusta
        clear_wa_buffer(phone)

    except Exception as e:
        logger.error(f"Erro geral ao processar mensagens para {phone}: {e}")
        # Limpar cache mesmo em caso de erro para evitar reprocessamento
        clear_wa_buffer(phone)


def sched_message_response(phone: str) -> None:
    """
    Agenda o processamento da resposta via signal para execução no cluster.

    Esta função apenas emite um signal indicando que há mensagens
    bufferizadas para um determinado telefone. O agendamento real ocorre
    no receiver do signal, que cria uma Schedule (Django Q) do tipo ONCE
    para execução futura no cluster, respeitando um tempo de debounce
    configurado por SERVICEHUB.TIME_CACHE.
    """

    timer_key = f"wa_timer_{phone}"

    timer_exists = cache.get(timer_key)

    # Evita múltiplos agendamentos em janelas curtas usando um flag no cache
    if not timer_exists:
        # Define janela de proteção um pouco maior que o tempo de cache
        timeout_value = SERVICEHUB.TIME_CACHE * 2
        cache.set(timer_key, True, timeout=timeout_value)
        # Emite signal para que o handler crie a Schedule no cluster
        mensagem_bufferizada.send(sender="oraculo", phone=phone)


def _obter_entidades_metadados_validas() -> set[str]:
    """
    Obtém as entidades válidas para metadados do contato a partir do SERVICEHUB.

    Esta função extrai dinamicamente as entidades que devem ser armazenadas
    nos metadados do contato, baseando-se na configuração centralizada do sistema.
    Remove entidades que já são cadastradas automaticamente (contato, telefone).

    Returns:
        set[str]: Conjunto de entidades válidas para metadados

    Examples:
        >>> entidades = _obter_entidades_metadados_validas()
        >>> 'email' in entidades
        True
        >>> 'contato' in entidades  # Contato vai para o campo nome, não metadados
        False
    """
    try:
        # Obtém configuração de entidades válidas do SERVICEHUB
        valid_entity_types = SERVICEHUB.VALID_ENTITY_TYPES

        if not valid_entity_types:
            return set()

        # Parse do JSON das entidades válidas
        import json

        entidades_validas: set[str] = set()

        entidades_config = json.loads(valid_entity_types)

        # Extrai todas as entidades de todas as categorias
        if isinstance(entidades_config, dict) and "entity_types" in entidades_config:
            for _, entidades in entidades_config["entity_types"].items():
                if isinstance(entidades, dict):
                    entidades_validas.update(entidades.keys())

        # Remove entidades que não devem ir para metadados
        # Já cadastrado no recebimento da mensagem
        entidades_validas.discard("contato")
        entidades_validas.discard("telefone")

        return entidades_validas

    except Exception as e:
        logger.error(f"Erro ao obter entidades válidas do SERVICEHUB: {e}")
        return set()


def _processar_entidades_contato(
    mensagem: "Mensagem", entity_types: list[dict[str, Any]]
) -> None:
    """
    Processa entidades extraídas para atualizar dados do contato.

    Esta função analisa as entidades extraídas da mensagem e atualiza
    automaticamente os dados do contato conforme encontra informações relevantes.

    Comportamento:
    - Se encontra entidade "contato", atualiza o campo nome do contato (caso esteja vazio)
    - Para outras entidades com dados do contato (contato, email, cpf, etc.),
      salva nos metadados do contato
    - Se o nome do contato ainda não está salvo, pode ser solicitado via nova mensagem

    Args:
        mensagem (Mensagem): Instância da mensagem analisada
        entity_types (list[dict[str, Any]]): Lista de entidades extraídas
            Formato esperado: [{"tipo_entidade": "valor_extraido"}, ...]

    Returns:
        None: A função atualiza diretamente o contato no banco de dados

    Examples:
        >>> entity_types = [
        ...     {"contato": "João Silva"},
        ...     {"email": "joao@email.com"},
        ...     {"telefone": "(11) 99999-9999"}
        ... ]
        >>> _processar_entidades_contato(mensagem, entity_types)
        # Contato terá nome="João Silva" e metadados com email e telefone
    """
    try:
        atendimento = cast(Atendimento, mensagem.atendimento)
        contato = cast(Contato, atendimento.contato)
        contato_atualizado = False
        metadados_atualizados = False

        # Obter entidades válidas para metadados dinamicamente
        entidades_metadados = _obter_entidades_metadados_validas()

        for entidade_dict in entity_types:
            for tipo_entidade, valor in entidade_dict.items():
                # Processar entidade "contato" para atualizar nome
                if tipo_entidade.lower() == "nome_contato" and valor:
                    # Só atualiza nome se estiver vazio ou se novo nome for
                    # mais completo
                    if not contato.nome_contato or len(valor.strip()) > len(
                        contato.nome_contato or ""
                    ):
                        nome_limpo = valor.strip()
                        if nome_limpo and len(nome_limpo) >= 2:  # Validação básica
                            contato.nome_contato = nome_limpo
                            contato_atualizado = True

                # Processar outras entidades para metadados
                elif tipo_entidade.lower() in entidades_metadados and valor:
                    valor_limpo = valor.strip() if isinstance(valor, str) else valor
                    if valor_limpo:
                        # Atualizar metadados do contato
                        if not contato.metadados:
                            contato.metadados = {}

                        # Evitar duplicatas - só atualiza se não existe ou
                        # valor é diferente
                        if (
                            tipo_entidade.lower() not in contato.metadados
                            or contato.metadados[tipo_entidade.lower()] != valor_limpo
                        ):
                            contato.metadados[tipo_entidade.lower()] = valor_limpo
                            metadados_atualizados = True

        # Salvar contato se houve alterações
        if contato_atualizado or metadados_atualizados:
            update_fields = []
            if contato_atualizado:
                update_fields.append("nome_contato")
            if metadados_atualizados:
                update_fields.append("metadados")

            # Atualizar timestamp da última interação quando dados são
            # atualizados
            contato.ultima_interacao = timezone.now()
            update_fields.append("ultima_interacao")

            contato.save(update_fields=update_fields)  # [no-untyped-call]

            # Se ainda não há nome do contato, solicitar dados
            if not contato.nome_contato:
                FeaturesCompose.solicitacao_info_cliene()

    except Exception as e:
        logger.error(f"Erro ao processar entidades do contato: {e}")
        # Não interrompe o fluxo em caso de erro
        pass


def _analisar_conteudo_mensagem(mensagem_id: int) -> None:
    """
    Análise prévia do conteúdo da mensagem para detectar intent e extrair entidades.

    Esta função utiliza o sistema de IA para analisar o conteúdo textual da mensagem,
    identificando a intenção do usuário e extraindo entidades relevantes. É uma etapa
    crítica para melhorar a compreensão do contexto e direcionamento das respostas.

    Args:
        mensagem (Mensagem): Instância da mensagem a ser analisada.
            Deve conter o campo 'conteudo' com texto a ser analisado.

    Returns:
        None: A função atualiza a mensagem diretamente no banco de dados.

    Raises:
        Exception: Capturada internamente e logada. Função não retorna valor
            em caso de erro, mas garante que o processamento continue.

    Notes:
        - Implementação planejada para análise de intent e entidades
        - Base para futuras melhorias na experiência do usuário
        - Logs de erro são gerados para facilitar troubleshooting

    Examples:
        >>> mensagem = Mensagem.objects.get(id=123)
        >>> _analisar_conteudo_mensagem(mensagem)
    """

    try:
        mensagem: Mensagem = Mensagem.objects.get(id=mensagem_id)
        atendimento: Atendimento = cast(Atendimento, mensagem.atendimento)
        exists_atendimento_anterior = (
            Atendimento.objects.filter(contato=atendimento.contato)
            .exclude(id=atendimento.id)
            .exists()
        )
        # Carrega historico EXCLUINDO a mensagem atual para análise de contexto
        historico_atendimento = atendimento.carregar_historico_mensagens(
            excluir_mensagem_id=mensagem_id
        )
        # Se não há atendimentos anteriores, nem mensagens anteriores no
        # histórico do atendimento atual, chama apresentação
        if not exists_atendimento_anterior:
            if not historico_atendimento.get("conteudo_mensagens"):
                FeaturesCompose.mensagem_apresentacao()

        # Análise de intenção e extração de entidades
        resultado_analise = FeaturesCompose.analise_previa_mensagem(
            historico_atendimento=historico_atendimento, context=mensagem.conteudo
        )
        mensagem.intent_detectado = resultado_analise.intent_types
        mensagem.entidades_extraidas = resultado_analise.entity_types

        mensagem.save(update_fields=["intent_detectado", "entidades_extraidas"])

        # Processar entidades para atualizar dados do contato
        _processar_entidades_contato(mensagem, resultado_analise.entity_types)

    except Exception as e:
        logger.error(f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")
        # Continua processamento mesmo com erro na análise
        # Não interrompe o fluxo para garantir resiliência
        pass


def _pode_bot_responder_atendimento(atendimento: Optional["Atendimento"]) -> bool:
    """
    Verifica se o bot pode responder automaticamente em um atendimento específico.

    O bot não deve responder se há mensagens de atendente humano no atendimento
    ou se um atendente humano está associado ao atendimento, garantindo que
    a experiência do usuário não seja comprometida por respostas conflitantes.

    Args:
        atendimento (Atendimento | None): Instância do atendimento a ser
            verificado. Deve conter as relações 'mensagens' e
            'atendente_humano'.

    Returns:
        bool: True se o bot pode responder automaticamente, False caso contrário.
            Retorna False também em caso de erro durante a verificação.
    """

    if atendimento is None:
        return False

    try:
        # Verifica se existe alguma mensagem de atendente humano neste
        # atendimento ou se o atendimento tem um atendente humano associado
        mensagens_manager = getattr(atendimento, "mensagens", None)
        has_human_messages = False
        if mensagens_manager is not None:
            mm_any = cast(Any, mensagens_manager)
            has_human_messages = mm_any.filter(
                remetente=TipoRemetente.ATENDENTE_HUMANO
            ).exists()

        has_human_attendant = getattr(atendimento, "atendente_humano", None) is not None

        return not (has_human_messages or has_human_attendant)
    except Exception as e:
        logger.error(f"Erro ao verificar se bot pode responder: {e}")
        return False


def _compile_message_data_list(messages: List[MessageData]) -> MessageData:
    """
    Compila uma lista de MessageData em um único objeto MessageData.

    Concatena todos os campos 'conteudo' em uma única string,
    combina todos os metadados e utiliza os valores dos demais campos
    da última mensagem da lista.

    Args:
        messages (List[MessageData]): Lista de objetos MessageData para compilar

    Returns:
        MessageData: Objeto MessageData compilado

    Raises:
        ValueError: Se a lista estiver vazia ou contiver dados inválidos
    """
    if not messages:
        raise ValueError("Lista de mensagens não pode estar vazia")

    if not isinstance(messages, list):
        raise ValueError("Parâmetro 'messages' deve ser uma lista")

    # Validar se todas as mensagens são válidas
    for i, msg in enumerate(messages):
        if not isinstance(msg, MessageData):
            raise ValueError(f"Item {i} não é uma instância válida de MessageData")
        if not hasattr(msg, "numero_telefone") or not msg.numero_telefone:
            raise ValueError(f"Mensagem {i} não possui número de telefone válido")

    # Usar última mensagem como base
    ultima_mensagem = messages[-1]

    # Concatenar todos os conteúdos das mensagens (filtrar conteúdos vazios)
    conteudos_validos = [
        msg.conteudo.strip()
        for msg in messages
        if msg.conteudo and msg.conteudo.strip()
    ]
    conteudo_compilado = "\n".join(conteudos_validos)

    # Combinar todos os metadados (quando chaves repetirem, o último prevalece)
    metadados_compilados: dict[str, Any] = {}
    for msg in messages:
        if msg.metadados and isinstance(msg.metadados, dict):
            metadados_compilados.update(msg.metadados)

    # Criar nova MessageData com conteúdo e metadados compilados
    return MessageData(
        instance=ultima_mensagem.instance,
        numero_telefone=ultima_mensagem.numero_telefone,
        from_me=ultima_mensagem.from_me,
        conteudo=conteudo_compilado,
        message_type=ultima_mensagem.message_type,
        message_id=ultima_mensagem.message_id,
        metadados=metadados_compilados or None,
        nome_perfil_whatsapp=ultima_mensagem.nome_perfil_whatsapp,
    )
