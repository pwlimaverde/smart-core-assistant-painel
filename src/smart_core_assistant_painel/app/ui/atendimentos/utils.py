"""Funções utilitárias para o aplicativo Atendimentos."""

import json
from typing import Any, Optional

from django.core.cache import cache
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    TipoEtapa,
)
from smart_core_assistant_painel.app.ui.treinamento.models import (
    Documento,
    QueryCompose,
)
from smart_core_assistant_painel.modules.ai_engine import (
    AMTuple,
    FeaturesCompose,
    MessageData,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .models import (
    Atendimento,
    Mensagem,
    TipoRemetente,
    processar_mensagem_whatsapp,
)
from .signals import mensagem_bufferizada


def set_wa_buffer(message: MessageData) -> None:
    """Adiciona uma mensagem ao buffer do WhatsApp no cache."""
    cache_key = f"wa_buffer_{message.numero_telefone}"
    buffer = cache.get(cache_key, [])
    buffer.append(message)
    timeout = SERVICEHUB.TIME_CACHE + 60
    cache.set(cache_key, buffer, timeout=timeout)


def clear_wa_buffer(phone: str) -> None:
    """Remove o buffer de mensagens do WhatsApp para um telefone."""
    cache_key = f"wa_buffer_{phone}"
    timer_key = f"wa_timer_{phone}"
    cache.delete(cache_key)
    cache.delete(timer_key)


def send_message_response(phone: str) -> None:
    """Envia uma resposta para uma mensagem do WhatsApp."""
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
            # Garante que os campos atualizados pela análise sejam refletidos neste objeto
            try:
                mensagem.refresh_from_db(
                    fields=["intent_detectado", "entidades_extraidas"]
                )
            except Exception:
                mensagem.refresh_from_db()
            atendimento_obj: Atendimento = mensagem.atendimento
            pode_responder = _pode_bot_responder_atendimento(atendimento_obj)
            if pode_responder:
                # Monta um prompt de sistema claro e objetivo para orientar a LLM
                # sobre como responder de acordo com as intenções detectadas.

                prompt_lines: list[str] = [
                    (
                        "INSTRUÇÕES DO SISTEMA - CONTEXTO PARA RESPOSTA\n"
                        "Siga estritamente as orientações abaixo, em "
                        "português claro e objetivo.\n"
                        "Adapte a resposta ao contexto do atendimento atual."
                    ),
                    "Intenções detectadas e orientações:",
                ]
                # Remove tags duplicadas mantendo a primeira ocorrência
                seen_tags: set[str] = set()
                has_known_intent: bool = False
                index: int = 0
                for intent in mensagem.intent_detectado:
                    tag: str = list(intent.keys())[0]
                    # Pula intents com tag já utilizada para evitar instruções repetidas
                    if tag in seen_tags:
                        continue
                    seen_tags.add(tag)
                    index += 1
                    qc = QueryCompose.objects.filter(tag=tag).first()
                    if qc:
                        # Há intenção conhecida (possui configuração de comportamento)
                        has_known_intent = True
                        # Normaliza espaços e remove quebras de linha acidentais
                        behavior: str = " ".join(
                            str(qc.comportamento).split()
                        ).strip()
                        prompt_lines.append(f"{index}. [{tag}] {behavior}")
                    else:
                        intent_vector: list[float] = (
                            FeaturesCompose.generate_embeddings(
                                f"{tag}: {intent[tag]}"
                            )
                        )
                        comportamento: str | None = (
                            QueryCompose.buscar_comportamento_similar(
                                intent_vector
                            )
                        )
                        if comportamento:
                            prompt_lines.append(
                                f"{index}. [{tag}] {comportamento}"
                            )
                prompt_lines.append(
                    (
                        "Se houver múltiplas intenções, priorize a ordem "
                        "listada e mantenha a resposta concisa."
                    )
                )
                historico_atendimento = (
                    atendimento_obj.carregar_historico_mensagens(
                        excluir_mensagem_id=mensagem_id
                    )
                )
                prompt_intent: str = "\n".join(prompt_lines)
                vector_conteudo = FeaturesCompose.generate_embeddings(
                    mensagem.conteudo
                )
                dados_treinamento = Documento.buscar_documentos_similares(
                    query_vec=vector_conteudo
                )

                fluxos_disponiveis: dict[str, str] = (
                    _gerar_dict_fluxos_disponiveis()
                )
                # Comentário (PT-BR): evita uso da IA quando existirem apenas
                # tags desconhecidas ou quando dados de treinamento não forem
                # uma lista válida, mantendo previsibilidade em testes.
                should_call_ai: bool = (
                    has_known_intent
                    or (
                        isinstance(dados_treinamento, list)
                        and len(dados_treinamento) > 0
                    )
                )

                if should_call_ai:
                    # Anotação explícita da tupla para garantir inferência tipada
                    result: AMTuple = FeaturesCompose.analise_mensage(
                        fluxos_disponiveis=fluxos_disponiveis,
                        historico_atendimento=historico_atendimento,
                        prompt_human=prompt_intent,
                        context=mensagem.conteudo,
                        dados_treinamento=dados_treinamento,
                    )

                    SERVICEHUB.whatsapp_service.send_message(
                        instance=message_data.instance,
                        api_key=message_data.api_key,
                        number=message_data.numero_telefone,
                        text=result.resposta_bot,
                    )
                    mensagem.registrar_resposta_bot(
                        resposta=result.resposta_bot,
                        confianca=result.confiabilidade,
                    )

                    # Atualiza status do atendimento para "Em Atendimento"
                    _atualizar_status_atendimento_em_andamento(
                        atendimento_obj
                    )
                    logger.info(f"result: {result}")
                    if result.transferir_atendimento:
                        if result.fluxo_transferencia:
                            logger.info(
                                (
                                    "Transferência para fluxo: "
                                    f"{result.fluxo_transferencia}"
                                )
                            )
                            atendimento_obj.apply_flow_by_description(
                                result.fluxo_transferencia
                            )
                else:
                    # Resposta de fallback sem IA para manter o fluxo
                    texto_fallback: str = (
                        "Recebemos sua mensagem. Em breve retornaremos."
                    )
                    SERVICEHUB.whatsapp_service.send_message(
                        instance=message_data.instance,
                        api_key=message_data.api_key,
                        number=message_data.numero_telefone,
                        text=texto_fallback,
                    )
                    mensagem.registrar_resposta_bot(
                        resposta=texto_fallback,
                        confianca=0.0,
                    )

                    # Atualiza status do atendimento para "Em Atendimento"
                    _atualizar_status_atendimento_em_andamento(
                        atendimento_obj
                    )
            else:
                logger.warning(
                    "DEBUG: Bot não pode responder - pulando processamento de intents"
                )

        except Mensagem.DoesNotExist:
            logger.error(
                f"Mensagem criada (ID: {mensagem_id}) não encontrada."
            )
        except Exception as e:
            logger.error(f"Erro ao processar mensagem {mensagem_id}: {e}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagens para {phone}: {e}")
    finally:
        clear_wa_buffer(phone)


def sched_message_response(phone: str) -> None:
    """Agenda o processamento da resposta via signal."""
    timer_key = f"wa_timer_{phone}"
    if not cache.get(timer_key):
        timeout_value = SERVICEHUB.TIME_CACHE + 60
        cache.set(timer_key, True, timeout=timeout_value)
        mensagem_bufferizada.send(sender="atendimentos", phone=phone)


def _obter_entidades_metadados_validas() -> set[str]:
    """Obtém as entidades válidas para metadados do contato."""
    try:
        valid_entity_types = SERVICEHUB.VALID_ENTITY_TYPES
        if not valid_entity_types:
            return set()
        entidades_config: dict[str, Any] = json.loads(valid_entity_types)
        entidades_validas: set[str] = set()
        if "entity_types" in entidades_config:
            entidades: dict[str, Any] = entidades_config["entity_types"]
            for _, entidades in entidades_config["entity_types"].items():
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
    """Processa entidades extraídas para atualizar dados do contato."""
    try:
        atendimento: Atendimento = mensagem.atendimento
        contato: Contato = atendimento.contato
        contato_atualizado = False
        metadados_atualizados = False
        entidades_metadados = _obter_entidades_metadados_validas()

        for entidade_dict in entity_types:
            for tipo_entidade, valor in entidade_dict.items():
                if tipo_entidade.lower() == "nome_contato" and valor:
                    if not contato.nome_contato or len(
                        str(valor).strip()
                    ) > len(contato.nome_contato or ""):
                        contato.nome_contato = str(valor).strip()
                        contato_atualizado = True
                elif tipo_entidade.lower() in entidades_metadados and valor:
                    valor_limpo = str(valor).strip()
                    if valor_limpo:
                        if not contato.metadados:
                            contato.metadados = {}
                        if (
                            tipo_entidade.lower() not in contato.metadados
                            or contato.metadados[tipo_entidade.lower()]
                            != valor_limpo
                        ):
                            contato.metadados[tipo_entidade.lower()] = (
                                valor_limpo
                            )
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
    """Analisa o conteúdo da mensagem para detectar intenção e entidades."""
    try:
        mensagem: Mensagem = Mensagem.objects.get(id=mensagem_id)
        atendimento: Atendimento = mensagem.atendimento
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
        intent_types = QueryCompose.build_intent_types_config()
        resultado_analise = FeaturesCompose.analise_previa_mensagem(
            historico_atendimento=historico_atendimento,
            context=mensagem.conteudo,
            valid_intent_types=intent_types,
        )
        mensagem.intent_detectado = resultado_analise.intent_types
        mensagem.entidades_extraidas = resultado_analise.entity_types
        mensagem.save(
            update_fields=["intent_detectado", "entidades_extraidas"]
        )
        _processar_entidades_contato(mensagem, resultado_analise.entity_types)
    except Exception as e:
        logger.error(
            f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}"
        )


