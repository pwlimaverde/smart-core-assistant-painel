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
    from smart_core_assistant_painel.app.atendimentos.models import (
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
        from smart_core_assistant_painel.app.atendimentos.models import (
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
            from smart_core_assistant_painel.app.atendimentos.models import (
                Mensagem,
            )

            # Obtém mensagem
            mensagem: Mensagem = Mensagem.objects.get(id=message_id)

            # Conversão de mídia antes da análise de IA
            _MEDIA_TYPES = (
                "audioMessage",
                "imageMessage",
                "videoMessage",
                "documentMessage",
            )
            if mensagem.tipo in _MEDIA_TYPES:
                self._convert_media_context(mensagem, api_key=api_key)

            # --- Feedback Loop Check ---
            if self._check_and_process_feedback(mensagem, contact_id):
                logger.info(
                    f"Mensagem {message_id} processada como feedback. Encerrando fluxo."
                )
                return
            # ---------------------------

            # Analisa conteúdo (intenções e entidades)
            self._message_analyzer.analyze_message_content(message_id)

            # Atualiza mensagem com dados analisados
            mensagem.refresh_from_db(
                fields=["intent_detectado", "entidades_extraidas"]
            )

            # Configura atendimento
            atendimento = mensagem.atendimento

            # Preenche assunto e tags automaticamente
            self._auto_fill_subject(atendimento, mensagem)
            self._sync_intent_tags(atendimento, mensagem)

            self._configure_attendance(
                atendimento, api_key, env_list, message=mensagem
            )

            # Verifica se bot pode responder
            # Verifica se bot pode responder
            pode_responder = self._rules_engine.can_bot_respond(
                atendimento, api_key
            )

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

    def _fetch_media_base64_from_evolution(
        self,
        mensagem: "Mensagem",
        api_key: str = "",
    ) -> str:
        """Busca base64 de mídia descriptografada via Evolution API.

        Quando ``webhookBase64`` está desabilitado, a URL no metadata
        aponta para o CDN do WhatsApp (arquivo encriptado). Este método
        usa o endpoint ``getBase64FromMediaMessage`` da Evolution API
        para obter o conteúdo descriptografado.

        Args:
            mensagem: Mensagem com metadados contendo info da Evolution.

        Returns:
            String base64 do conteúdo de mídia, ou string vazia se falhar.
        """
        from smart_core_assistant_painel.app.evolution_sync.models import (
            EvolutionInstance,
        )
        from smart_core_assistant_painel.app.evolution_sync.services.evolution_api import (
            EvolutionWhatsAppService,
        )
        from smart_core_assistant_painel.app.tenants.models import (
            TenantEvolution,
        )

        meta = mensagem.metadados or {}

        # api_key vem do parâmetro (passado pelo orchestrator)
        # ou fallback para metadados (compatibilidade)
        if not api_key:
            evo = meta.get("evolution", {}) or {}
            api_key = evo.get("api_key", "")
        if not api_key:
            logger.debug(f"Mensagem {mensagem.id}: sem api_key Evolution.")
            return ""

        inst = EvolutionInstance.objects.filter(
            api_key=str(api_key), active=True
        ).first()
        if not inst:
            logger.debug(
                f"Mensagem {mensagem.id}: EvolutionInstance "
                f"não encontrada para api_key={api_key[:8]}..."
            )
            return ""

        # Resolver base_url via TenantEvolution
        base_url = ""
        tenant_id = getattr(inst, "tenant_id", None)
        if tenant_id:
            tenant_cfg = TenantEvolution.objects.filter(
                tenant_id=tenant_id
            ).first()
            if tenant_cfg and tenant_cfg.server_url:
                base_url = str(tenant_cfg.server_url).rstrip("/")
        if not base_url:
            logger.debug(
                f"Mensagem {mensagem.id}: base_url da Evolution "
                f"não encontrada (tenant_id={tenant_id})."
            )
            return ""

        # Construir key da mensagem WhatsApp
        contato = getattr(mensagem.atendimento, "contato", None)
        phone = str(getattr(contato, "telefone", "") or "").strip()
        if not phone:
            logger.debug(
                f"Mensagem {mensagem.id}: telefone do contato não disponível."
            )
            return ""

        message_key = {
            "remoteJid": f"{phone}@s.whatsapp.net",
            "fromMe": False,
            "id": mensagem.message_id_whatsapp or "",
        }

        # Campos comuns de encriptação do WhatsApp
        crypto_fields = {
            "url": meta.get("url", ""),
            "mimetype": meta.get("mimetype", ""),
            "mediaKey": meta.get("mediaKey", ""),
            "directPath": meta.get("directPath", ""),
            "fileSha256": meta.get("fileSha256", ""),
            "fileEncSha256": meta.get("fileEncSha256", ""),
        }
        if meta.get("fileLength"):
            crypto_fields["fileLength"] = meta["fileLength"]
        if meta.get("mediaKeyTimestamp"):
            crypto_fields["mediaKeyTimestamp"] = meta["mediaKeyTimestamp"]

        # Campos específicos por tipo de mídia
        if mensagem.tipo == "audioMessage":
            crypto_fields["seconds"] = meta.get("seconds", 0)
            crypto_fields["ptt"] = meta.get("ptt", False)
        elif mensagem.tipo == "videoMessage":
            crypto_fields["seconds"] = meta.get("seconds", 0)

        message_content = {mensagem.tipo: crypto_fields}

        if not meta.get("mediaKey"):
            logger.warning(
                f"Mensagem {mensagem.id}: sem mediaKey nos "
                "metadados. Evolution API não conseguirá "
                "descriptografar a mídia."
            )
            return ""

        service = EvolutionWhatsAppService()
        result = service.get_base64_from_media(
            base_url=base_url,
            api_key=str(api_key),
            instance_name=inst.name,
            message_key=message_key,
            message_content=message_content,
        )
        return result

    def _convert_media_context(
        self,
        mensagem: "Mensagem",
        api_key: str = "",
    ) -> None:
        """Converte metadados de mídia em texto contextual.

        Centraliza a conversão de conteúdo multimídia (áudio, imagem,
        vídeo, documento) em texto para análise de IA via
        FeaturesCompose.converter_contexto.

        Args:
            mensagem: Mensagem com metadados de mídia.
            api_key: Chave da API Evolution para buscar mídia.
        """
        try:
            metadados = mensagem.metadados or {}
            has_url = bool(metadados.get("url"))
            has_base64 = bool(metadados.get("base64"))

            logger.info(
                f"[MIDIA-CTX] >>> Iniciando processamento de mídia | "
                f"msg_id={mensagem.id} | tipo={mensagem.tipo} | "
                f"mimetype={metadados.get('mimetype')} | "
                f"fileLength={metadados.get('fileLength')} | "
                f"seconds={metadados.get('seconds')} | "
                f"fileName={metadados.get('fileName')} | "
                f"has_url={has_url} | has_base64={has_base64} | "
                f"base64_len={len(metadados.get('base64') or '')} | "
                f"meta_keys={sorted(metadados.keys())}"
            )

            if not has_url and not has_base64:
                logger.warning(
                    f"[MIDIA-CTX] Mensagem {mensagem.id}: "
                    f"{mensagem.tipo} sem URL/base64. Mantendo placeholder."
                )
                return

            # Se não tem base64, busca via Evolution API
            # (a URL do webhook aponta para o CDN do WhatsApp,
            # que é um arquivo encriptado).
            if not has_base64 and has_url:
                try:
                    base64_data = self._fetch_media_base64_from_evolution(
                        mensagem, api_key=api_key
                    )
                    if base64_data:
                        metadados = dict(metadados)
                        metadados["base64"] = base64_data
                        has_base64 = True
                        logger.info(
                            f"[MIDIA-CTX] Base64 obtido via Evolution API | "
                            f"msg_id={mensagem.id} | "
                            f"base64_len={len(base64_data)}"
                        )
                except Exception as e:
                    logger.warning(
                        f"[MIDIA-CTX] Falha ao buscar base64 via Evolution API "
                        f"para msg_id={mensagem.id}: {e}"
                    )

            logger.info(
                f"[MIDIA-CTX] Chamando converter_contexto | "
                f"msg_id={mensagem.id} | tipo={mensagem.tipo}"
            )

            texto_convertido = FeaturesCompose.converter_contexto(
                metadados=metadados,
                message_type=mensagem.tipo,
            )

            if texto_convertido and texto_convertido.strip():
                texto_final = texto_convertido.strip()
                conteudo_original = mensagem.conteudo
                mensagem.conteudo = texto_final
                meta = dict(metadados)
                meta["contexto_convertido"] = texto_final
                meta.pop("base64", None)
                mensagem.metadados = meta
                mensagem.save(update_fields=["conteudo", "metadados"])

                logger.info(
                    f"[MIDIA-CTX] <<< Conteúdo inserido na mensagem | "
                    f"msg_id={mensagem.id} | tipo={mensagem.tipo} | "
                    f"len_convertido={len(texto_final)} | "
                    f"placeholder_anterior={conteudo_original!r}\n"
                    f"---[MIDIA-CTX] TEXTO INTERPRETADO]---\n"
                    f"{texto_final}\n"
                    f"---[MIDIA-CTX] FIM TEXTO INTERPRETADO]---"
                )
            else:
                logger.warning(
                    f"[MIDIA-CTX] Conversão vazia para msg_id={mensagem.id}. "
                    "Mantendo placeholder."
                )
        except Exception as e:
            logger.error(
                f"[MIDIA-CTX] Erro ao converter mídia da msg_id={mensagem.id}: "
                f"{e}. Continuando com placeholder."
            )

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
            from smart_core_assistant_painel.app.operacional.models import (
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

            # Reabilita o bot ao trocar de contexto de instância,
            # permitindo que processe a interação e detecte
            # transferência
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
            from smart_core_assistant_painel.app.operacional.models import (
                AppInstance,
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
                f"message_id={message.id}, "
                f"has_known_intent={has_known_intent}, "
                f"intent_detectado={message.intent_detectado}"
            )

            # Detecta intents de transferência já identificados
            # pela análise prévia (antes de chamar a LLM)
            transfer_intents = {
                "falar_com_humano",
                "transferir_atendimento",
                "transferencia_atendente",
                "atendente_humano",
                "suporte_humano",
            }
            detected_tags = {
                list(intent.keys())[0].lower()
                for intent in (message.intent_detectado or [])
            }
            is_transfer = bool(detected_tags & transfer_intents)

            # Carrega histórico
            historico_atendimento = attendance.carregar_historico_mensagens(
                excluir_mensagem_id=message.id
            )

            # Busca dados de treinamento
            vector_conteudo = FeaturesCompose.generate_embeddings(
                message.conteudo
            )

            from smart_core_assistant_painel.app.treinamento.models import (
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
                    f"RAG: rag_sources={rag_doc_ids} "
                    f"salvos em mensagem {message.id}"
                )

            logger.info(
                f"dados_treinamento len="
                f"{len(dados_treinamento)}, "
                f"rag_doc_ids={rag_doc_ids}"
            )

            # Obtém fluxos disponíveis
            fluxos_disponiveis = self._structure_manager.get_available_flows()

            # --- Transferência direta (sem LLM) ---
            # Se o intent de transferência já foi detectado e há
            # apenas 1 fluxo disponível, executa diretamente sem
            # depender da LLM para determinar o fluxo.
            if is_transfer and len(fluxos_disponiveis) == 1:
                fluxo = next(iter(fluxos_disponiveis.keys()))
                logger.info(
                    f"Transferência direta: intent "
                    f"detectado, fluxo único '{fluxo}'"
                )
                fast_msg = SERVICEHUB.MSG_TRANSFERENCIA_GENERICA
                message.registrar_resposta_bot(
                    resposta=fast_msg,
                    confianca=1.0,
                )
                ok = self._structure_manager.apply_transfer_flow(
                    attendance, fluxo
                )
                if not ok:
                    logger.error(
                        f"Falha na transferência direta para '{fluxo}'"
                    )
                    self._structure_manager._update_attendance_status_ongoing(
                        attendance
                    )
                return
            # --- Fim transferência direta ---

            # Verifica se há histórico de conversa
            has_active_history = (
                len(historico_atendimento.get("chat_history", [])) > 0
            )

            # Decide se deve chamar IA
            has_training_data = len(dados_treinamento.strip()) > 0

            should_call_ai = (
                has_active_history or has_known_intent or has_training_data
            )

            logger.info(
                f"should_call_ai={should_call_ai} "
                f"(history={has_active_history}, "
                f"intent={has_known_intent}, "
                f"rag={has_training_data})"
            )

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
                logger.warning(f"Fallback triggered for message {message.id}")
                self._register_fallback_response(message, attendance)

        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")

            # Fallback: se a LLM falhou mas o intent de
            # transferência já foi detectado, tenta transferir
            try:
                detected = {
                    list(i.keys())[0].lower()
                    for i in (message.intent_detectado or [])
                }
                fallback_intents = {
                    "falar_com_humano",
                    "transferir_atendimento",
                    "transferencia_atendente",
                    "atendente_humano",
                    "suporte_humano",
                }
                if detected & fallback_intents:
                    fast_msg = SERVICEHUB.MSG_TRANSFERENCIA_GENERICA
                    message.registrar_resposta_bot(
                        resposta=fast_msg,
                        confianca=0.8,
                    )
                    ok = self._structure_manager.apply_transfer_flow(
                        attendance
                    )
                    if ok:
                        logger.info(
                            f"Fallback: atendimento "
                            f"{attendance.id} "
                            f"transferido"
                        )
                    else:
                        logger.error("Fallback: nenhum fluxo disponível")
            except Exception as fallback_err:
                logger.error(
                    f"Fallback de transferência também falhou: {fallback_err}"
                )

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
            from smart_core_assistant_painel.app.treinamento.models import (
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
                "Se houver múltiplas intenções, processe as instruções de CADA UMA "
                "delas. Em seguida, combine as respostas em um texto organizado. "
                "Use listas e parágrafos curtos para separar os assuntos. "
                "Garanta que a resposta seja fluida, mas estruturada visualmente."
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

        # Transfere se necessário — apply_transfer_flow já
        # desabilita bot_pode_atender e seta etapa inicial
        if result.transferir_atendimento and result.fluxo_transferencia:
            ok = self._structure_manager.apply_transfer_flow(
                attendance,
                result.fluxo_transferencia,
            )
            if ok:
                logger.info(
                    f"Atendimento {attendance.id} "
                    f"transferido para "
                    f"'{result.fluxo_transferencia}'"
                )
                return  # Transferência concluída
            else:
                logger.error(
                    f"Falha ao transferir "
                    f"{attendance.id} para "
                    f"'{result.fluxo_transferencia}'"
                )

        # Fallback: atualiza status se NÃO transferiu
        self._structure_manager._update_attendance_status_ongoing(attendance)

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

    def _auto_fill_subject(
        self,
        attendance: "Atendimento",
        message: "Mensagem",
    ) -> None:
        """Preenche assunto automaticamente se vazio.

        Usa intents e entidades da mensagem para gerar
        um resumo curto como assunto do atendimento.

        Args:
            attendance: Atendimento a atualizar.
            message: Mensagem com intents/entidades.
        """
        if attendance.assunto:
            return

        parts: list[str] = []

        # Usa entidades como base do assunto
        for entity_dict in message.entidades_extraidas or []:
            for key, value in entity_dict.items():
                if key.lower() == "nome_contato":
                    continue
                val = str(value).strip()
                if val and len(val) <= 50 and val not in parts:
                    parts.append(val)
                if len(parts) >= 3:
                    break
            if len(parts) >= 3:
                break

        # Complementa com intents se não tem entidades
        if not parts:
            for intent_dict in message.intent_detectado or []:
                for tag in intent_dict.keys():
                    label = tag.replace("_", " ").capitalize()
                    if label not in parts:
                        parts.append(label)
                    if len(parts) >= 2:
                        break
                if len(parts) >= 2:
                    break

        if parts:
            assunto = " - ".join(parts)
            attendance.assunto = assunto[:200]
            attendance.save(update_fields=["assunto"])
            logger.info(
                f"Assunto auto-preenchido para "
                f"atendimento {attendance.id}: "
                f"{assunto}"
            )

    def _sync_intent_tags(
        self,
        attendance: "Atendimento",
        message: "Mensagem",
    ) -> None:
        """Sincroniza intents detectados como tags.

        Adiciona tags de intent (prefixadas com 'intent:')
        ao atendimento, evitando duplicatas.

        Args:
            attendance: Atendimento a atualizar.
            message: Mensagem com intents detectados.
        """
        if not message.intent_detectado:
            return

        tags: list[str] = list(attendance.tags or [])
        updated = False

        for intent_dict in message.intent_detectado:
            for tag_name in intent_dict.keys():
                tag = f"intent:{tag_name}"
                if tag not in tags:
                    tags.append(tag)
                    updated = True

        if updated:
            attendance.tags = tags
            attendance.save(update_fields=["tags"])
            logger.info(
                f"Tags atualizadas no atendimento {attendance.id}: {tags}"
            )

    def _check_and_process_feedback(
        self, message: "Mensagem", contact_id: int
    ) -> bool:
        """Verifica se a mensagem é um feedback para um atendimento recém-concluído.

        Args:
            message: Mensagem recebida.
            contact_id: ID do contato.

        Returns:
            bool: True se processado como feedback, False caso contrário.
        """
        try:
            from datetime import timedelta

            from django.utils import timezone
            from langchain_core.messages import HumanMessage

            from smart_core_assistant_painel.app.atendimentos.models import (
                Atendimento,
                StatusAtendimento,
            )
            from smart_core_assistant_painel.modules.ai_engine import (
                FeaturesCompose,
            )

            # Busca último atendimento resolvido deste contato
            # Ordena por data_fim decrescente
            last_atd = (
                Atendimento.objects.filter(
                    contato_id=contact_id,
                    status=StatusAtendimento.RESOLVIDO,
                )
                .exclude(data_fim__isnull=True)
                .order_by("-data_fim")
                .first()
            )

            if not last_atd or not last_atd.data_fim:
                return False

            # Verifica janela de tempo (10 minutos)
            if timezone.now() - last_atd.data_fim > timedelta(minutes=10):
                return False

            # Se já tem avaliação, ignora
            if last_atd.avaliacao:
                return False

            # Analisa se é feedback válido usando AI
            chat_history = [HumanMessage(content=message.conteudo or "")]

            try:
                resultado = FeaturesCompose.analise_avaliacao(chat_history)
            except Exception as e:
                logger.warning(f"Falha na análise de avaliação: {e}")
                return False

            # Atualiza atendimento anterior
            last_atd.avaliacao = resultado.nota
            if resultado.feedback_original:
                last_atd.feedback = resultado.feedback_original
            elif message.conteudo:
                last_atd.feedback = message.conteudo

            # Tags de sentimento
            tags = last_atd.tags or []
            # Remove tags de sentimento anteriores para evitar duplicidade
            tags = [t for t in tags if not t.startswith("sentimento:")]

            tag_sentimento = f"sentimento: {resultado.sentimento}"
            if tag_sentimento not in tags:
                tags.append(tag_sentimento)
            last_atd.tags = tags

            last_atd.save(update_fields=["avaliacao", "feedback", "tags"])

            logger.info(
                f"Feedback registrado para atendimento {last_atd.id}: "
                f"Nota={resultado.nota}, Sentimento={resultado.sentimento}"
            )

            # Envia agradecimento
            msg_agradecimento = (
                "Obrigado pelo seu feedback! Ele é muito importante para nós."
            )

            # [Task 26.5] Taggear mensagem como feedback para mascarar no Trello
            if message.metadados is None:
                message.metadados = {}
            # Copia para garantir que é um dicionário mutável de Python e não um objeto proxy
            meta = dict(message.metadados)
            meta["is_feedback"] = True

            # [FIX] Injeta API Key da instância original para envio correto
            ctx = last_atd.contexto_conversa or {}
            api_key = ctx.get("api_key")
            if api_key:
                meta["evolution"] = {"api_key": str(api_key)}
                logger.info(
                    f"API Key {api_key} injetada na resposta de feedback"
                )

            message.metadados = meta
            # Salva metadados antes de registrar resposta (que já salva, mas melhor garantir)
            message.save(update_fields=["metadados"])

            message.registrar_resposta_bot(msg_agradecimento, 1.0)

            # Cancela o atendimento "temporário" criado apenas para esta mensagem
            current_atd = message.atendimento
            if current_atd and current_atd.id != last_atd.id:
                if current_atd.mensagens.count() <= 1:
                    current_atd.status = StatusAtendimento.CANCELADO
                    current_atd.save(update_fields=["status"])
                    logger.info(
                        f"Atendimento temporário {current_atd.id} cancelado após feedback."
                    )
                else:
                    # Se tem mais mensagens, talvez devêssemos marcar como resolvido também?
                    # Ou deixar como está.
                    pass

            return True

        except Exception as e:
            logger.error(f"Erro ao processar feedback: {e}")
            return False
