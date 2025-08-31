"""Funções utilitárias para o aplicativo Oráculo.

Este módulo fornece funções para gerenciar o buffer de mensagens do WhatsApp,
agendar respostas, processar entidades e analisar o conteúdo das mensagens.
"""

import json
from typing import Any, Optional, cast

from django.core.cache import cache
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.ui.oraculo.models_documento import Documento
from smart_core_assistant_painel.modules.ai_engine import (
    FeaturesCompose,
    MessageData,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .models import (
    Atendimento,
    Contato,
    Mensagem,
    TipoRemetente,
    processar_mensagem_whatsapp,
)
from .models_treinamento import Treinamento
from .signals import mensagem_bufferizada


def set_wa_buffer(message: MessageData) -> None:
    """Adiciona uma mensagem ao buffer do WhatsApp no cache.

    Args:
        message (MessageData): A mensagem a ser adicionada ao buffer.
    """
    cache_key = f"wa_buffer_{message.numero_telefone}"
    buffer = cache.get(cache_key, [])
    buffer.append(message)
    timeout = SERVICEHUB.TIME_CACHE + 120
    cache.set(cache_key, buffer, timeout=timeout)


def clear_wa_buffer(phone: str) -> None:
    """Remove o buffer de mensagens do WhatsApp para um telefone.

    Args:
        phone (str): O número de telefone normalizado.
    """
    cache_key = f"wa_buffer_{phone}"
    timer_key = f"wa_timer_{phone}"
    cache.delete(cache_key)
    cache.delete(timer_key)


def send_message_response(phone: str) -> None:
    """Envia uma resposta para uma mensagem do WhatsApp.

    Args:
        phone (str): O número de telefone para o qual enviar a resposta.
    """
    cache_key = f"wa_buffer_{phone}"
    message_data_list: list[MessageData] = cache.get(cache_key, [])
    if not message_data_list:
        logger.warning(f"Buffer vazio para {phone}")
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
        try:
            mensagem = Mensagem.objects.get(id=mensagem_id)
            _analisar_conteudo_mensagem(mensagem_id)
            query_vec = FeaturesCompose.generate_embeddings(
                text=mensagem.conteudo
            )
            teste_similaridade = Documento.buscar_documentos_similares(
                query_vec=query_vec
            )
            logger.info(f"Teste similaridade: {teste_similaridade}")


            atendimento_obj: Atendimento = cast(Atendimento, mensagem.atendimento)
            if _pode_bot_responder_atendimento(atendimento_obj):
                SERVICEHUB.whatsapp_service.send_message(
                    instance=message_data.instance,
                    api_key=message_data.api_key,
                    number=message_data.numero_telefone,
                    text="Obrigado pela sua mensagem, em breve um atendente entrará em contato.",
                )
        except Mensagem.DoesNotExist:
            logger.error(f"Mensagem criada (ID: {mensagem_id}) não encontrada.")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem {mensagem_id}: {e}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagens para {phone}: {e}")
    finally:
        clear_wa_buffer(phone)


def sched_message_response(phone: str) -> None:
    """Agenda o processamento da resposta via signal.

    Args:
        phone (str): O número de telefone para o qual agendar a resposta.
    """
    timer_key = f"wa_timer_{phone}"
    if not cache.get(timer_key):
        timeout_value = SERVICEHUB.TIME_CACHE + 120
        cache.set(timer_key, True, timeout=timeout_value)
        mensagem_bufferizada.send(sender="oraculo", phone=phone)


def _obter_entidades_metadados_validas() -> set[str]:
    """Obtém as entidades válidas para metadados do contato.

    Returns:
        set[str]: Um conjunto de entidades válidas para metadados.
    """
    try:
        valid_entity_types = SERVICEHUB.VALID_ENTITY_TYPES
        if not valid_entity_types:
            return set()
        entidades_config = json.loads(valid_entity_types)
        entidades_validas: set[str] = set()
        if isinstance(entidades_config, dict) and "entity_types" in entidades_config:
            for _, entidades in entidades_config["entity_types"].items():
                if isinstance(entidades, dict):
                    entidades_validas.update(entidades.keys())
        entidades_validas.discard("contato")
        entidades_validas.discard("telefone")
        entidades_validas.discard("nome_contato")
        return entidades_validas
    except Exception as e:
        logger.error(f"Erro ao obter entidades válidas: {e}")
        return set()


def _processar_entidades_contato(
    mensagem: "Mensagem", entity_types: list[dict[str, Any]]
) -> None:
    """Processa entidades extraídas para atualizar dados do contato.

    Args:
        mensagem (Mensagem): A instância da mensagem analisada.
        entity_types (list[dict[str, Any]]): lista de entidades extraídas.
    """
    try:
        atendimento = cast(Atendimento, mensagem.atendimento)
        contato = cast(Contato, atendimento.contato)
        contato_atualizado = False
        metadados_atualizados = False
        entidades_metadados = _obter_entidades_metadados_validas()

        for entidade_dict in entity_types:
            for tipo_entidade, valor in entidade_dict.items():
                if tipo_entidade.lower() == "nome_contato" and valor:
                    if not contato.nome_contato or len(str(valor).strip()) > len(
                        contato.nome_contato or ""
                    ):
                        contato.nome_contato = str(valor).strip()
                        contato_atualizado = True
                elif tipo_entidade.lower() in entidades_metadados and valor:
                    valor_limpo = str(valor).strip()
                    if valor_limpo:
                        if not contato.metadados:
                            contato.metadados = {}
                        if (
                            tipo_entidade.lower() not in contato.metadados
                            or contato.metadados[tipo_entidade.lower()] != valor_limpo
                        ):
                            contato.metadados[tipo_entidade.lower()] = valor_limpo
                            metadados_atualizados = True

        if contato_atualizado or metadados_atualizados:
            update_fields = []
            if contato_atualizado:
                update_fields.append("nome_contato")
            if metadados_atualizados:
                update_fields.append("metadados")
            contato.ultima_interacao = timezone.now()
            update_fields.append("ultima_interacao")
            contato.save(update_fields=update_fields)
            if not contato.nome_contato:
                FeaturesCompose.solicitacao_info_cliene()
    except Exception as e:
        logger.error(f"Erro ao processar entidades do contato: {e}")


def _analisar_conteudo_mensagem(mensagem_id: int) -> None:
    """Analisa o conteúdo da mensagem para detectar intenção e entidades.

    Args:
        mensagem_id (int): O ID da mensagem a ser analisada.
    """
    try:
        mensagem: Mensagem = Mensagem.objects.get(id=mensagem_id)
        atendimento: Atendimento = cast(Atendimento, mensagem.atendimento)
        exists_atendimento_anterior = (
            Atendimento.objects.filter(contato=atendimento.contato)
            .exclude(id=atendimento.id)
            .exists()
        )
        historico_atendimento = atendimento.carregar_historico_mensagens(
            excluir_mensagem_id=mensagem_id
        )
        if not exists_atendimento_anterior and not historico_atendimento.get(
            "conteudo_mensagens"
        ):
            FeaturesCompose.mensagem_apresentacao()
        resultado_analise = FeaturesCompose.analise_previa_mensagem(
            historico_atendimento=historico_atendimento, context=mensagem.conteudo
        )
        mensagem.intent_detectado = resultado_analise.intent_types
        mensagem.entidades_extraidas = resultado_analise.entity_types
        mensagem.save(update_fields=["intent_detectado", "entidades_extraidas"])
        _processar_entidades_contato(mensagem, resultado_analise.entity_types)
    except Exception as e:
        logger.error(f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")


def _pode_bot_responder_atendimento(atendimento: Optional["Atendimento"]) -> bool:
    """Verifica se o bot pode responder automaticamente a um atendimento.

    Args:
        atendimento (Optional[Atendimento]): A instância do atendimento.

    Returns:
        bool: True se o bot pode responder, False caso contrário.
    """
    if atendimento is None:
        return False
    try:
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
        logger.error(f"Erro ao verificar se o bot pode responder: {e}")
        return False


def _compile_message_data_list(messages: list[MessageData]) -> MessageData:
    """Compila uma lista de MessageData em um único objeto.

    Args:
        messages (list[MessageData]): A lista de objetos MessageData.

    Returns:
        MessageData: O objeto MessageData compilado.

    Raises:
        ValueError: Se a lista de mensagens estiver vazia ou for inválida.
    """
    if not messages:
        raise ValueError("lista de mensagens não pode estar vazia")
    if not isinstance(messages, list):
        raise ValueError("O parâmetro 'messages' deve ser uma lista")

    ultima_mensagem = messages[-1]
    conteudos_validos = [
        msg.conteudo.strip()
        for msg in messages
        if msg.conteudo and msg.conteudo.strip()
    ]
    conteudo_compilado = "\n".join(conteudos_validos)
    metadados_compilados: dict[str, Any] = {}
    for msg in messages:
        if msg.metadados and isinstance(msg.metadados, dict):
            metadados_compilados.update(msg.metadados)

    return MessageData(
        instance=ultima_mensagem.instance,
        api_key=ultima_mensagem.api_key,
        numero_telefone=ultima_mensagem.numero_telefone,
        from_me=ultima_mensagem.from_me,
        conteudo=conteudo_compilado,
        message_type=ultima_mensagem.message_type,
        message_id=ultima_mensagem.message_id,
        metadados=metadados_compilados or None,
        nome_perfil_whatsapp=ultima_mensagem.nome_perfil_whatsapp,
    )