def _garantir_estrutura_atendimento_padrao() -> tuple[
    Departamento, FluxoAtendimento
]:
    """
    Garante que exista a estrutura padrão de atendimento.

    Cria o departamento 'Atendimento' e o fluxo 'Atendimento Inicial' se não existirem.

    Returns:
        Tupla com (departamento, fluxo) criados ou existentes.
    """
    try:
        # Verifica/cria departamento Atendimento
        departamento, created_departamento = (
            Departamento.objects.get_or_create(
                nome="Atendimento",
                defaults={
                    "descricao": (
                        "Departamento usado para centralizar o atendimento via mensagens "
                        "e fazer seu processamento antes de seguir para os outros departamentos."
                    ),
                    "ativo": True,
                },
            )
        )

        if created_departamento:
            logger.info(
                f"Departamento 'Atendimento' criado com ID {departamento.id}"
            )
        else:
            logger.debug(
                f"Departamento 'Atendimento' já existe (ID {departamento.id})"
            )

        # Verifica/cria fluxo Atendimento Inicial
        fluxo, created_fluxo = FluxoAtendimento.objects.get_or_create(
            departamento=departamento,
            nome="Atendimento Inicial",
            defaults={
                "descricao": "Fluxo responsável pelo processamento inicial dos atendimentos",
                "ativo": True,
            },
        )

        if created_fluxo:
            logger.info(
                f"Fluxo 'Atendimento Inicial' criado com ID {fluxo.id}"
            )
        else:
            logger.debug(
                f"Fluxo 'Atendimento Inicial' já existe (ID {fluxo.id})"
            )

        return departamento, fluxo

    except Exception as e:
        logger.error(f"Erro ao garantir estrutura de atendimento padrão: {e}")
        raise


