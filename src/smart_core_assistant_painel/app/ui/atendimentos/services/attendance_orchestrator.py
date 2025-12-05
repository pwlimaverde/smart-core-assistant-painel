"""Orquestrador de processamento de atendimentos.

Este módulo contém a lógica principal para processar mensagens agendadas,
coordenar serviços e gerar respostas do bot.
"""

from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from smart_core_assistant_painel.app.evolution_sync.services import (
    clear_scheduling_lock,
    get_and_clear_buffer_contact,
)
from smart_core_assistant_painel.modules.ai_engine import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .interfaces import (
    AttendanceOrchestratorInterface,
    AttendanceStructureManagerInterface,
    BotRulesEngineInterface,
    MessageAnalyzerInterface,
)

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento,
        Mensagem,
    )


class AttendanceOrchestrator(AttendanceOrchestratorInterface):
    """[ATD-LIF-001] Orquestrador de processamento de atendimentos.

    Responsabilidades:
    - Coordenar processamento de respostas
    - Integrar todos os services
    - Gerenciar fluxo completo de mensagens agendadas
    """

    def __init__(
        self,
        message_analyzer: MessageAnalyzerInterface,
        structure_manager: AttendanceStructureManagerInterface,
        rules_engine: BotRulesEngineInterface,
    ) -> None:
        """Inicializa orquestrador com dependências injetadas.

        Args:
            message_analyzer: Serviço de análise de mensagens.
            structure_manager: Gerenciador de estrutura de atendimento.
            rules_engine: Motor de regras de negócio do bot.
        """
        self._message_analyzer = message_analyzer
        self._structure_manager = structure_manager
        self._rules_engine = rules_engine

    def process_contact_response(
        self,
        contact_id: int,
        api_key: Optional[str] = None,
    ) -> None:
        """Processa resposta para um contato a partir de mensagens agendadas.

        Fluxo:
        1. Obtém mensagens do buffer
        2. Compila conteúdo e metadados
        3. Cria mensagem no sistema
        4. Analisa intenções
        5. Gera resposta do bot (se aplicável)
        6. Limpa buffer

        Args:
            contact_id: ID do contato a processar.
            api_key: Chave de API para envio de mensagens (opcional).
        """
        try:
            # 1. Obtém mensagens do buffer e limpa atomicamente
            env_list = get_and_clear_buffer_contact(contact_id)
            if not env_list:
                logger.warning(
                    f"Sem mensagens para processar para contato {contact_id}"
                )
                return

            # 2. Compila conteúdo e metadados
            content_data = self._compile_message_content(env_list)

            # 3. Determina API key
            final_api_key = api_key or content_data.get("api_key")
            logger.debug(
                f"Processando mensagem para contato {contact_id} - {content_data['content']}"
            )
            # 4. Cria mensagem no sistema
            message_id = self._create_message(
                contact_id=contact_id,
                content=content_data["content"],
                message_type=content_data["message_type"],
                message_id_whatsapp=content_data["message_id"],
                metadados=content_data["metadados"],
                profile_name=content_data["profile_name"],
                api_key=final_api_key,
            )

            if not message_id:
                return

            # 5. Processa mensagem e gera resposta
            self._process_message_and_respond(
                message_id=message_id,
                contact_id=contact_id,
                api_key=final_api_key,
                env_list=env_list,
            )

        except Exception as e:
            logger.error(
                f"Erro ao processar mensagens para contato {contact_id}: {e}"
            )
        finally:
            # 6. Limpa lock de agendamento para permitir novas tasks
            try:
                clear_scheduling_lock(contact_id)
                logger.info(
                    f"atd_process_done contact_id={contact_id} scheduling_lock_cleared=1"
                )
            except Exception:
                pass

    def _compile_message_content(
        self, env_list: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compila conteúdo e metadados de múltiplos envelopes.

        Args:
            env_list: Lista de envelopes de mensagens.

        Returns:
            Dicionário com conteúdo compilado.
        """
        last_env = env_list[-1]
        texts: list[str] = []
        metadados: dict[str, Any] = {}

        # Compila textos e metadados de todos os envelopes
        for env in env_list:
            msg_env = env.get("message", {})
            t = str(msg_env.get("text", "")).strip()
            if t:
                texts.append(t)

            md_env = msg_env.get("metadata") or {}
            if isinstance(md_env, dict):
                metadados.update(md_env)

        # Dados do último envelope (mais recente)
        profile = last_env.get("profile", {})
        msg = last_env.get("message", {})

        return {
            "content": "\n".join(texts),
            "message_type": str(msg.get("type") or "extendedTextMessage"),
            "message_id": str(msg.get("id") or ""),
            "profile_name": profile.get("push_name"),
            "metadados": metadados,
            "api_key": str(last_env.get("apikey"))
            if last_env.get("apikey")
            else None,
        }

    def _create_message(
        self,
        contact_id: int,
        content: str,
        message_type: str,
        message_id_whatsapp: str,
        metadados: Optional[dict[str, Any]],
        profile_name: Optional[str],
        api_key: Optional[str],
    ) -> Optional[int]:
        """Cria mensagem no sistema.

        Args:
            contact_id: ID do contato.
            content: Conteúdo da mensagem.
            message_type: Tipo da mensagem.
            message_id_whatsapp: ID da mensagem no WhatsApp.
            metadados: Metadados adicionais.
            profile_name: Nome do perfil no WhatsApp.
            api_key: Chave de API.

        Returns:
            ID da mensagem criada ou None se falhar.
        """
        from smart_core_assistant_painel.app.ui.atendimentos.models import (
            processar_mensagem_por_contato,
        )

        if not content:
            logger.warning(
                f"Conteúdo vazio para contato {contact_id}. Ignorando processamento."
            )
            return None

        try:
            mensagem_id = processar_mensagem_por_contato(
                contato_id=contact_id,
                conteudo=content,
                message_type=message_type,
                message_id=message_id_whatsapp,
                metadados=metadados or None,
                nome_perfil_whatsapp=(
                    str(profile_name) if profile_name else None
                ),
                from_me=False,
                api_key=api_key,
            )

            logger.info(
                f"atd_process_compiled contact_id={contact_id} "
                f"text_len={len(content)} msg_id={mensagem_id}"
            )

            return mensagem_id

        except Exception as e:
            logger.error(f"Erro ao criar mensagem: {e}")
            return None

    def _process_message_and_respond(
        self,
        message_id: int,
        contact_id: int,
        api_key: Optional[str],
        env_list: list[dict[str, Any]],
    ) -> None:
        """Processa mensagem e gera resposta do bot.

        Args:
            message_id: ID da mensagem.
            contact_id: ID do contato.
            api_key: Chave de API.
            env_list: Lista de envelopes originais.
        """
        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                Mensagem,
            )

            # Obtém mensagem
            mensagem: Mensagem = Mensagem.objects.get(id=message_id)

            # Analisa conteúdo (intenções e entidades)
            self._message_analyzer.analyze_message_content(message_id)

            # Atualiza mensagem com dados analisados
            mensagem.refresh_from_db(
                fields=["intent_detectado", "entidades_extraidas"]
            )

            # Configura atendimento
            atendimento = mensagem.atendimento
            self._configure_attendance(
                atendimento, api_key, env_list, message=mensagem
            )

            # Verifica se bot pode responder
            pode_responder = self._rules_engine.can_bot_respond(atendimento)

            logger.info(
                f"atd_process_can_respond contact_id={contact_id} "
                f"pode_responder={pode_responder}"
            )

            if pode_responder:
                self._generate_and_register_response(
                    mensagem, atendimento, env_list
                )
            else:
                logger.warning(
                    "Bot não pode responder - pulando processamento de intents"
                )

        except Exception as e:
            logger.error(f"Erro ao processar mensagem {message_id}: {e}")

    def _configure_attendance(
        self,
        attendance: "Atendimento",
        api_key: Optional[str],
        env_list: list[dict[str, Any]],
        message: Optional["Mensagem"] = None,
    ) -> None:
        """Configura atendimento com API key e departamento.

        Args:
            attendance: Atendimento a configurar.
            api_key: Chave de API.
            env_list: Lista de envelopes.
        """
        try:
            # Salva API key no contexto
            if api_key:
                self._save_api_key_to_context(attendance, api_key)

            # Verifica e atualiza contexto da instância (mudança de departamento/fluxo)
            if api_key:
                self._check_and_update_instance_context(attendance, api_key)

            # Configura departamento inicial se ainda não definido (fallback)
            if getattr(attendance, "departamento", None) is None and api_key:
                self._configure_department_from_app_instance(
                    attendance, api_key
                )

            # Salva metadados do Evolution
            self._save_evolution_metadata(
                attendance, env_list, message=message
            )

        except Exception as e:
            logger.error(f"Erro ao configurar atendimento: {e}")

    def _save_api_key_to_context(
        self, attendance: "Atendimento", api_key: str
    ) -> None:
        """Salva API key no contexto do atendimento.

        Args:
            attendance: Atendimento.
            api_key: Chave de API.
        """
        try:
            ctx = dict(attendance.contexto_conversa or {})
            if ctx.get("api_key") != api_key:
                ctx["api_key"] = api_key
                attendance.contexto_conversa = ctx
                attendance.save(update_fields=["contexto_conversa"])
        except Exception:
            pass

    def _check_and_update_instance_context(
        self, attendance: "Atendimento", api_key: str
    ) -> None:
        """Verifica e atualiza o contexto se a instância mudou.

        Se a mensagem veio de uma instância diferente da atual do atendimento,
        atualiza departamento, fluxo, etapa e atendente.

        Args:
            attendance: Atendimento atual.
            api_key: API Key da instância que recebeu a mensagem.
        """
        try:
            from smart_core_assistant_painel.app.ui.operacional.models import (
                AppInstance,
            )

            # Busca instância atual da mensagem
            app_inst: Optional[AppInstance] = AppInstance.objects.filter(
                api_key=api_key, active=True
            ).first()

            if not app_inst:
                return

            # Determina o novo departamento e atendente baseados na instância
            novo_departamento = None
            novo_atendente = None

            if getattr(app_inst, "departamento", None):
                novo_departamento = app_inst.departamento
            elif getattr(app_inst, "owner", None):
                novo_atendente = app_inst.owner
                if getattr(app_inst.owner, "departamento", None):
                    novo_departamento = app_inst.owner.departamento

            # Se não detectou departamento, não há o que alterar
            if not novo_departamento:
                return

            # Verifica se houve mudança de departamento
            # (ou se o atendimento não tinha departamento)
            dept_atual = getattr(attendance, "departamento", None)

            # Se o departamento é o mesmo, verifica se precisa ajustar atendente
            # Caso a instância seja de um atendente específico
            if dept_atual and dept_atual.id == novo_departamento.id:
                if (
                    novo_atendente
                    and attendance.atendente_humano != novo_atendente
                ):
                    attendance.atendente_humano = novo_atendente
                    attendance.save(update_fields=["atendente_humano"])
                return

            # Se chegou aqui, houve mudança de departamento (ou definição inicial)
            logger.info(
                f"Detectada mudança de instância/departamento para atendimento {attendance.id}. "
                f"Antigo: {dept_atual}. Novo: {novo_departamento}."
            )

            attendance.departamento = novo_departamento
            attendance.atendente_humano = novo_atendente

            # Busca novo fluxo do departamento
            fluxo = novo_departamento.get_fluxo()

            if fluxo:
                etapa_ini = (
                    fluxo.get_etapa_inicial()
                    or fluxo.etapas.order_by("ordem").first()
                    or fluxo.etapas.order_by("id").first()
                )

                if etapa_ini:
                    attendance.fluxo_atendimento = fluxo
                    attendance.etapa_atual = etapa_ini
                    logger.info(
                        f"Fluxo/Etapa atualizados para atendimento {attendance.id}: "
                        f"Fluxo={fluxo.nome}, Etapa={etapa_ini.nome}"
                    )
                else:
                    logger.warning(
                        f"Fluxo {fluxo.nome} (ID {fluxo.id}) não possui etapas."
                    )
            else:
                logger.warning(
                    f"Departamento {novo_departamento.nome} (ID {novo_departamento.id}) "
                    "não possui fluxo ativo."
                )

            # Garante que o bot pode responder
            attendance.bot_pode_atender = True

            attendance.save(
                update_fields=[
                    "departamento",
                    "atendente_humano",
                    "fluxo_atendimento",
                    "etapa_atual",
                    "bot_pode_atender",
                ]
            )

        except Exception as e:
            logger.error(f"Erro ao atualizar contexto da instância: {e}")

    def _configure_department_from_app_instance(
        self, attendance: "Atendimento", api_key: str
    ) -> None:
        """Configura departamento baseado em AppInstance.

        Args:
            attendance: Atendimento.
            api_key: Chave de API.
        """
        try:
            from smart_core_assistant_painel.app.ui.operacional.models import (
                AppInstance,
            )
            from smart_core_assistant_painel.app.ui.operacional.models import (
                FluxoAtendimento,
            )

            app_inst: Optional[AppInstance] = AppInstance.objects.filter(
                api_key=api_key, active=True
            ).first()

            if not app_inst:
                return

            # Configura departamento
            if getattr(app_inst, "departamento", None):
                attendance.departamento = app_inst.departamento
            elif getattr(app_inst, "owner", None):
                attendance.atendente_humano = app_inst.owner
                if getattr(app_inst.owner, "departamento", None):
                    attendance.departamento = app_inst.owner.departamento

            # Configura fluxo se departamento foi definido
            if getattr(attendance, "departamento_id", None) and not getattr(
                attendance, "fluxo_atendimento_id", None
            ):
                fluxo = (
                    FluxoAtendimento.objects.filter(
                        departamento_id=attendance.departamento_id
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
                    attendance.fluxo_atendimento = fluxo
                    attendance.etapa_atual = etapa_ini

            # Salva mudanças
            attendance.save(
                update_fields=[
                    "departamento",
                    "atendente_humano",
                    "fluxo_atendimento",
                    "etapa_atual",
                ]
            )

        except Exception:
            pass

    def _save_evolution_metadata(
        self,
        attendance: "Atendimento",
        env_list: list[dict[str, Any]],
        message: Optional["Mensagem"] = None,
    ) -> None:
        """Salva metadados do Evolution na mensagem.

        Args:
            attendance: Atendimento.
            env_list: Lista de envelopes.
        """
        try:
            last_env = env_list[-1]

            # Se mensagem foi passada, usa ela. Senão, busca a última do atendimento.
            mensagem = message
            if not mensagem:
                mensagens_qs = attendance.mensagens.order_by("-id")
                mensagem = mensagens_qs.first()

            if mensagem:
                api_key = str(last_env.get("apikey") or "")

                meta = dict(mensagem.metadados or {})
                meta["evolution"] = {
                    "api_key": api_key or None,
                }
                mensagem.metadados = meta
                mensagem.save(update_fields=["metadados"])

        except Exception:
            pass

    def _generate_and_register_response(
        self,
        message: "Mensagem",
        attendance: "Atendimento",
        env_list: list[dict[str, Any]],
    ) -> None:
        """Gera e registra resposta do bot.

        Args:
            message: Mensagem a responder.
            attendance: Atendimento.
            env_list: Lista de envelopes.
        """
        try:
            # Monta prompt baseado em intenções
            prompt_intent, has_known_intent = self._build_intent_prompt(
                message
            )

            logger.info(
                f"DEBUG: message_id={message.id}, has_known_intent={has_known_intent}"
            )
            logger.info(f"DEBUG: intent_detectado={message.intent_detectado}")

            # --- FAST-PATH: Roteamento Proativo ---
            # Se detectou intent crítico (falar_com_humano, etc), transfere
            # imediatamente sem chamar RAG/LLM para economizar tokens.
            critical_intents = {
                "falar_com_humano",
                "transferir_atendimento",
                "atendente_humano",
                "suporte_humano",
            }
            detected_tags = {
                list(intent.keys())[0].lower()
                for intent in (message.intent_detectado or [])
            }
            critical_match = detected_tags & critical_intents

            if critical_match:
                logger.info(
                    f"FAST-PATH: Intent crítico detectado: {critical_match}. "
                    "Transferindo imediatamente."
                )
                # Resposta de fast-path
                fast_path_msg = SERVICEHUB.MSG_TRANSFERENCIA_GENERICA
                message.registrar_resposta_bot(
                    resposta=fast_path_msg,
                    confianca=1.0,  # Alta confiança - intent explícito
                )
                # Obtém fluxos e inicia transferência
                fluxos_disponiveis = (
                    self._structure_manager.get_available_flows()
                )
                if fluxos_disponiveis:
                    fluxo = next(iter(fluxos_disponiveis.keys()))
                    logger.info(f"FAST-PATH: Transferindo para fluxo {fluxo}")
                    # Usa método do modelo Atendimento para transferência
                    attendance.apply_flow_by_description(fluxo)
                else:
                    # Atualiza status sem transferência
                    self._structure_manager._update_attendance_status_ongoing(
                        attendance
                    )
                return  # Sai sem chamar LLM
            # --- FIM FAST-PATH ---

            # Carrega histórico
            historico_atendimento = attendance.carregar_historico_mensagens(
                excluir_mensagem_id=message.id
            )

            # Busca dados de treinamento
            vector_conteudo = FeaturesCompose.generate_embeddings(
                message.conteudo
            )

            from smart_core_assistant_painel.app.ui.treinamento.models import (
                Documento,
            )

            # Busca retorna tupla (contexto, lista_ids) para rastreabilidade
            dados_treinamento, rag_doc_ids = (
                Documento.buscar_documentos_similares(
                    query_vec=vector_conteudo
                )
            )

            # Salva IDs dos documentos RAG para rastreabilidade
            if rag_doc_ids:
                if message.metadados is None:
                    message.metadados = {}
                message.metadados["rag_sources"] = rag_doc_ids
                message.save(update_fields=["metadados"])
                logger.info(
                    f"RAG: rag_sources={rag_doc_ids} salvos em mensagem {message.id}"
                )

            logger.info(
                f"DEBUG: dados_treinamento len={len(dados_treinamento)}, "
                f"rag_doc_ids={rag_doc_ids}"
            )

            # Obtém fluxos disponíveis
            fluxos_disponiveis = self._structure_manager.get_available_flows()

            # Decide se deve chamar IA
            has_training_data = len(dados_treinamento.strip()) > 0
            should_call_ai = has_known_intent or has_training_data

            logger.info(f"DEBUG: should_call_ai={should_call_ai}")

            if should_call_ai:
                self._call_ai_and_register(
                    message,
                    attendance,
                    prompt_intent,
                    historico_atendimento,
                    dados_treinamento,
                    fluxos_disponiveis,
                )
            else:
                logger.warning(
                    f"DEBUG: Fallback triggered for message {message.id}"
                )
                self._register_fallback_response(message, attendance)

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")

    def _build_intent_prompt(self, message: "Mensagem") -> tuple[str, bool]:
        """Constrói prompt baseado em intenções detectadas.

        Args:
            message: Mensagem com intenções.

        Returns:
            Tupla (prompt, has_known_intent).
        """
        # Usa prompt de intent externalizado ou fallback
        prompt_intent_system = SERVICEHUB.PROMPT_INTENT_SYSTEM
        if not prompt_intent_system:
            prompt_intent_system = (
                "INSTRUÇÕES DO SISTEMA - CONTEXTO PARA RESPOSTA\n"
                "Siga estritamente as orientações abaixo, em "
                "português claro e objetivo.\n"
                "Adapte a resposta ao contexto do atendimento atual."
            )

        prompt_lines: list[str] = [
            prompt_intent_system,
            "Intenções detectadas e orientações:",
        ]

        seen_tags: set[str] = set()
        has_known_intent = False
        index = 0

        for intent in message.intent_detectado:
            tag: str = list(intent.keys())[0]
            if tag in seen_tags:
                continue

            seen_tags.add(tag)
            index += 1

            # Busca comportamento para a tag
            from smart_core_assistant_painel.app.ui.treinamento.models import (
                QueryCompose,
            )

            qc = QueryCompose.objects.filter(tag=tag).first()

            if qc:
                has_known_intent = True
                behavior: str = " ".join(str(qc.comportamento).split()).strip()
                prompt_lines.append(f"{index}. [{tag}] {behavior}")
            else:
                # Busca comportamento similar por embedding
                intent_vector: list[float] = (
                    FeaturesCompose.generate_embeddings(
                        f"{tag}: {intent[tag]}"
                    )
                )
                comportamento: str | None = (
                    QueryCompose.buscar_comportamento_similar(intent_vector)
                )
                if comportamento:
                    prompt_lines.append(f"{index}. [{tag}] {comportamento}")

        # Usa footer de intent externalizado ou fallback
        prompt_intent_footer = SERVICEHUB.PROMPT_INTENT_FOOTER
        if not prompt_intent_footer:
            prompt_intent_footer = (
                "Se houver múltiplas intenções, priorize a ordem "
                "listada e mantenha a resposta concisa."
            )
        prompt_lines.append(prompt_intent_footer)

        return "\n".join(prompt_lines), has_known_intent

    def _call_ai_and_register(
        self,
        message: "Mensagem",
        attendance: "Atendimento",
        prompt_intent: str,
        historico_atendimento: dict[str, Any],
        dados_treinamento: str,
        fluxos_disponiveis: dict[str, str],
    ) -> None:
        """Chama IA e registra resposta.

        Args:
            message: Mensagem.
            attendance: Atendimento.
            prompt_intent: Prompt de intenções.
            historico_atendimento: Histórico.
            dados_treinamento: Documentos de treinamento.
            fluxos_disponiveis: Fluxos disponíveis.
        """
        logger.info(f"atd_process_ai_call contact_id={attendance.contato_id}")

        result = FeaturesCompose.analise_mensage(
            fluxos_disponiveis=fluxos_disponiveis,
            historico_atendimento=historico_atendimento,
            prompt_human=prompt_intent,
            context=message.conteudo,
            dados_treinamento=dados_treinamento,
        )

        # Registra resposta (signal enviará automaticamente)
        message.registrar_resposta_bot(
            resposta=result.resposta_bot,
            confianca=result.confiabilidade,
        )

        logger.info(
            f"atd_process_registered_bot_response msg_id={message.id} "
            f"len={len(result.resposta_bot or '')}"
        )

        # Atualiza status
        self._structure_manager._update_attendance_status_ongoing(attendance)

        # Transfere se necessário
        if result.transferir_atendimento and result.fluxo_transferencia:
            attendance.apply_flow_by_description(result.fluxo_transferencia)

    def _register_fallback_response(
        self, message: "Mensagem", attendance: "Atendimento"
    ) -> None:
        """Registra resposta fallback.

        Args:
            message: Mensagem.
            attendance: Atendimento.
        """
        # Usa mensagem de fallback externalizada
        texto_fallback = SERVICEHUB.MSG_FALLBACK_GERAL

        message.registrar_resposta_bot(
            resposta=texto_fallback,
            confianca=0.0,
        )

        logger.info(
            f"atd_process_registered_bot_response msg_id={message.id} "
            f"len={len(texto_fallback)}"
        )

        self._structure_manager._update_attendance_status_ongoing(attendance)
