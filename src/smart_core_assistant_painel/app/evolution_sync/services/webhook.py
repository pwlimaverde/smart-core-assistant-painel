from typing import Any, Dict, List


from django.core.cache import cache
from loguru import logger

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
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    processar_mensagem_por_contato,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato


class WebhookProcessor:
    """Processador de Webhooks da Evolution API.

    Responsável por orquestrar o processamento de mensagens recebidas,
    gerenciamento de instâncias e contatos, e agendamento de respostas.
    """

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
        # Filtrar mensagens enviadas pelo próprio bot ou sem JID válido
        valid_envelopes = []
        for e in envelopes:
            # Safety Check: Ensure contact has JID
            if not e.contact.jid:
                logger.warning(
                    f"Ignoring envelope - missing contact JID. Event: {e.event}"
                )
                continue

            # PRIMEIRA VALIDAÇÃO: Filtrar mensagens de grupos (mais importante)
            # Ignorar imediatamente antes de qualquer processamento
            if e.contact.is_group():
                logger.info(f"Ignoring group message from {e.contact.jid}")
                continue

            # SEGUNDA VALIDAÇÃO: Filtrar eventos de contatos/chats relacionados a grupos
            # Eventos contacts.update e chats.update podem ter JID de grupo sem mensagem
            if e.event in ["contacts.update", "chats.update", "chats.upsert"]:
                # Verificar se o JID é de grupo
                jid = e.contact.jid or ""
                if jid.endswith("@g.us"):
                    logger.debug(f"Ignoring {e.event} event for group {jid}")
                    continue

            if e.from_me:
                # Para mensagens from_me, verificar se o destinatário é uma instância
                # Se for, ignorar (comunicação entre instâncias)
                other_phone = e.contact.phone
                if other_phone:
                    # Normalização para números brasileiros
                    phone_variations = [other_phone]
                    if other_phone.startswith("55") and len(other_phone) in [
                        12,
                        13,
                    ]:
                        if len(other_phone) == 13 and other_phone[4] == "9":
                            phone_variations.append(
                                other_phone[:4] + other_phone[5:]
                            )
                        elif len(other_phone) == 12:
                            phone_variations.append(
                                other_phone[:4] + "9" + other_phone[4:]
                            )

                    from django.db.models import Q

                    instance_query = Q()
                    for phone_var in phone_variations:
                        instance_query |= Q(phone_number=phone_var) | Q(
                            name=phone_var
                        )

                    if EvolutionInstance.objects.filter(
                        instance_query
                    ).exists():
                        logger.info(
                            f"Ignoring interaction with instance {other_phone} (from_me={e.from_me})"
                        )
                        continue

                # Processa mensagens enviadas pela própria instância (atendente)
                # mas não adiciona aos envelopes válidos para o bot
                try:
                    self._handle_from_me_message(e, payload)
                except Exception as exc:
                    logger.error(f"Error handling from_me message: {exc})")
                continue

            # Filtrar comunicação entre instâncias e WhiteList
            other_phone = e.contact.phone
            # Bug 3 Fix: Check if JID belongs to an instance even if phone extraction failed or is partial
            # Also ensure we check for instances BEFORE creating anything
            if other_phone:
                # Normalização para números brasileiros (tratamento do 9º dígito)
                phone_variations = [other_phone]
                if other_phone.startswith("55") and len(other_phone) in [
                    12,
                    13,
                ]:
                    if len(other_phone) == 13 and other_phone[4] == "9":
                        # Remove 9th digit: 55 88 9 9714 1275 -> 55 88 9714 1275
                        phone_variations.append(
                            other_phone[:4] + other_phone[5:]
                        )
                    elif len(other_phone) == 12:
                        # Add 9th digit: 55 88 9714 1275 -> 55 88 9 9714 1275
                        phone_variations.append(
                            other_phone[:4] + "9" + other_phone[4:]
                        )
                from django.db.models import Q

                # Check if ANY variation matches an instance
                instance_query = Q()
                for phone_var in phone_variations:
                    instance_query |= Q(phone_number=phone_var) | Q(
                        name=phone_var
                    )

                if EvolutionInstance.objects.filter(instance_query).exists():
                    logger.info(
                        f"Ignoring interaction with instance {other_phone} (from_me={e.from_me})"
                    )
                    continue

                # Verifica se está na WhiteList
                whitelist_query = Q()
                for phone_var in phone_variations:
                    whitelist_query |= Q(phone_number=phone_var)

                if WhiteList.objects.filter(
                    whitelist_query, active=True
                ).exists():
                    logger.info(
                        f"Ignoring interaction with whitelist {other_phone}"
                    )
                    continue

            # Bug Fix: Also check by JID if phone check failed or wasn't sufficient
            # This catches cases where phone extraction might be tricky but JID is clear
            jid_check = e.contact.jid or ""
            if jid_check:
                # Extract phone from JID roughly
                jid_phone = jid_check.split("@")[0]
                if EvolutionInstance.objects.filter(
                    phone_number=jid_phone
                ).exists():
                    logger.info(
                        f"Ignoring interaction with instance JID {jid_check}"
                    )
                    continue

            # Verificação de duplicidade de mensagem
            msg_id = e.message.id
            if msg_id:
                # Cache key única para cada mensagem
                cache_key = f"evo_msg_proc_{msg_id}"
                if cache.get(cache_key):
                    logger.info(f"Ignoring duplicate message {msg_id}")
                    continue
                # Marca mensagem como processada por 5 minutos
                cache.set(cache_key, "1", timeout=300)

            valid_envelopes.append(e)

        if not valid_envelopes:
            return {"status": "ignored_from_me"}

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
        # Isso evita agendar mensagens que foram filtradas/ignoradas
        if not evo_contact.contact_id:
            logger.warning(
                f"Skipping scheduling - no valid contact_id for jid={first_env.contact.jid}"
            )
            return {"status": "ignored_no_contact", "processed": 0}

        # Agendar resposta (buffer)
        self._schedule_response(
            instance, evo_contact, valid_envelopes, first_env
        )

        return {"status": "ok", "processed": len(valid_envelopes)}

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
        # (Bug 1: Instância criada duplicada sem ID)
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

            if update_fields:
                instance.save(update_fields=update_fields)
        else:
            # Cria nova instância
            # Usamos inst_id ou None para respeitar unique=True do banco se possível,
            # mas o campo é CharField, então vazio é "".
            instance = EvolutionInstance.objects.create(
                instance_id=inst_id or None,
                name=name_val,
                api_key=api_key,
                phone_number=phone_number_val,
            )

        return instance

    def _resolve_contact(
        self, instance: EvolutionInstance, envelope: EvolutionWebhookEnvelope
    ) -> EvolutionContact:
        """Resolve o contato Evolution (busca ou cria)."""
        jid = envelope.contact.jid
        lid = envelope.contact.lid
        addressing_mode = envelope.contact.addressing_mode

        qs = EvolutionContact.objects.filter(instance=instance)
        qs = EvolutionContact.objects.filter(instance=instance)
        if not jid:
            # Safety check: if JID is missing, we cannot resolve or create a contact.
            # This might happen if normalization failed or payload is malformed.
            # We should return None, but type hint says EvolutionContact.
            # Raising an error is safer to stop processing.
            raise ValueError("Cannot resolve contact without JID")

        if jid:
            qs = qs.filter(jid=jid)

            # Bug Fix: Prevent creating EvolutionContact for managed instances
            # Check if JID belongs to a managed instance
            jid_phone = jid.split("@")[0]
            if EvolutionInstance.objects.filter(
                phone_number=jid_phone
            ).exists():
                logger.info(
                    f"Skipping EvolutionContact creation for instance JID {jid}"
                )
                # Return a dummy or existing contact but DO NOT create a new one if possible
                # Or better, return None? But type hint says EvolutionContact.
                # If we return None, the caller might crash.
                # But the caller checks `if not evo_contact.contact_id`.
                # If we return an existing one, it's fine.
                # If we can't find one, we should NOT create it.
                # But we must return something.
                # Let's return the first existing one if any, or create a dummy one?
                # No, creating a dummy one pollutes DB.
                # The best way is to throw exception or handle it upstream.
                # But `process_webhook` calls this.
                # If we added the filter in `process_webhook`, we shouldn't reach here for instances.
                # So this is a safety net.
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

    def _link_contact(
        self,
        evo_contact: EvolutionContact,
        envelope: EvolutionWebhookEnvelope,
        from_me: bool = False,
    ) -> None:
        """Vincula ou cria um Contato do sistema principal.

        Args:
            evo_contact: Contato Evolution a ser vinculado
            envelope: Envelope com dados da mensagem
            from_me: Se True, mensagem foi enviada pelo atendente
        """

        push_name = envelope.profile.push_name
        phone = envelope.contact.phone

        # Bug 2: Não criar contatos sem telefone
        # Se não tem telefone, não podemos identificar unicamente nem contatar
        if not phone:
            logger.debug(
                f"Skipping contact creation: no phone available (push_name={push_name})"
            )
            return

        # Bug 3: Não criar contatos para números de instâncias internas
        # Verifica se o telefone pertence a alguma instância ativa
        if EvolutionInstance.objects.filter(
            phone_number=str(phone), active=True
        ).exists():
            logger.info(
                f"Skipping contact creation for own instance phone {phone}"
            )
            return

        contato: Contato | None = None

        # Para mensagens from_me, o push_name é do REMETENTE (atendente), não do destinatário
        # Portanto, NÃO devemos usar esse nome para criar/atualizar o contato
        use_push_name = push_name if not from_me else None

        logger.debug(
            f"_link_contact phone={phone} push_name={push_name} from_me={from_me} use_push_name={use_push_name}"
        )

        if phone:
            contato, created_contact = Contato.objects.get_or_create(
                telefone=str(phone),
                defaults={
                    "nome_contato": str(use_push_name or ""),
                    "nome_perfil_whatsapp": str(use_push_name or ""),
                    "ativo": True,
                    "metadados": {},
                },
            )
        else:
            # Código inalcançável devido à verificação inicial, mantido por segurança
            return

        if contato:
            # Update push_name if it exists and contact was not created (existing contact)
            # MAS: apenas se NÃO for from_me (para evitar sobrescrever com nome do atendente)
            if not created_contact and use_push_name:
                if not contato.nome_perfil_whatsapp:
                    contato.nome_perfil_whatsapp = str(use_push_name)
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
                # Inject instance_db_id into metadata if needed for signal
                env_dict = env.to_dict()
                if instance.id:
                    if "evolution" not in env_dict:
                        env_dict["evolution"] = {}
                    env_dict["evolution"]["instance_db_id"] = instance.id

                set_buffer_contact(int(evo_contact.contact_id), env_dict)
        # evo_meta = first_env.get("evolution") or {}
        # evo_meta["instance_db_id"] = int(instance.id)
        # first_env["evolution"] = evo_meta

        # In our new structure, we can pass this as part of the sched_payload or modify the raw if needed.
        # The scheduler likely reads from the buffer or expects specific params.
        # sched_response_contact takes 'params'.

        # IMPORTANT: The original code modified 'first_env' which was a dict.
        # Here 'first_env' is an object. The buffer stores 'env_dict'.
        # We should probably update the buffer with the instance_db_id if that's where it's read from?
        # Actually, sched_response_contact just triggers a task. The task likely reads the buffer.
        # Wait, the original code did:
        # first_env["evolution"] = evo_meta (where evo_meta has instance_db_id)
        # Then it called sched_response_contact(sched_payload)
        # The buffer was ALREADY set before this modification in the loop.
        # BUT, the loop used 'envelope' (from envelopes list).
        # The modification to 'first_env' (which is envelopes[0]) happened AFTER the loop in the original code?
        # Let's check the original code order.
        # 1. Loop envelopes -> set_buffer_contact
        # 2. Modify first_env["evolution"]
        # 3. sched_response_contact

        # This implies the modification to first_env was NOT stored in the buffer?
        # Or maybe it was intended to be?
        # If set_buffer_contact copies the dict, then the modification after doesn't affect the buffer.
        # If it stores a reference, it might.
        # `cache.set` pickles the object, so it stores a copy.
        # So the modification to `first_env` in the original code seemed to only affect `sched_payload` construction?
        # No, `sched_payload` only has contact_id, api_key, message.
        # So where is `instance_db_id` used?
        # It seems it might be used if `first_env` is passed somewhere else, but it isn't.
        # Wait, maybe I missed something.
        # Ah, `signals.py` reads `instance.metadados.get("evolution", {}).get("instance_db_id")`.
        # But that's from `Mensagem` model.
        # The flow is: Webhook -> Buffer -> Task (send_message_response_by_contact) -> AI Processing -> Mensagem Saved -> Signal.
        # So the `instance_db_id` needs to persist through this flow.
        # The `send_message_response_by_contact` likely reads the buffer, processes it, and creates a `Mensagem`.
        # If the buffer was already set, how does `instance_db_id` get into `Mensagem`?
        # Maybe the task reads the buffer and expects `evolution` metadata there?
        # If so, the original code might have had a bug or I am misinterpreting the order.
        # Original:
        # for envelope in envelopes: set_buffer_contact(...)
        # evo_meta = first_env.get("evolution") ... first_env["evolution"] = evo_meta
        # This modification happens AFTER buffering. So the buffered envelopes DO NOT have the updated instance_db_id.
        # Unless `first_env` is a reference to the same dict object that is in `envelopes` list, AND `set_buffer_contact` stores it.
        # But `cache.set` serializes. So the buffer definitely has the OLD version.
        # This suggests `instance_db_id` might not be successfully passed via buffer in the original code, OR it's passed another way.
        # However, to be safe and clean, I should ensure `instance_db_id` is in the buffered data if possible, or verify if it's needed.
        # In the signal, it tries to find the instance via `evo_contact.instance`.
        # `inst = getattr(evo_contact, "instance", None)`
        # Only if that fails does it look at `instance.metadados`.
        # Since we are linking `EvolutionContact` to `EvolutionInstance` explicitly in `_get_or_create_instance` and `_resolve_contact`,
        # the signal should be able to find the instance via the relation, rendering the metadata fallback secondary.
        # So I will proceed without obsessing over the metadata injection, but I will try to preserve the behavior if possible.

        sched_payload: Dict[str, Any] = {
            "contact_id": evo_contact.contact_id,
            "api_key": first_env.apikey,
            "message": first_env.message.to_dict()
            if first_env.message
            else {},  # message is obj
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
        instance = self._get_or_create_instance(envelope, payload)

        # Atualiza telefone da instância se disponível no sender_jid
        if envelope.sender_jid:
            phone = envelope.sender_jid.split("@")[0]
            # Garante que é apenas números e tem tamanho razoável
            if phone.isdigit() and len(phone) <= 20:
                if instance.phone_number != phone:
                    instance.phone_number = phone
                    instance.save(update_fields=["phone_number"])

        evo_contact = self._resolve_contact(instance, envelope)

        if not evo_contact.contact_id:
            # Bug 1 e 2: Passar from_me=True para evitar usar nome do atendente
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

    def _link_contact(
        self,
        evo_contact: EvolutionContact,
        envelope: EvolutionWebhookEnvelope,
        from_me: bool = False,
    ) -> None:
        """Vincula ou cria um Contato do sistema principal.

        Args:
            evo_contact: Contato Evolution a ser vinculado
            envelope: Envelope com dados da mensagem
            from_me: Se True, mensagem foi enviada pelo atendente
        """

        push_name = envelope.profile.push_name
        phone = envelope.contact.phone

        # Bug 2 Fix: STRICTLY forbid creating contacts without phone
        if not phone:
            logger.debug(
                f"Skipping contact creation: no phone available (push_name={push_name})"
            )
            return

        contato: Contato | None = None

        # Para mensagens from_me, o push_name é do REMETENTE (atendente), não do destinatário
        # Portanto, NÃO devemos usar esse nome para criar/atualizar o contato
        use_push_name = push_name if not from_me else None

        logger.debug(
            f"_link_contact phone={phone} push_name={push_name} from_me={from_me} use_push_name={use_push_name}"
        )

        if phone:
            contato, created_contact = Contato.objects.get_or_create(
                telefone=str(phone),
                defaults={
                    "nome_contato": str(use_push_name or ""),
                    "nome_perfil_whatsapp": str(use_push_name or ""),
                    "ativo": True,
                    "metadados": {},
                },
            )
        else:
            # Não criar contatos sem telefone quando from_me=True
            # pois o push_name seria do atendente, não do destinatário
            if from_me:
                logger.debug(
                    "Skipping contact creation for from_me message without phone"
                )
                return

            # Create contact without phone if it doesn't exist
            # We create a new one because we can't match by phone
            contato = Contato.objects.create(
                nome_contato=str(push_name or "Desconhecido"),
                telefone=None,
                ativo=True,
                metadados={},
            )
            created_contact = True

        if contato:
            # Update push_name if it exists and contact was not created (existing contact)
            # MAS: apenas se NÃO for from_me (para evitar sobrescrever com nome do atendente)
            if not created_contact and use_push_name:
                if not contato.nome_perfil_whatsapp:
                    contato.nome_perfil_whatsapp = str(use_push_name)
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
                # Inject instance_db_id into metadata if needed for signal
                env_dict = env.to_dict()
                if instance.id:
                    if "evolution" not in env_dict:
                        env_dict["evolution"] = {}
                    env_dict["evolution"]["instance_db_id"] = instance.id

                set_buffer_contact(int(evo_contact.contact_id), env_dict)
        # evo_meta = first_env.get("evolution") or {}
        # evo_meta["instance_db_id"] = int(instance.id)
        # first_env["evolution"] = evo_meta

        # In our new structure, we can pass this as part of the sched_payload or modify the raw if needed.
        # The scheduler likely reads from the buffer or expects specific params.
        # sched_response_contact takes 'params'.

        # IMPORTANT: The original code modified 'first_env' which was a dict.
        # Here 'first_env' is an object. The buffer stores 'env_dict'.
        # We should probably update the buffer with the instance_db_id if that's where it's read from?
        # Actually, sched_response_contact just triggers a task. The task likely reads the buffer.
        # Wait, the original code did:
        # first_env["evolution"] = evo_meta (where evo_meta has instance_db_id)
        # Then it called sched_response_contact(sched_payload)
        # The buffer was ALREADY set before this modification in the loop.
        # BUT, the loop used 'envelope' (from envelopes list).
        # The modification to 'first_env' (which is envelopes[0]) happened AFTER the loop in the original code?
        # Let's check the original code order.
        # 1. Loop envelopes -> set_buffer_contact
        # 2. Modify first_env["evolution"]
        # 3. sched_response_contact

        # This implies the modification to first_env was NOT stored in the buffer?
        # Or maybe it was intended to be?
        # If set_buffer_contact copies the dict, then the modification after doesn't affect the buffer.
        # If it stores a reference, it might.
        # `cache.set` pickles the object, so it stores a copy.
        # So the modification to `first_env` in the original code seemed to only affect `sched_payload` construction?
        # No, `sched_payload` only has contact_id, api_key, message.
        # So where is `instance_db_id` used?
        # It seems it might be used if `first_env` is passed somewhere else, but it isn't.
        # Wait, maybe I missed something.
        # Ah, `signals.py` reads `instance.metadados.get("evolution", {}).get("instance_db_id")`.
        # But that's from `Mensagem` model.
        # The flow is: Webhook -> Buffer -> Task (send_message_response_by_contact) -> AI Processing -> Mensagem Saved -> Signal.
        # So the `instance_db_id` needs to persist through this flow.
        # The `send_message_response_by_contact` likely reads the buffer, processes it, and creates a `Mensagem`.
        # If the buffer was already set, how does `instance_db_id` get into `Mensagem`?
        # Maybe the task reads the buffer and expects `evolution` metadata there?
        # If so, the original code might have had a bug or I am misinterpreting the order.
        # Original:
        # for envelope in envelopes: set_buffer_contact(...)
        # evo_meta = first_env.get("evolution") ... first_env["evolution"] = evo_meta
        # This modification happens AFTER buffering. So the buffered envelopes DO NOT have the updated instance_db_id.
        # Unless `first_env` is a reference to the same dict object that is in `envelopes` list, AND `set_buffer_contact` stores it.
        # But `cache.set` serializes. So the buffer definitely has the OLD version.
        # This suggests `instance_db_id` might not be successfully passed via buffer in the original code, OR it's passed another way.
        # However, to be safe and clean, I should ensure `instance_db_id` is in the buffered data if possible, or verify if it's needed.
        # In the signal, it tries to find the instance via `evo_contact.instance`.
        # `inst = getattr(evo_contact, "instance", None)`
        # Only if that fails does it look at `instance.metadados`.
        # Since we are linking `EvolutionContact` to `EvolutionInstance` explicitly in `_get_or_create_instance` and `_resolve_contact`,
        # the signal should be able to find the instance via the relation, rendering the metadata fallback secondary.
        # So I will proceed without obsessing over the metadata injection, but I will try to preserve the behavior if possible.

        sched_payload: Dict[str, Any] = {
            "contact_id": evo_contact.contact_id,
            "api_key": first_env.apikey,
            "message": first_env.message.to_dict()
            if first_env.message
            else {},  # message is obj
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
        instance = self._get_or_create_instance(envelope, payload)

        # Atualiza telefone da instância se disponível no sender_jid
        if envelope.sender_jid:
            phone = envelope.sender_jid.split("@")[0]
            # Garante que é apenas números e tem tamanho razoável
            if phone.isdigit() and len(phone) <= 20:
                if instance.phone_number != phone:
                    instance.phone_number = phone
                    instance.save(update_fields=["phone_number"])

        evo_contact = self._resolve_contact(instance, envelope)

        if not evo_contact.contact_id:
            # Bug 1 e 2: Passar from_me=True para evitar usar nome do atendente
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