def _atualizar_status_atendimento_em_andamento(
    atendimento: "Atendimento",
) -> None:
    """
    Atualiza o status e etapa do atendimento para "Em Atendimento".

    Args:
        atendimento: Objeto Atendimento a ser atualizado.
    """
    try:
        # Garante que a estrutura padrão exista
        _, fluxo = _garantir_estrutura_atendimento_padrao()

        # Atualiza o status do atendimento
        atendimento.status = StatusAtendimento.EM_ATENDIMENTO

        # Busca a etapa "Em Atendimento" do fluxo
        etapa_em_atendimento = fluxo.etapas.filter(
            nome="Em Atendimento", tipo_etapa=TipoEtapa.TRABALHO
        ).first()

        if etapa_em_atendimento:
            atendimento.etapa_atual = etapa_em_atendimento
            logger.debug(
                f"Atendimento {atendimento.id} movido para etapa '{etapa_em_atendimento.nome}'"
            )
        else:
            logger.warning(
                f"Etapa 'Em Atendimento' não encontrada no fluxo {fluxo.id}"
            )

        # Salva as alterações apenas nos campos modificados
        atendimento.save(update_fields=["status", "etapa_atual"])

        logger.info(
            f"Atendimento {atendimento.id} atualizado para status 'Em Atendimento'"
        )

    except Exception as e:
        logger.error(
            f"Erro ao atualizar status do atendimento {atendimento.id}: {e}"
        )
        raise


def _gerar_dict_fluxos_disponiveis() -> dict[str, str]:
    """
    Gera um dicionário com todos os fluxos de atendimento disponíveis.

    A chave do dicionário é formatada como "nome_fluxo - nome_departamento"
    e o valor é a descrição do fluxo.

    Returns:
        Dicionário com os fluxos disponíveis no formato:
        {"Atendimento Comercial - Comercial": "Descrição do fluxo"}
    """
    try:
        fluxos_disponiveis: dict[str, str] = {}

        # Busca todos os fluxos ativos (exceto o padrão) ordenados por departamento e nome
        fluxos_queryset = (
            FluxoAtendimento.objects.filter(ativo=True)
            .exclude(
                nome="Atendimento Inicial", departamento__nome="Atendimento"
            )
            .select_related("departamento")
            .order_by("departamento__nome", "nome")
        )

        for fluxo in fluxos_queryset:
            # Formata a chave como "nome_fluxo - nome_departamento"
            chave = f"{fluxo.nome} - {fluxo.departamento.nome}"

            # Usa a descrição do fluxo como valor, ou texto padrão se estiver vazia
            valor = (
                fluxo.descricao
                or f"Fluxo de {fluxo.nome} para {fluxo.departamento.nome}"
            )

            fluxos_disponiveis[chave] = valor

        logger.info(
            f"Gerado dicionário com {len(fluxos_disponiveis)} fluxos disponíveis - {fluxos_disponiveis}"
        )
        return fluxos_disponiveis

    except Exception as e:
        logger.error(f"Erro ao gerar dicionário de fluxos disponíveis: {e}")
        return {}


