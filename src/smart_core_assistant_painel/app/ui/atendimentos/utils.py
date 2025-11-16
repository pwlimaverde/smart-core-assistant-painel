"""Funções utilitárias para o aplicativo Atendimentos."""

import json
from dataclasses import dataclass
from typing import Any, Optional

from django.core.cache import cache
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import (
    AppInstance,
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
    processar_mensagem_por_contato,
)


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


@dataclass
class ProcessingParams:
    contact_id: int
    api_key: Optional[str]
    message: dict[str, Any]


def _send_message_response_by_contact(params: ProcessingParams) -> None:
    try:
        contact_id = int(params.contact_id)
        api_key: Optional[str] = params.api_key
        cache_key = f"evo_buffer_{contact_id}"
        env_list: list[dict[str, Any]] = cache.get(cache_key, [])
        if not env_list:
            logger.warning(f"Buffer vazio para contato {contact_id}")
            return
        last_env = env_list[-1]
        texts: list[str] = []
        metadados: dict[str, Any] = {}
        for env in env_list:
            msg_env = env.get("message", {})
            t = str(msg_env.get("text", "")).strip()
            if t:
                texts.append(t)
            md_env = msg_env.get("metadata") or {}
            if isinstance(md_env, dict):
                metadados.update(md_env)
        conteudo = "\n".join(texts)
        profile = last_env.get("profile", {})
        nome_perfil = profile.get("push_name")

        msg = params.message or {}
        message_type = str(msg.get("type") or "extendedTextMessage")
        message_id = str(msg.get("id") or "")
        if msg.get("text"):
            conteudo = str(msg.get("text"))
        if isinstance(msg.get("metadata"), dict):
            metadados.update(msg.get("metadata") or {})

        # Comentário (PT-BR): utiliza api_key do agendamento ou do envelope
        if not api_key:
            api_key = (
                str(last_env.get("apikey")) if last_env.get("apikey") else None
            )

        mensagem_id = processar_mensagem_por_contato(
            contato_id=contact_id,
            conteudo=conteudo,
            message_type=message_type,
            message_id=message_id,
            metadados=metadados or None,
            nome_perfil_whatsapp=(str(nome_perfil) if nome_perfil else None),
            from_me=False,
            api_key=api_key,
        )

        try:
            mensagem = Mensagem.objects.get(id=mensagem_id)
            _analisar_conteudo_mensagem(mensagem_id)
            try:
                mensagem.refresh_from_db(
                    fields=["intent_detectado", "entidades_extraidas"]
                )
            except Exception:
                mensagem.refresh_from_db()
            atendimento_obj: Atendimento = mensagem.atendimento
            if (
                getattr(atendimento_obj, "departamento", None) is None
                and api_key
            ):
                app_inst = AppInstance.objects.filter(
                    api_key=api_key, active=True
                ).first()
                if app_inst:
                    if getattr(app_inst, "departamento", None):
                        atendimento_obj.departamento = app_inst.departamento
                    elif getattr(app_inst, "owner", None):
                        atendimento_obj.atendente_humano = app_inst.owner
                        if getattr(app_inst.owner, "departamento", None):
                            atendimento_obj.departamento = (
                                app_inst.owner.departamento
                            )
                    try:
                        if getattr(
                            atendimento_obj, "departamento_id", None
                        ) and not getattr(
                            atendimento_obj, "fluxo_atendimento_id", None
                        ):
                            from smart_core_assistant_painel.app.ui.operacional.models import (
                                FluxoAtendimento,
                            )

                            fluxo = (
                                FluxoAtendimento.objects.filter(
                                    departamento_id=atendimento_obj.departamento_id,
                                )
                                .order_by("id")
                                .first()
                            )
                            if fluxo:
                                etapa_ini = (
                                    fluxo.get_etapa_inicial()
                                    or fluxo.etapas.order_by("ordem").first()
                                    or fluxo.etapas.order_by("id").first()
                                )
                                atendimento_obj.fluxo_atendimento = fluxo
                                atendimento_obj.etapa_atual = etapa_ini
                                atendimento_obj.save(
                                    update_fields=[
                                        "departamento",
                                        "atendente_humano",
                                        "fluxo_atendimento",
                                        "etapa_atual",
                                    ]
                                )
                            else:
                                atendimento_obj.save(
                                    update_fields=[
                                        "departamento",
                                        "atendente_humano",
                                    ]
                                )
                        else:
                            atendimento_obj.save(
                                update_fields=[
                                    "departamento",
                                    "atendente_humano",
                                ]
                            )
                    except Exception:
                        atendimento_obj.save(
                            update_fields=[
                                "departamento",
                                "atendente_humano",
                            ]
                        )
            # pode_responder = False
            pode_responder = _pode_bot_responder_atendimento(atendimento_obj)
            if pode_responder:
                prompt_lines: list[str] = [
                    (
                        "INSTRUÇÕES DO SISTEMA - CONTEXTO PARA RESPOSTA\n"
                        "Siga estritamente as orientações abaixo, em "
                        "português claro e objetivo.\n"
                        "Adapte a resposta ao contexto do atendimento atual."
                    ),
                    "Intenções detectadas e orientações:",
                ]
                seen_tags: set[str] = set()
                has_known_intent: bool = False
                index: int = 0
                for intent in mensagem.intent_detectado:
                    tag: str = list(intent.keys())[0]
                    if tag in seen_tags:
                        continue
                    seen_tags.add(tag)
                    index += 1
                    qc = QueryCompose.objects.filter(tag=tag).first()
                    if qc:
                        has_known_intent = True
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
                should_call_ai: bool = has_known_intent or (
                    isinstance(dados_treinamento, list)
                    and len(dados_treinamento) > 0
                )
                if should_call_ai:
                    result: AMTuple = FeaturesCompose.analise_mensage(
                        fluxos_disponiveis=fluxos_disponiveis,
                        historico_atendimento=historico_atendimento,
                        prompt_human=prompt_intent,
                        context=mensagem.conteudo,
                        dados_treinamento=dados_treinamento,
                    )
                    from smart_core_assistant_painel.app.evolution_sync.services import (
                        send_message_by_contact_id,
                    )

                    send_message_by_contact_id(contact_id, result.resposta_bot)
                    mensagem.registrar_resposta_bot(
                        resposta=result.resposta_bot,
                        confianca=result.confiabilidade,
                    )
                    _atualizar_status_atendimento_em_andamento(atendimento_obj)
                    if result.transferir_atendimento:
                        if result.fluxo_transferencia:
                            atendimento_obj.apply_flow_by_description(
                                result.fluxo_transferencia
                            )
                else:
                    texto_fallback: str = (
                        "Recebemos sua mensagem. Em breve retornaremos."
                    )
                    from smart_core_assistant_painel.app.evolution_sync.services import (
                        send_message_by_contact_id,
                    )

                    send_message_by_contact_id(contact_id, texto_fallback)
                    mensagem.registrar_resposta_bot(
                        resposta=texto_fallback,
                        confianca=0.0,
                    )
                    _atualizar_status_atendimento_em_andamento(atendimento_obj)
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
        logger.error(
            f"Erro ao processar mensagens para contato {contact_id}: {e}"
        )
    finally:
        try:
            cache.delete(cache_key)
            cache.delete(f"evo_timer_{contact_id}")
        except Exception:
            ...


def send_message_response_by_contact(
    args: ProcessingParams | str | int | dict[str, Any],
) -> None:
    if isinstance(args, ProcessingParams):
        _send_message_response_by_contact(args)
        return
    data: Any = args
    try:
        if isinstance(args, str):
            data = json.loads(args)
    except Exception:
        data = args
    if isinstance(data, int):
        contact_id = int(data)
        cache_key = f"evo_buffer_{contact_id}"
        env_list: list[dict[str, Any]] = cache.get(cache_key, [])
        last_env = env_list[-1] if env_list else {}
        msg_last = last_env.get("message", {})
        params = ProcessingParams(
            contact_id=contact_id,
            api_key=(
                str(last_env.get("apikey")) if last_env.get("apikey") else None
            ),
            message={
                "id": msg_last.get("id"),
                "type": msg_last.get("type"),
                "text": msg_last.get("text"),
                "metadata": msg_last.get("metadata"),
            },
        )
        _send_message_response_by_contact(params)
        return
    if isinstance(data, dict):
        params = ProcessingParams(
            contact_id=int(data.get("contact_id")),
            api_key=(
                str(data.get("api_key")) if data.get("api_key") else None
            ),
            message=dict(data.get("message") or {}),
        )
        _send_message_response_by_contact(params)
