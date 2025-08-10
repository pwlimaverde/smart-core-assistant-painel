import datetime
from typing import Any, List, cast
from venv import logger

from apscheduler.schedulers.background import BackgroundScheduler
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from oraculo.wrapper_evolutionapi import SendMessage

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
    TipoMensagem,
    TipoRemetente,
    processar_mensagem_whatsapp,
)

scheduler = BackgroundScheduler()
scheduler.start()


def send_message_response(phone: str) -> None:
    message_data_list: List[MessageData] = cache.get(f"wa_buffer_{phone}", [])

    if messages:
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

        # Processamento especial para mensagens não textuais
        if mensagem.tipo != TipoMensagem.TEXTO_FORMATADO:
            try:
                conteudo_original = mensagem.conteudo
                conteudo_convertido = _converter_contexto(metadata=mensagem.metadados)

                if conteudo_convertido != conteudo_original:
                    mensagem.conteudo = conteudo_convertido
                    mensagem.save(update_fields=["conteudo"])

            except Exception as e:
                # Continua processamento mesmo com erro na conversão
                logger.error(
                    f"Erro ao converter contexto da mensagem {mensagem_id}: {e}"
                )

        # Analise previa do conteudo da mensagem por agente de IA, detectando
        # intent e extraindo entidades
        try:
            _analisar_conteudo_mensagem(mensagem_id)
        except Exception as e:
            logger.error(f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")

        # Verificação de direcionamento do atendimento
        try:
            is_bot_responder = _pode_bot_responder_atendimento(mensagem.atendimento)
            if is_bot_responder:
                SendMessage().send_message(
                    instance="5588921729550",
                    body={
                        "number": "558897141275",
                        "text": "Obrigado pela sua mensagem, em breve um atendente entrará em contato.",
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

        cache.delete(f"wa_buffer_{phone}")
        cache.delete(f"wa_timer_{phone}")


def sched_message_response(phone: str) -> None:
    if not cache.get(f"wa_timer_{phone}"):
        scheduler.add_job(
            send_message_response,
            "date",
            run_date=datetime.datetime.now()
            + datetime.timedelta(seconds=SERVICEHUB.TIME_CACHE),
            kwargs={"phone": phone},
            misfire_grace_time=SERVICEHUB.TIME_CACHE,
        )
        cache.set(f"wa_timer_{phone}", True, timeout=(SERVICEHUB.TIME_CACHE * 2))


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
            logger.warning("SERVICEHUB.VALID_ENTITY_TYPES não configurado")
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
        logger.info(f"Entidades válidas para metadados: {entidades_validas}")
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

            contato.save(update_fields=update_fields)

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


def _pode_bot_responder_atendimento(atendimento):
    """
    Verifica se o bot pode responder automaticamente em um atendimento específico.

    O bot não deve responder se há mensagens de atendente humano no atendimento
    ou se um atendente humano está associado ao atendimento, garantindo que
    a experiência do usuário não seja comprometida por respostas conflitantes.

    Args:
        atendimento (Atendimento): Instância do atendimento a ser verificado.
            Deve conter as relações 'mensagens' e 'atendente_humano'.

    Returns:
        bool: True se o bot pode responder automaticamente, False caso contrário.
            Retorna False também em caso de erro durante a verificação.

    Raises:
        Exception: Capturada internamente e logada. Função retorna False
            em caso de erro para garantir segurança operacional.

    Notes:
        - A verificação inclui tanto mensagens quanto associação direta de atendente
        - Em caso de erro, assume-se comportamento conservador (False)
        - Logs de erro são gerados para facilitar troubleshooting

    Examples:
        >>> atendimento = Atendimento.objects.get(id=123)
        >>> pode_responder = _pode_bot_responder_atendimento(atendimento)
        >>> if pode_responder:
        ...     # Bot pode responder automaticamente
        ...     pass
    """

    try:
        # Verifica se existe alguma mensagem de atendente humano neste
        # atendimento ou se o atendimento tem um atendente humano associado
        mensagens_atendente = (
            atendimento.mensagens.filter(
                remetente=TipoRemetente.ATENDENTE_HUMANO
            ).exists()
            or atendimento.atendente_humano is not None
        )

        return not mensagens_atendente
    except Exception as e:
        logger.error(f"Erro ao verificar se bot pode responder: {e}")
        return False


def _converter_contexto(metadata: dict[str, Any]) -> str:
    """
    Converte metadados de mensagens multimídia para texto formatado legível.

    Esta função processa os metadados de mensagens não textuais (imagens,
    áudios, documentos, vídeos, stickers, etc.) e os converte em uma
    representação textual que pode ser compreendida e processada pelo
    sistema de IA para geração de respostas contextuais apropriadas.

    Args:
        metadata (dict): Dicionário contendo os metadados da mensagem.
            Estrutura típica inclui:
            - 'type': Tipo da mídia (image, audio, document, etc.)
            - 'mime_type'/'mimetype': Tipo MIME do arquivo
            - 'size'/'fileLength': Tamanho do arquivo em bytes
            - 'url': URL para download do arquivo
            - 'fileName': Nome original do arquivo
            - Campos específicos por tipo (duration, dimensions, etc.)

    Returns:
        str: Texto formatado representando o contexto da mensagem.
            Exemplos de retorno futuro:
            - "Imagem JPEG de 2.1MB (1920x1080)"
            - "Áudio MP3 de 45 segundos"
            - "Documento PDF: 'Relatório_Mensal.pdf' (856KB)"
            - "Vídeo MP4 de 2min30s (1280x720)"

    Raises:
        Exception: Repassada para o chamador em caso de erro na conversão.
            Logs de erro são gerados automaticamente para debugging.

    Implementation Status:
        - ATUAL: Retorna placeholder 'contexto' para todos os tipos
        - PLANEJADO: Conversão específica por tipo de mídia
        - FUTURO: Integração com análise de conteúdo por IA

    Processing Logic (Futuro):
        1. Identificar tipo de mídia pelos metadados
        2. Extrair informações relevantes (tamanho, formato, duração)
        3. Formatar texto descritivo apropriado
        4. Adicionar contexto específico quando possível

    Notes:
        - Função crítica para suporte completo a mensagens multimídia
        - Permite que o bot compreenda e responda a qualquer tipo de mensagem
        - Essencial para experiência de usuário completa no WhatsApp
        - Base para futuras funcionalidades de análise de conteúdo

    Examples:
        >>> # Imagem
        >>> metadata = {
        ...     "type": "image",
        ...     "mimetype": "image/jpeg",
        ...     "fileLength": 2048000,
        ...     "url": "https://example.com/image.jpg"
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Imagem JPEG de 2MB'  # Implementação futura

        >>> # Áudio
        >>> metadata = {
        ...     "type": "audio",
        ...     "mimetype": "audio/ogg",
        ...     "seconds": 45,
        ...     "ptt": True
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Mensagem de voz de 45 segundos'  # Implementação futura

        >>> # Documento
        >>> metadata = {
        ...     "type": "document",
        ...     "fileName": "Contrato_2025.pdf",
        ...     "mimetype": "application/pdf",
        ...     "fileLength": 856000
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Documento PDF: Contrato_2025.pdf (856KB)'  # Implementação futura
    """
    try:
        # TODO: Implementar lógica específica de conversão por tipo de mídia
        #
        # Estrutura planejada:
        # if not metadata:
        #     return "Conteúdo sem metadados"
        #
        # media_type = metadata.get('type', 'unknown')
        #
        # if media_type == 'image':
        #     return _processar_contexto_imagem(metadata)
        # elif media_type == 'audio':
        #     return _processar_contexto_audio(metadata)
        # elif media_type == 'document':
        #     return _processar_contexto_documento(metadata)
        # elif media_type == 'video':
        #     return _processar_contexto_video(metadata)
        # else:
        #     return f"Conteúdo do tipo {media_type}"

        # Implementação atual: placeholder
        return "contexto"

    except Exception as e:
        logger.error(f"Erro ao converter contexto: {e}")
        raise e


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
        ValueError: Se a lista estiver vazia
    """
    if not messages:
        raise ValueError("Lista de mensagens não pode estar vazia")

    # Usar última mensagem como base
    ultima_mensagem = messages[-1]

    # Concatenar todos os conteúdos das mensagens
    conteudo_compilado = "\n".join(msg.conteudo for msg in messages if msg.conteudo)

    # Combinar todos os metadados (quando chaves repetirem, o último prevalece)
    metadados_compilados: dict[str, Any] = {}
    for msg in messages:
        if msg.metadados:
            metadados_compilados.update(msg.metadados)

    # Criar nova MessageData com conteúdo e metadados compilados
    return MessageData(
        numero_telefone=ultima_mensagem.numero_telefone,
        from_me=ultima_mensagem.from_me,
        conteudo=conteudo_compilado,
        message_type=ultima_mensagem.message_type,
        message_id=ultima_mensagem.message_id,
        metadados=metadados_compilados or None,
        nome_perfil_whatsapp=ultima_mensagem.nome_perfil_whatsapp,
    )
