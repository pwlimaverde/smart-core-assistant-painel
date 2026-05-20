from typing import Any, Dict, List

from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Q
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    processar_mensagem_por_contato,
)
from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionWebhookEnvelope,
)
from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
    EvolutionInstance,
    WhiteList,
)
from smart_core_assistant_painel.app.evolution_sync.services import (
    sched_response_contact,
    set_buffer_contact,
)
from smart_core_assistant_painel.app.tenants.models import Tenant


class WebhookProcessor:
    """Processador de Webhooks da Evolution API.

    Responsável por orquestrar o processamento de mensagens recebidas,
    gerenciamento de instâncias e contatos, e agendamento de respostas.

    Attributes:
        tenant: Tenant associado ao webhook (opcional).
    """

    def __init__(self, tenant: Tenant | None = None) -> None:
        """Inicializa o processador com um tenant opcional.

        Args:
            tenant: Tenant associado às mensagens recebidas.
        """
        self.tenant = tenant

    def process_webhook(
        self,
        payload: Dict[str, Any],
        envelopes: List[EvolutionWebhookEnvelope],
    ) -> Dict[str, Any]:
        """Processa o webhook recebido.

        Args:
            payload: O payload bruto recebido.
            envelopes: Lista de envelopes normalizados.

        Returns:
            Dict[str, Any]: Resultado do processamento.
        """
        # Despacha eventos especiais antes de processar mensagens inbound
        if envelopes:
            first = envelopes[0]
            event_raw = first.event or ""
            # MESSAGE_UPDATE → atualiza status_envio das mensagens
            if event_raw == "MESSAGE_UPDATE":
                try:
                    self._handle_message_update(payload)
                except Exception as exc:
                    logger.error(f"Erro ao processar MESSAGE_UPDATE: {exc}")
                return {"status": "ok", "event": "MESSAGE_UPDATE"}
            # PRESENCE → notifica presença do contato via SSE (best-effort)
            if event_raw == "PRESENCE":
                try:
                    self._handle_presence(payload)
                except Exception as exc:
                    logger.warning(f"Erro ao processar PRESENCE: {exc}")
                return {"status": "ok", "event": "PRESENCE"}
            # CONTACTS → baixa profilePictureUrl para Contato.foto_perfil
            if event_raw == "CONTACTS":
                try:
                    self._handle_contacts(payload)
                except Exception as exc:
                    logger.warning(f"Erro ao processar CONTACTS: {exc}")
                return {"status": "ok", "event": "CONTACTS"}
            # CONNECTION → atualiza connection_state da instância (Connected/
            # Disconnected do Go). Fonte da verdade do estado, sem depender
            # do polling do navegador.
            if event_raw == "CONNECTION":
                try:
                    self._handle_connection(payload)
                except Exception as exc:
                    logger.warning(f"Erro ao processar CONNECTION: {exc}")
                return {"status": "ok", "event": "CONNECTION"}

        valid_envelopes = []

        for e in envelopes:
            # Safety Check: Ensure contact has JID
            if not e.contact.jid:
                logger.warning(
                    f"Ignoring envelope - missing contact JID. Event: {e.event}"
                )
                continue

            # Verificações de ignorar mensagem
            if self._should_ignore_message(e):
                continue

            # Processa mensagens enviadas pela própria instância (atendente)
            if e.from_me:
                try:
                    self._handle_from_me_message(e, payload)
                except Exception as exc:
                    logger.error(f"Error handling from_me message: {exc}")
                continue

            # Verificação de duplicidade de mensagem
            if self._is_duplicate_message(e):
                continue

            valid_envelopes.append(e)

        if not valid_envelopes:
            return {"status": "ignored_or_processed_from_me"}

        # Processar o primeiro envelope para obter instância e contato (assumindo mesmo contexto)
        first_env = valid_envelopes[0]
        instance = self._get_or_create_instance(first_env, payload)
        evo_contact = self._resolve_contact(instance, first_env)

        # Garantir que o contato principal existe e está vinculado
        if not evo_contact.contact_id:
            self._link_contact(
                evo_contact, first_env, from_me=first_env.from_me
            )
            evo_contact.refresh_from_db()

        # Bug 5: Só agendar resposta se contact_id é válido
        if not evo_contact.contact_id:
            logger.warning(
                f"Skipping scheduling - no valid contact_id for jid={first_env.contact.jid}"
            )
            return {"status": "ignored_no_contact", "processed": 0}

        # Agendar resposta (buffer)
        self._schedule_response(
            instance, evo_contact, valid_envelopes, first_env
        )

        logger.debug(f"Scheduled response instance {instance.name}")
        return {"status": "ok", "processed": len(valid_envelopes)}

    def _should_ignore_message(
        self, envelope: EvolutionWebhookEnvelope
    ) -> bool:
        """Verifica se a mensagem deve ser ignorada com base nas regras de negócio."""

        # 1. Mensagens de Grupo
        if self._is_group_message(envelope):
            return True

        # 2. Comunicação entre Instâncias (Internal Loop)
        if self._is_internal_instance_communication(envelope):
            return True

        # 3. Whitelist (Gestão)
        if self._is_whitelist_contact(envelope):
            return True

        return False

    def _is_group_message(self, envelope: EvolutionWebhookEnvelope) -> bool:
        """Verifica se é mensagem de grupo.

        Mensagens de grupo NÃO devem virar atendimentos individuais (o
        ``push_name`` nesses eventos é do remetente do grupo, não do contato
        no sentido individual — vinculá-lo a um Contato corromperia o nome
        do contato real). Logamos com warning para visibilidade.
        """
        if envelope.contact.is_group():
            logger.warning(
                f"[group-skip] Ignorando mensagem de grupo "
                f"jid={envelope.contact.jid!r} "
                f"push_name={envelope.profile.push_name!r}"
            )
            return True

        # Verificação extra por JID (fallback se ``is_group()`` falhar)
        jid = envelope.contact.jid or ""
        if jid.endswith("@g.us"):
            logger.warning(
                f"[group-skip] Ignorando evento por JID de grupo {jid!r}"
            )
            return True

        return False

    def _is_internal_instance_communication(
        self, envelope: EvolutionWebhookEnvelope
    ) -> bool:
        """Verifica se é comunicação entre instâncias internas."""
        other_phone = envelope.contact.phone
        jid_check = envelope.contact.jid or ""

        # Verificação por telefone
        if other_phone:
            phone_variations = self._get_phone_variations(other_phone)

            instance_query = Q()
            for phone_var in phone_variations:
                instance_query |= Q(phone_number=phone_var) | Q(name=phone_var)

            if EvolutionInstance.objects.filter(instance_query).exists():
                logger.info(
                    f"Ignoring interaction with instance {other_phone} (from_me={envelope.from_me})"
                )
                return True

        # Verificação por JID (fallback)
        if jid_check:
            jid_phone = jid_check.split("@")[0]
            if EvolutionInstance.objects.filter(
                phone_number=jid_phone
            ).exists():
                logger.info(
                    f"Ignoring interaction with instance JID {jid_check}"
                )
                return True

        return False

    def _is_whitelist_contact(
        self, envelope: EvolutionWebhookEnvelope
    ) -> bool:
        """Verifica se o contato está na Whitelist."""
        other_phone = envelope.contact.phone
        if not other_phone:
            return False

        phone_variations = self._get_phone_variations(other_phone)

        whitelist_query = Q()
        for phone_var in phone_variations:
            whitelist_query |= Q(phone_number=phone_var)

        if WhiteList.objects.filter(whitelist_query, active=True).exists():
            logger.info(f"Ignoring interaction with whitelist {other_phone}")
            return True

        return False

    def _is_duplicate_message(
        self, envelope: EvolutionWebhookEnvelope
    ) -> bool:
        """Verifica se a mensagem é duplicada."""
        msg_id = envelope.message.id
        if msg_id:
            cache_key = f"evo_msg_proc_{msg_id}"
            if cache.get(cache_key):
                logger.info(f"Ignoring duplicate message {msg_id}")
                return True
            # Marca mensagem como processada por 5 minutos
            cache.set(cache_key, "1", timeout=300)
        return False

    def _get_phone_variations(self, phone: str) -> List[str]:
        """Gera variações de telefone (com e sem 9º dígito)."""
        variations = [phone]
        if phone.startswith("55") and len(phone) in [12, 13]:
            if len(phone) == 13 and phone[4] == "9":
                # Remove 9th digit: 55 88 9 9714 1275 -> 55 88 9714 1275
                variations.append(phone[:4] + phone[5:])
            elif len(phone) == 12:
                # Add 9th digit: 55 88 9714 1275 -> 55 88 9 9714 1275
                variations.append(phone[:4] + "9" + phone[4:])
        return variations

    def _get_or_create_instance(
        self, envelope: EvolutionWebhookEnvelope, payload: Dict[str, Any]
    ) -> EvolutionInstance:
        """Obtém ou cria a instância Evolution no banco de dados."""
        inst_name = envelope.instance
        inst_id = envelope.instance_id
        api_key = str(envelope.apikey or "")
        name_val = str(inst_name or inst_id or "")
        # phone_number tem limite de 20 caracteres no banco
        phone_number_val = name_val[:20] if name_val else ""

        instance = None

        # 1. Tentar buscar por instance_id se disponível
        if inst_id:
            instance = EvolutionInstance.objects.filter(
                instance_id=inst_id
            ).first()

        # 2. Se não achou (ou sem ID), buscar por nome para evitar duplicidade
        if not instance and inst_name:
            instance = EvolutionInstance.objects.filter(name=inst_name).first()

        if instance:
            # Atualiza campos se necessário
            update_fields: list[str] = []
            if inst_id and instance.instance_id != inst_id:
                instance.instance_id = inst_id
                update_fields.append("instance_id")
            if name_val and instance.name != name_val:
                instance.name = name_val
                update_fields.append("name")
            if api_key and instance.api_key != api_key:
                instance.api_key = api_key
                update_fields.append("api_key")
            if phone_number_val and instance.phone_number != phone_number_val:
                instance.phone_number = phone_number_val
                update_fields.append("phone_number")
            # Associar tenant_id se ainda não tiver e temos um tenant
            if self.tenant and not instance.tenant_id:
                instance.tenant_id = self.tenant.id
                update_fields.append("tenant_id")

            if update_fields:
                instance.save(update_fields=update_fields)
        else:
            # Cria nova instância com tratamento de erro de integridade
            try:
                instance = EvolutionInstance.objects.create(
                    instance_id=inst_id or None,
                    name=name_val,
                    api_key=api_key,
                    phone_number=phone_number_val,
                    tenant_id=self.tenant.id if self.tenant else None,
                )
            except IntegrityError:
                # Se falhar por duplicidade (race condition), tenta buscar novamente
                logger.warning(
                    f"IntegrityError creating instance {inst_id}. Retrying fetch."
                )
                if inst_id:
                    instance = EvolutionInstance.objects.filter(
                        instance_id=inst_id
                    ).first()
                if not instance and inst_name:
                    instance = EvolutionInstance.objects.filter(
                        name=inst_name
                    ).first()

                if not instance:
                    # Se ainda assim não encontrar, algo estranho aconteceu
                    logger.error(
                        f"Failed to recover instance {inst_id} after IntegrityError"
                    )
                    raise

        # Sincroniza AppInstance para manter paridade operacional
        self._sync_app_instance(instance)

        return instance

    def _sync_app_instance(
        self, instance: EvolutionInstance
    ) -> None:
        """Sincroniza AppInstance com a EvolutionInstance.

        Garante que exista um AppInstance correspondente para
        manter paridade operacional (roteamento de departamento,
        atendente, etc.). O campo resposta_bot NÃO é
        sobrescrito — é controlado exclusivamente pelo painel.

        Args:
            instance: EvolutionInstance a sincronizar.
        """
        try:
            from smart_core_assistant_painel.app.operacional.models import (
                AppInstance,
            )

            if not instance.api_key:
                return

            AppInstance.objects.update_or_create(
                api_key=instance.api_key,
                defaults={
                    "channel": "evolution_api",
                    "display_name": instance.name,
                    "active": instance.active,
                },
            )
        except Exception as e:
            logger.warning(
                f"Falha ao sincronizar AppInstance "
                f"para {instance.name}: {e}"
            )

    def _resolve_contact(
        self, instance: EvolutionInstance, envelope: EvolutionWebhookEnvelope
    ) -> EvolutionContact:
        """Resolve o contato Evolution (busca ou cria)."""
        jid = envelope.contact.jid
        lid = envelope.contact.lid
        addressing_mode = envelope.contact.addressing_mode

        qs = EvolutionContact.objects.filter(instance=instance)

        if not jid:
            raise ValueError("Cannot resolve contact without JID")

        if jid:
            qs = qs.filter(jid=jid)

            # Check if JID belongs to a managed instance
            jid_phone = jid.split("@")[0]
            if EvolutionInstance.objects.filter(
                phone_number=jid_phone
            ).exists():
                logger.info(
                    f"Skipping EvolutionContact creation for instance JID {jid}"
                )
                # We still proceed to try and find it, but we won't create it if not found?
                # Actually, the original logic was a bit fuzzy here.
                # If it's an instance, we probably shouldn't create a contact for it.
                pass

        if not qs.exists() and lid:
            qs = EvolutionContact.objects.filter(instance=instance, lid=lid)

        evo_contact = qs.first()
        if evo_contact is None:
            evo_contact = EvolutionContact.objects.create(
                instance=instance,
                jid=jid,
                lid=lid,
                addressing_mode=addressing_mode,
            )
        else:
            update_fields_contact: list[str] = []
            if jid and evo_contact.jid != jid:
                evo_contact.jid = jid
                update_fields_contact.append("jid")
            if lid and evo_contact.lid != lid:
                evo_contact.lid = lid
                update_fields_contact.append("lid")
            if (
                addressing_mode
                and evo_contact.addressing_mode != addressing_mode
            ):
                evo_contact.addressing_mode = addressing_mode
                update_fields_contact.append("addressing_mode")
            if update_fields_contact:
                evo_contact.save(update_fields=update_fields_contact)

        return evo_contact

    @staticmethod
    def _normalize_push_name(raw: str | None) -> str:
        """Normaliza o ``push_name`` vindo da Evolution.

        - Strip whitespace.
        - Descarta se ficar vazio.
        - Descarta se contiver apenas dígitos/espaços/símbolos de telefone
          (parece um número, não um nome real).
        - Trunca em 100 caracteres.
        """
        if not raw:
            return ""
        cleaned = raw.strip()
        if not cleaned:
            return ""
        # "parece telefone": só dígitos/espaços/+ - ()
        only_phone_chars = all(c.isdigit() or c in " +-()" for c in cleaned)
        if only_phone_chars:
            return ""
        return cleaned[:100]

    def _link_contact(
        self,
        evo_contact: EvolutionContact,
        envelope: EvolutionWebhookEnvelope,
        from_me: bool = False,
    ) -> None:
        """Vincula ou cria um Contato do sistema principal.

        Regras de nome:
            - ``nome_contato`` é fonte da verdade *manual* — só é gravado na
              criação se o push_name normalizado vier não-vazio; NUNCA é
              sobrescrito depois.
            - ``nome_perfil_whatsapp`` reflete o último push_name visto e é
              atualizado a cada webhook (quando diferente do atual).
        """
        push_name_raw = envelope.profile.push_name
        push_name = "" if from_me else self._normalize_push_name(push_name_raw)
        phone = envelope.contact.phone

        # Bug 2: Não criar contatos sem telefone
        if not phone:
            logger.debug(
                f"Skipping contact creation: no phone available "
                f"(push_name_raw={push_name_raw!r})"
            )
            return

        # Bug 3: Não criar contatos para números de instâncias internas
        if EvolutionInstance.objects.filter(
            phone_number=str(phone), active=True
        ).exists():
            logger.info(
                f"Skipping contact creation for own instance phone {phone}"
            )
            return

        contato, created_contact = Contato.objects.get_or_create(
            telefone=str(phone),
            defaults={
                "nome_contato": push_name,
                "nome_perfil_whatsapp": push_name,
                "ativo": True,
                "metadados": {},
            },
        )

        if not created_contact and push_name:
            # Atualiza nome_perfil_whatsapp sempre que mudar (último push_name
            # visto). NÃO toca em nome_contato — esse é manual.
            if (contato.nome_perfil_whatsapp or "") != push_name:
                contato.nome_perfil_whatsapp = push_name
                contato.save(update_fields=["nome_perfil_whatsapp"])

        if evo_contact.contact != contato:
            evo_contact.contact = contato
            evo_contact.save(update_fields=["contact"])

    def _schedule_response(
        self,
        instance: EvolutionInstance,
        evo_contact: EvolutionContact,
        envelopes: List[EvolutionWebhookEnvelope],
        first_env: EvolutionWebhookEnvelope,
    ) -> None:
        """Agenda a resposta para o contato."""
        # Ensure phone is updated in main contact if missing
        if first_env.contact.phone:
            contato = evo_contact.contact
            if contato and not getattr(contato, "telefone", None):
                contato.telefone = str(first_env.contact.phone)
                contato.save(update_fields=["telefone"])

        # Buffer messages for processing
        if evo_contact.contact_id:
            for env in envelopes:
                env_dict = env.to_dict()
                if instance.id:
                    if "evolution" not in env_dict:
                        env_dict["evolution"] = {}
                    env_dict["evolution"]["instance_db_id"] = instance.id

                set_buffer_contact(int(evo_contact.contact_id), env_dict)

        sched_payload: Dict[str, Any] = {
            "contact_id": evo_contact.contact_id,
            "api_key": first_env.apikey,
            "message": first_env.message.to_dict()
            if first_env.message
            else {},
        }

        logger.debug(
            f"Scheduling response for contact_id={evo_contact.contact_id}. "
            f"Payload: {sched_payload}"
        )

        sched_response_contact(sched_payload)

    def _handle_from_me_message(
        self, envelope: EvolutionWebhookEnvelope, payload: Dict[str, Any]
    ) -> None:
        """Processa mensagens enviadas pela própria instância."""
        if envelope.event == "send.message":
            logger.debug(
                f"Ignoring send.message event (bot automated message): {envelope.message.id}"
            )
            return

        if envelope.event == "messages.update":
            logger.debug(
                f"Ignoring messages.update event for fromMe message: {envelope.message.id}"
            )
            return

        instance = self._get_or_create_instance(envelope, payload)

        if envelope.sender_jid:
            phone = envelope.sender_jid.split("@")[0]
            if phone.isdigit() and len(phone) <= 20:
                if instance.phone_number != phone:
                    instance.phone_number = phone
                    instance.save(update_fields=["phone_number"])

        evo_contact = self._resolve_contact(instance, envelope)

        if not evo_contact.contact_id:
            self._link_contact(evo_contact, envelope, from_me=True)
            evo_contact.refresh_from_db()

        if evo_contact.contact_id:
            processar_mensagem_por_contato(
                contato_id=int(evo_contact.contact_id),
                conteudo=envelope.message.text,
                message_type=envelope.message.type or "conversation",
                message_id=envelope.message.id or "",
                metadados=envelope.message.metadata,
                nome_perfil_whatsapp=envelope.profile.push_name,
                from_me=True,
                api_key=envelope.apikey,
            )

    def _handle_message_update(self, payload: Dict[str, Any]) -> None:
        """Processa evento MESSAGE_UPDATE do Evolution Go para atualizar status_envio.

        O Evolution Go emite este evento quando o WhatsApp confirma entrega
        (✓✓) ou leitura (✓✓ azul) de uma mensagem enviada.

        Payload esperado (Evolution Go)::

            {
                "event": "MESSAGE_UPDATE",
                "instance": "atendimento",
                "data": {
                    "key": {"id": "MSGID...", "fromMe": true, "remoteJid": "..."},
                    "update": {"status": "DELIVERY_ACK" | "READ"}
                }
            }

        Status Evolution Go → status_envio do modelo:
        - ``SERVER_ACK``   → ``"sent"``
        - ``DELIVERY_ACK`` → ``"delivered"``
        - ``READ``         → ``"read"``

        Args:
            payload: Payload bruto do webhook.
        """


        data = payload.get("data", {})
        if isinstance(data, list):
            # batch: processa cada item
            for item in data:
                if isinstance(item, dict):
                    self._process_single_message_update(item)
            return

        if isinstance(data, dict):
            self._process_single_message_update(data)

    def _process_single_message_update(self, data: Dict[str, Any]) -> None:
        """Processa um único item de MESSAGE_UPDATE.

        Args:
            data: Um dict dentro de ``payload["data"]``.
        """
        from django.utils import timezone

        from smart_core_assistant_painel.app.atendimentos.models import (
            Mensagem,
        )

        key = data.get("key", {})
        update = data.get("update", {})
        message_id = key.get("id", "")
        status_raw = update.get("status", "")

        if not message_id or not status_raw:
            return

        # Mapeamento Evolution Go status → choices do modelo
        _STATUS_MAP: dict[str, str] = {
            "SERVER_ACK": "sent",
            "DELIVERY_ACK": "delivered",
            "READ": "read",
            "PLAYED": "read",  # áudios ouvidos
        }
        novo_status = _STATUS_MAP.get(status_raw.upper(), "")
        if not novo_status:
            logger.debug(f"MESSAGE_UPDATE: status desconhecido {status_raw!r}")
            return

        # Busca a Mensagem pelo message_id_whatsapp
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp=message_id
        ).first()

        if not mensagem:
            logger.debug(
                f"MESSAGE_UPDATE: mensagem {message_id!r} não encontrada no banco"
            )
            return

        update_fields: list[str] = ["status_envio"]
        mensagem.status_envio = novo_status

        now = timezone.now()
        if novo_status == "delivered" and not mensagem.data_entregue:
            mensagem.data_entregue = now
            update_fields.append("data_entregue")
        elif novo_status == "read" and not mensagem.data_lida:
            mensagem.data_lida = now
            update_fields.append("data_lida")
            if not mensagem.data_entregue:
                mensagem.data_entregue = now
                update_fields.append("data_entregue")

        mensagem.save(update_fields=list(set(update_fields)))
        logger.info(
            f"MESSAGE_UPDATE: msg_id={message_id} → status_envio={novo_status}"
        )

    def _handle_connection(self, payload: Dict[str, Any]) -> None:
        """Processa evento de conexão do Evolution Go (``Connected``/``Disconnected``).

        Persiste ``connection_state`` na ``EvolutionInstance`` para que a tela
        reflita o estado real sem depender do polling do navegador (que pode
        ter parado quando o usuário trocou de aba para escanear o QR).

        Payload Evolution Go (aproximado)::

            {"event": "Connected", "instance": "atendimento", "data": {...}}
        """
        from django.utils import timezone

        from smart_core_assistant_painel.app.evolution_sync.models import (
            EvolutionInstance,
        )

        raw_event = str(payload.get("event", ""))
        instance_name = payload.get("instance")
        if not instance_name:
            return

        ev = raw_event.upper().replace(".", "_")
        is_down = any(
            k in ev for k in ("DISCONNECT", "LOGOUT", "LOGGED_OUT", "CLOSE")
        )
        state = "close" if is_down else "open"

        inst = EvolutionInstance.objects.filter(
            name=instance_name, active=True
        ).first()
        if not inst:
            logger.warning(
                f"CONNECTION: instância {instance_name!r} não encontrada"
            )
            return

        inst.connection_state = state
        inst.last_connection_state = raw_event
        inst.last_state_check = timezone.now()
        inst.save(
            update_fields=[
                "connection_state",
                "last_connection_state",
                "last_state_check",
            ]
        )
        logger.info(
            f"CONNECTION: instance={instance_name!r} "
            f"raw={raw_event!r} state={state!r}"
        )

    def _handle_presence(self, payload: Dict[str, Any]) -> None:
        """Processa evento PRESENCE do Evolution Go e publica SSE ``presence.update``.

        Payload Evolution Go::

            {
                "event": "PRESENCE",
                "instance": "atendimento",
                "data": {
                    "id": "5511999999999@s.whatsapp.net",
                    "presences": {
                        "5511999999999@s.whatsapp.net": {
                            "lastKnownPresence": "composing" | "recording" | "available" | "paused"
                        }
                    }
                }
            }

        O JID do contato é usado para localizar o ``Atendimento`` ativo
        e publicar SSE ``presence.update`` com o estado.
        """
        from smart_core_assistant_painel.app.atendimento_unificado.services.realtime_publisher import (
            publish_event,
        )
        from smart_core_assistant_painel.app.evolution_sync.models import (
            EvolutionContact,
        )

        data = payload.get("data", {}) or {}
        presences: dict = data.get("presences", {}) or {}

        for jid, presence_info in presences.items():
            state = str(
                (presence_info or {}).get("lastKnownPresence", "available")
            ).lower()

            # Busca contato pelo JID
            evo_contact = (
                EvolutionContact.objects.select_related("contact")
                .filter(jid=jid, active=True)
                .first()
            )
            if not evo_contact or not evo_contact.contact_id:
                continue

            # Busca atendimento ativo do contato
            from smart_core_assistant_painel.app.atendimentos.models import (
                Atendimento,
                StatusAtendimento,
            )
            atend = (
                Atendimento.objects.filter(
                    contato_id=evo_contact.contact_id,
                )
                .exclude(
                    status__in=[
                        StatusAtendimento.RESOLVIDO,
                        StatusAtendimento.CANCELADO,
                    ]
                )
                .order_by("-data_inicio")
                .first()
            )
            if not atend:
                continue

            publish_event(
                "presence.update",
                {
                    "atendimento_id": atend.id,
                    "jid": jid,
                    "state": state,
                },
            )
            logger.debug(
                f"PRESENCE: atendimento={atend.id}, jid={jid!r}, state={state!r}"
            )

    def _handle_contacts(self, payload: Dict[str, Any]) -> None:
        """Processa evento CONTACTS (Go) / CONTACTS_UPDATE (v2) e sincroniza avatar.

        Para cada contato vindo no payload, localiza o ``Contato`` pelo
        telefone (extraído do ``id``/``remoteJid``) e baixa a imagem de
        ``profilePictureUrl`` para ``Contato.foto_perfil`` quando a URL
        for diferente da última sincronizada (``foto_perfil_url_origem``).

        Formatos suportados:
            - Evolution Go: ``payload["data"]`` é dict único ou lista de dicts
              ``{id, profilePictureUrl, pushName?, name?}``.
            - Evolution v2: ``payload["data"]`` é lista de dicts com
              ``{remoteJid, profilePicUrl, pushName?}``.
        """
        import re
        from urllib.parse import urlparse

        import requests
        from django.core.files.base import ContentFile

        data_obj: Any = payload.get("data")
        if isinstance(data_obj, dict):
            contacts_raw: List[Dict[str, Any]] = [data_obj]
        elif isinstance(data_obj, list):
            contacts_raw = [c for c in data_obj if isinstance(c, dict)]
        else:
            return

        for contact_data in contacts_raw:
            jid = str(
                contact_data.get("id")
                or contact_data.get("remoteJid")
                or ""
            )
            profile_url = str(
                contact_data.get("profilePictureUrl")
                or contact_data.get("profilePicUrl")
                or ""
            ).strip()
            if not jid or not profile_url:
                continue

            telefone = re.sub(r"\D", "", jid.split("@")[0])
            if not telefone:
                continue

            contato = Contato.objects.filter(telefone=telefone).first()
            if not contato:
                continue

            if contato.foto_perfil_url_origem == profile_url and contato.foto_perfil:
                continue

            try:
                resp = requests.get(profile_url, timeout=15)
                if not resp.ok or not resp.content:
                    logger.debug(
                        f"CONTACTS: download avatar falhou jid={jid!r} "
                        f"status={resp.status_code}"
                    )
                    continue

                ext = (urlparse(profile_url).path.rsplit(".", 1)[-1] or "jpg").lower()
                if ext not in {"jpg", "jpeg", "png", "webp"}:
                    ext = "jpg"
                filename = f"{telefone}.{ext}"

                contato.foto_perfil.save(
                    filename, ContentFile(resp.content), save=False
                )
                contato.foto_perfil_url_origem = profile_url
                contato.save(
                    update_fields=["foto_perfil", "foto_perfil_url_origem"]
                )
                logger.info(
                    f"CONTACTS: avatar atualizado contato_id={contato.pk} "
                    f"telefone={telefone}"
                )
            except requests.RequestException as exc:
                logger.warning(
                    f"CONTACTS: erro baixando avatar jid={jid!r}: {exc}"
                )