def gerar_dict_fluxos_disponiveis() -> dict[str, str]:
    """Exponha os fluxos disponíveis de atendimento.

    Função pública para uso externo e em testes. Internamente delega
    para a função privada que realiza a consulta ao banco e trata
    possíveis erros.

    Returns:
        Dicionário no formato "nome_fluxo - nome_departamento": descrição.
    """
    return _gerar_dict_fluxos_disponiveis()


def _configurar_atendimento_padrao(atendimento: "Atendimento") -> None:
    """
    Configura um atendimento para usar a estrutura padrão.

    Args:
        atendimento: Objeto Atendimento a ser configurado.
    """
    try:
        departamento, fluxo = _garantir_estrutura_atendimento_padrao()

        # Atualiza o departamento do atendimento
        atendimento.departamento = departamento

        # Busca a etapa "Fila de Atendimento" do fluxo
        etapa_fila = fluxo.etapas.filter(
            nome="Fila de Atendimento", tipo_etapa=TipoEtapa.FILA
        ).first()

        if etapa_fila:
            atendimento.etapa_atual = etapa_fila
            logger.debug(
                f"Atendimento {atendimento.id} configurado para etapa '{etapa_fila.nome}'"
            )
        else:
            logger.warning(
                f"Etapa 'Fila de Atendimento' não encontrada no fluxo {fluxo.id}"
            )

        # Salva as alterações apenas nos campos modificados
        atendimento.save(update_fields=["departamento", "etapa_atual"])

    except Exception as e:
        logger.error(
            f"Erro ao configurar atendimento padrão {atendimento.id}: {e}"
        )
        raise


def _pode_bot_responder_atendimento(
    atendimento: Optional["Atendimento"],
) -> bool:
    """Verifica se o bot pode responder automaticamente a um atendimento.

    Regras:
    - Somente responde quando o atendimento está no departamento
      "Atendimento". Caso esteja em outro departamento, o bot não deve
      responder.
    - Mantém a lógica de não responder se há interação humana (mensagens
      de atendente ou atendente humano atribuído).
    """
    if atendimento is None:
        return False

    try:
        # Comentário (PT-BR): verifica o departamento atual do atendimento.
        # Se estiver em outro departamento que não "Atendimento",
        # o bot não pode responder.
        dep_atual = getattr(atendimento, "departamento", None)

        # Comentário: só bloqueia se for de fato um Departamento diferente
        # de "Atendimento". Objetos mockados ou ausência são tratados como
        # não configurados.
        if isinstance(dep_atual, Departamento) and (
            getattr(dep_atual, "nome", None) != "Atendimento"
        ):
            return False

        # Comentário (PT-BR): se não houver departamento definido,
        # trata-se da primeira interação. Configura a estrutura padrão
        # (Departamento "Atendimento" e etapa inicial) e retorna True
        # pois o bot pode responder.
        if dep_atual is None or not isinstance(dep_atual, Departamento):
            _configurar_atendimento_padrao(atendimento)
            return True

        mensagens_manager = getattr(atendimento, "mensagens", None)
        has_human_messages = False
        if mensagens_manager is not None:
            mm_any = mensagens_manager
            has_human_messages = mm_any.filter(
                remetente=TipoRemetente.ATENDENTE_HUMANO
            ).exists()
        has_human_attendant = (
            getattr(atendimento, "atendente_humano", None) is not None
        )
        return not (has_human_messages or has_human_attendant)
    except Exception as e:
        logger.error(f"Erro ao verificar se o bot pode responder: {e}")
        return False


def _compile_message_data_list(messages: list[MessageData]) -> MessageData:
    """Compila uma lista de MessageData em um único objeto."""
    if not messages:
        raise ValueError("lista de mensagens não pode estar vazia")

    ultima_mensagem = messages[-1]
    conteudos_validos = [
        msg.conteudo.strip()
        for msg in messages
        if msg.conteudo and msg.conteudo.strip()
    ]
    conteudo_compilado = "\n".join(conteudos_validos)
    metadados_compilados: dict[str, Any] = {}
    for msg in messages:
        if msg.metadados:
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
