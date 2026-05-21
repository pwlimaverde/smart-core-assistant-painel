# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportReturnType=false
"""Endpoints JSON do Workspace (consumidos pelo store Alpine).

Toda rota:
- Exige usuário autenticado.
- Exige ``module_permissions["atendimento"]["view"]`` (ou owner).
- Valida que o tenant atual tem a feature flag ligada.

Erros são serializados em JSON ``{"error": "...", "code": "..."}``.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from loguru import logger

from smart_core_assistant_painel.app.operacional.models import Atendente

from .feature_flags import is_workspace_enabled_for_tenant
from .selectors import (
    board_snapshot_by_fluxo,
    build_timeline,
    contar_nao_lidos_global,
    get_atendimento_detail,
    get_messages,
    list_conversations,
    list_etiquetas,
    list_etiquetas_do_atendimento,
    list_fluxos_acessiveis,
    list_medias,
    list_notas,
)
from smart_core_assistant_painel.app.gestao_kanban.services.board_service import (
    BoardMoveError,
    assign_atendimento,
    mark_read,
    move_atendimento,
)
from smart_core_assistant_painel.app.gestao_kanban.services.etiquetas_service import (
    toggle_etiqueta,
)
from smart_core_assistant_painel.app.chat_evolution.services.message_dispatch_service import (
    send_text_message,
)
from smart_core_assistant_painel.app.gestao_kanban.services.notas_service import (
    criar_nota,
    deletar_nota,
)
from smart_core_assistant_painel.app.gestao_kanban.services.transfer_fluxo_service import (
    transferir_fluxo,
)


def _err(msg: str, code: str = "error", status: int = 400) -> JsonResponse:
    return JsonResponse({"error": msg, "code": code}, status=status)


def _require_workspace(
    func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Decorator: verifica feature flag + autenticação + permissão."""

    def wrapper(
        view_self: View, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if not request.user.is_authenticated:
            return _err("Autenticação obrigatória.", "unauthenticated", 401)
        if not is_workspace_enabled_for_tenant():
            return _err(
                "Workspace não habilitado para este tenant.",
                "feature_disabled",
                404,
            )
        if not _user_can_view(request):
            return _err("Permissão negada.", "forbidden", 403)
        return func(view_self, request, *args, **kwargs)

    return wrapper


def _user_can_view(request: HttpRequest) -> bool:
    if request.user.is_superuser:
        return True
    tenant = getattr(request, "tenant", None)
    if tenant and getattr(tenant, "owner_id", None) == request.user.id:
        return True
    tenant_user = getattr(request, "tenant_user", None)
    if tenant_user is None:
        try:
            tenant_user = request.user.tenant_profile
        except Exception:
            tenant_user = None
    if tenant_user is None:
        return False
    return tenant_user.has_module_permission("atendimento", "view")


def _is_owner_user(request: HttpRequest) -> bool:
    if request.user.is_superuser:
        return True
    tenant = getattr(request, "tenant", None)
    return bool(
        tenant and getattr(tenant, "owner_id", None) == request.user.id
    )


def _resolve_atendente(request: HttpRequest) -> Optional[Atendente]:
    try:
        return (
            Atendente.objects.select_related("departamento", "fluxo")
            .filter(usuario_id=request.user.id, ativo=True)
            .first()
        )
    except Exception:
        return None


def _resolve_tenant_user(request: HttpRequest) -> Any:
    """Retorna o TenantUser do request, se houver."""
    tu = getattr(request, "tenant_user", None)
    if tu is not None:
        return tu
    try:
        return request.user.tenant_profile
    except Exception:
        return None


def _allowed_flow_ids(request: HttpRequest) -> Optional[set[int]]:
    """Conjunto de IDs de fluxo permitidos ao usuário.

    Retorna ``None`` quando o usuário tem acesso irrestrito (owner ou
    superuser) — neste caso o chamador não deve filtrar.
    """
    if _is_owner_user(request):
        return None
    tenant_user = _resolve_tenant_user(request)
    atendente = _resolve_atendente(request)
    fluxos = list_fluxos_acessiveis(
        atendente=atendente,
        is_owner=False,
        tenant_user=tenant_user,
    )
    return {int(f["id"]) for f in fluxos}


def _can_access_fluxo(request: HttpRequest, fluxo_id: Optional[int]) -> bool:
    """True se o usuário pode operar sobre ``fluxo_id``.

    ``fluxo_id`` ``None`` é considerado válido (rotas que aceitam "todos
    os fluxos do usuário"); o filtro real é aplicado downstream.
    """
    if fluxo_id is None:
        return True
    allowed = _allowed_flow_ids(request)
    if allowed is None:
        return True
    return int(fluxo_id) in allowed


def _can_access_atendimento(request: HttpRequest, atendimento_id: int) -> bool:
    """True se o usuário tem acesso ao fluxo do atendimento informado.

    Owner/superuser ⇒ sempre True. Caso contrário consulta o
    ``fluxo_atendimento_id`` do registro e checa contra os fluxos
    permitidos. Atendimento inexistente ⇒ False (delegamos 404 ao
    chamador apenas se ele consultar a entidade).
    """
    allowed = _allowed_flow_ids(request)
    if allowed is None:
        return True
    from smart_core_assistant_painel.app.atendimentos.models import (
        Atendimento,
    )

    fluxo_id = (
        Atendimento.objects.filter(id=atendimento_id)
        .values_list("fluxo_atendimento_id", flat=True)
        .first()
    )
    if fluxo_id is None:
        return False
    return int(fluxo_id) in allowed


def _load_body(request: HttpRequest) -> dict[str, Any]:
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


class FluxosListView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        return JsonResponse(
            {
                "fluxos": list_fluxos_acessiveis(
                    atendente=atendente,
                    is_owner=_is_owner_user(request),
                    tenant_user=_resolve_tenant_user(request),
                )
            }
        )


class ConversationsListView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        fluxo_id = _get_int(request.GET.get("fluxo"))
        if not _can_access_fluxo(request, fluxo_id):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        q = (request.GET.get("q") or "").strip() or None
        tag = (request.GET.get("tag") or "").strip() or None
        limit = min(_get_int(request.GET.get("limit")) or 100, 200)
        cursor = _get_datetime(request.GET.get("cursor"))
        prioridade = (request.GET.get("prioridade") or "").strip() or None
        atendente_id_filtro = _get_int(request.GET.get("atendente_id"))
        etiqueta_id = _get_int(request.GET.get("etiqueta_id"))
        apenas_nao_lidos = (
            request.GET.get("apenas_nao_lidos") or ""
        ).lower() in ("1", "true", "yes")
        items = list_conversations(
            fluxo_id=fluxo_id,
            atendente=atendente,
            is_owner=_is_owner_user(request),
            q=q,
            tag=tag,
            limit=limit,
            cursor=cursor,
            prioridade=prioridade,
            atendente_id_filtro=atendente_id_filtro,
            etiqueta_id=etiqueta_id,
            apenas_nao_lidos=apenas_nao_lidos,
        )
        return JsonResponse({"conversations": items})


class ConversationMessagesView(View):
    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        limit = min(_get_int(request.GET.get("limit")) or 50, 200)
        before_id = _get_int(request.GET.get("before_id"))
        msgs = get_messages(
            atendimento_id=int(atendimento_id),
            limit=limit,
            before_id=before_id,
        )
        return JsonResponse({"messages": msgs})


class ConversationDetailView(View):
    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        data = get_atendimento_detail(int(atendimento_id))
        if data is None:
            return _err("Atendimento não encontrado.", "not_found", 404)
        return JsonResponse(data)


@method_decorator(csrf_protect, name="dispatch")
class ConversationSendView(View):
    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        body = _load_body(request)
        texto = (body.get("texto") or "").strip()
        if not texto:
            return _err("Texto vazio.", "validation", 400)
        quoted_message_id = _get_int(body.get("quoted_message_id"))
        atendente = _resolve_atendente(request)
        try:
            msg = send_text_message(
                atendimento_id=int(atendimento_id),
                texto=texto,
                atendente=atendente,
                quoted_message_id=quoted_message_id,
            )
        except ValueError as exc:
            return _err(str(exc), "validation", 400)
        except Exception as exc:
            logger.exception("Falha ao enviar mensagem: {}", exc)
            return _err("Falha ao enviar mensagem.", "internal", 500)
        return JsonResponse(
            {
                "id": msg.id,
                "atendimento_id": msg.atendimento_id,
                "resposta_bot": msg.resposta_bot or "",
                "timestamp": (
                    msg.timestamp.isoformat() if msg.timestamp else None
                ),
            },
            status=201,
        )


@method_decorator(csrf_protect, name="dispatch")
class ConversationMarkReadView(View):
    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        if atendente is None:
            return _err(
                "Apenas atendentes cadastrados podem marcar como lido.",
                "no_atendente",
                400,
            )
        obj = mark_read(
            atendimento_id=int(atendimento_id), atendente_id=atendente.id
        )
        return JsonResponse(
            {
                "atendimento_id": obj.atendimento_id,
                "atendente_id": obj.atendente_id,
                "ultima_leitura_at": obj.ultima_leitura_at.isoformat(),
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class ConversationPresenceView(View):
    """E.5.1 — Envia indicador de presença (digitando/gravando) ao contato.

    Best-effort: falhas não retornam erro HTTP — apenas logam warning.
    Apenas Evolution Go suporta presence; v2 é no-op silencioso.
    """

    _VALID_STATES = {"composing", "recording", "paused", "available"}

    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        body = _load_body(request)
        state = (body.get("state") or "composing").strip().lower()
        if state not in self._VALID_STATES:
            state = "composing"
        is_audio = bool(body.get("is_audio", False))

        try:
            _dispatch_presence(int(atendimento_id), state, is_audio)
        except Exception as exc:
            logger.warning("presence dispatch falhou (best-effort): {}", exc)

        return JsonResponse({"ok": True, "state": state})


def _dispatch_presence(
    atendimento_id: int, state: str, is_audio: bool = False
) -> None:
    """Despacha set_presence ao Evolution Go para o atendimento (best-effort)."""
    from smart_core_assistant_painel.app.atendimentos.models import Atendimento
    from smart_core_assistant_painel.app.evolution_sync.models import (
        EvolutionContact,
    )
    from smart_core_assistant_painel.app.evolution_sync.services import (
        EvolutionGoAdapter,
    )
    from smart_core_assistant_painel.app.tenants.models import TenantEvolution

    atend = (
        Atendimento.objects.select_related("contato")
        .filter(id=atendimento_id)
        .first()
    )
    if not atend or not atend.contato:
        return

    evo_contact = (
        EvolutionContact.objects.select_related("instance")
        .filter(contact_id=atend.contato_id, active=True)
        .order_by("-updated_at")
        .first()
    )
    if not evo_contact or not evo_contact.instance:
        return

    inst = evo_contact.instance
    tenant_id = getattr(inst, "tenant_id", None)
    base_url = ""
    if tenant_id:
        from smart_core_assistant_painel.app.tenants.models import (
            TenantEvolution,
        )

        cfg = TenantEvolution.objects.filter(tenant_id=tenant_id).first()
        if cfg and cfg.server_url:
            base_url = str(cfg.server_url).rstrip("/")
    if not base_url:
        return

    jid = evo_contact.jid or ""
    if not jid and atend.contato.telefone:
        jid = f"{atend.contato.telefone}@s.whatsapp.net"
    if not jid:
        return

    adapter = EvolutionGoAdapter()
    adapter.set_presence(
        instance=str(inst.name or ""),
        api_key=str(inst.api_key or ""),
        base_url=base_url,
        number=jid,
        state=state,
        is_audio=is_audio,
    )


class BoardSnapshotView(View):
    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        fluxo_id = _get_int(request.GET.get("fluxo"))
        if fluxo_id is None:
            return _err("Parâmetro `fluxo` obrigatório.", "validation", 400)
        if not _can_access_fluxo(request, fluxo_id):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        q = (request.GET.get("q") or "").strip() or None
        prioridade = (request.GET.get("prioridade") or "").strip() or None
        atendente_id_filtro = _get_int(request.GET.get("atendente_id"))
        etiqueta_id = _get_int(request.GET.get("etiqueta_id"))
        apenas_nao_lidos = (
            request.GET.get("apenas_nao_lidos") or ""
        ).lower() in ("1", "true", "yes")
        data = board_snapshot_by_fluxo(
            fluxo_id=fluxo_id,
            atendente=atendente,
            is_owner=_is_owner_user(request),
            q=q,
            prioridade=prioridade,
            atendente_id_filtro=atendente_id_filtro,
            etiqueta_id=etiqueta_id,
            apenas_nao_lidos=apenas_nao_lidos,
        )
        return JsonResponse(data)


@method_decorator(csrf_protect, name="dispatch")
class BoardMoveView(View):
    @_require_workspace
    def post(self, request: HttpRequest) -> HttpResponse:
        body = _load_body(request)
        atendimento_id = _get_int(body.get("atendimento_id"))
        etapa_destino_id = _get_int(body.get("etapa_destino_id"))
        if atendimento_id is None or etapa_destino_id is None:
            return _err(
                "Campos `atendimento_id` e `etapa_destino_id` obrigatórios.",
                "validation",
                400,
            )
        if not _can_access_atendimento(request, atendimento_id):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        try:
            result = move_atendimento(
                atendimento_id=atendimento_id,
                etapa_destino_id=etapa_destino_id,
                atendente_actor=atendente,
                motivo=(body.get("motivo") or None),
            )
        except BoardMoveError as exc:
            return _err(str(exc), "board_move", 400)
        except Exception as exc:
            logger.exception("Falha ao mover card: {}", exc)
            return _err("Falha ao mover card.", "internal", 500)
        return JsonResponse(
            {
                "atendimento_id": result.atendimento.id,
                "etapa_id": result.atendimento.etapa_atual_id,
                "fluxo_id": result.atendimento.fluxo_atendimento_id,
                "novo_status": result.novo_status,
                "cross_board": result.cross_board,
                "finalizou": result.finalizou,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class BoardAssignView(View):
    @_require_workspace
    def post(self, request: HttpRequest) -> HttpResponse:
        body = _load_body(request)
        atendimento_id = _get_int(body.get("atendimento_id"))
        atendente_id = _get_int(body.get("atendente_id"))
        com_saudacao = bool(body.get("com_saudacao", True))
        if atendimento_id is None or atendente_id is None:
            return _err(
                "Campos `atendimento_id` e `atendente_id` obrigatórios.",
                "validation",
                400,
            )
        if not _can_access_atendimento(request, atendimento_id):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = Atendente.objects.filter(
            id=atendente_id, ativo=True
        ).first()
        if atendente is None:
            return _err("Atendente não encontrado.", "not_found", 404)
        try:
            atend = assign_atendimento(
                atendimento_id=atendimento_id,
                atendente=atendente,
                com_saudacao=com_saudacao,
            )
        except Exception as exc:
            logger.exception("Falha ao atribuir atendimento: {}", exc)
            return _err("Falha ao atribuir atendimento.", "internal", 500)
        return JsonResponse(
            {
                "atendimento_id": atend.id,
                "atendente_id": atend.atendente_humano_id,
                "status": atend.status,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class CustomFieldPatchView(View):
    @_require_workspace
    def patch(
        self, request: HttpRequest, atendimento_id: int, slug: str
    ) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        body = _load_body(request)
        if "valor" not in body:
            return _err("Campo `valor` obrigatório.", "validation", 400)
        valor = body["valor"]
        try:
            from .models import (
                CampoPersonalizado,
                OrigemValor,
                ValorCampoAtendimento,
            )

            campo = CampoPersonalizado.objects.filter(
                slug=slug, ativo=True
            ).first()
            if campo is None:
                return _err("Campo não encontrado.", "not_found", 404)
            atendente = _resolve_atendente(request)
            atendente_id = atendente.id if atendente else None
            obj, _ = ValorCampoAtendimento.objects.update_or_create(
                atendimento_id=atendimento_id,
                campo=campo,
                defaults={
                    "valor": valor,
                    "origem": OrigemValor.MANUAL,
                    "confianca": None,
                    "mensagem_origem_id": None,
                    "editado_por_id": atendente_id,
                },
            )
        except Exception as exc:
            logger.exception("Falha ao salvar campo personalizado: {}", exc)
            return _err("Falha ao salvar campo.", "internal", 500)
        return JsonResponse(
            {
                "slug": slug,
                "atendimento_id": atendimento_id,
                "valor": obj.valor,
                "origem": obj.origem,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class ConversationUploadView(View):
    """E.3.9 — Upload de mídia outbound (multipart/form-data, ≤10 MB)."""

    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        from smart_core_assistant_painel.app.chat_evolution.services.media_dispatch_service import (
            upload_and_send_media,
        )

        uploaded = request.FILES.get("file")
        if uploaded is None:
            return _err("Campo `file` obrigatório.", "validation", 400)
        if uploaded.size > 10 * 1024 * 1024:
            return _err("Arquivo excede limite de 10 MB.", "validation", 400)
        file_bytes = uploaded.read()
        filename = uploaded.name or "arquivo"
        content_type = uploaded.content_type or "application/octet-stream"
        caption = (request.POST.get("caption") or "").strip()
        atendente = _resolve_atendente(request)
        try:
            msg = upload_and_send_media(
                atendimento_id=atendimento_id,
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
                atendente=atendente,
                caption=caption,
            )
        except ValueError as exc:
            return _err(str(exc), "validation", 400)
        except Exception as exc:
            logger.exception("Falha ao fazer upload de mídia: {}", exc)
            return _err("Falha ao enviar mídia.", "internal", 500)
        return JsonResponse(
            {
                "id": msg.id,
                "atendimento_id": msg.atendimento_id,
                "tipo": msg.tipo,
                "respondida": msg.respondida,
                "timestamp": (
                    msg.timestamp.isoformat() if msg.timestamp else None
                ),
            },
            status=201,
        )


class ExportView(View):
    """E.3.10 — Export de conversas ativas em CSV (StreamingHttpResponse)."""

    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        import csv

        from django.http import StreamingHttpResponse

        from smart_core_assistant_painel.app.atendimentos.models import (
            Atendimento,
            StatusAtendimento,
        )

        fluxo_id = _get_int(request.GET.get("fluxo"))
        if not _can_access_fluxo(request, fluxo_id):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        is_owner = _is_owner_user(request)
        allowed_flow_ids = _allowed_flow_ids(request)

        qs = (
            Atendimento.objects.select_related(
                "contato",
                "atendente_humano",
                "etapa_atual",
                "fluxo_atendimento",
            )
            .exclude(
                status__in=[
                    StatusAtendimento.RESOLVIDO,
                    StatusAtendimento.CANCELADO,
                ]
            )
            .order_by("-data_ultima_mensagem")
        )
        if fluxo_id is not None:
            qs = qs.filter(fluxo_atendimento_id=fluxo_id)
        elif allowed_flow_ids is not None:
            qs = qs.filter(fluxo_atendimento_id__in=allowed_flow_ids)
        if not is_owner and atendente is not None:
            from django.db.models import Q

            qs = qs.filter(
                Q(atendente_humano=atendente)
                | Q(
                    atendente_humano__isnull=True,
                    departamento_id=atendente.departamento_id,
                )
            )

        class _Echo:
            def write(self, value: str) -> str:
                return value

        def _rows():
            writer = csv.writer(_Echo())
            yield writer.writerow(
                [
                    "id",
                    "contato_nome",
                    "telefone",
                    "assunto",
                    "status",
                    "prioridade",
                    "etapa",
                    "atendente",
                    "fluxo",
                    "data_inicio",
                    "data_ultima_mensagem",
                ]
            )
            for atend in qs.iterator(chunk_size=500):
                contato = getattr(atend, "contato", None)
                nome = (
                    (
                        getattr(contato, "nome_contato", None)
                        or getattr(contato, "nome_perfil_whatsapp", None)
                        or getattr(contato, "telefone", "")
                    )
                    if contato
                    else ""
                )
                yield writer.writerow(
                    [
                        atend.id,
                        nome,
                        getattr(contato, "telefone", "") if contato else "",
                        atend.assunto or "",
                        atend.status,
                        atend.prioridade,
                        getattr(atend.etapa_atual, "nome", "")
                        if getattr(atend, "etapa_atual", None)
                        else "",
                        getattr(atend.atendente_humano, "nome", "")
                        if getattr(atend, "atendente_humano", None)
                        else "",
                        getattr(atend.fluxo_atendimento, "nome", "")
                        if getattr(atend, "fluxo_atendimento", None)
                        else "",
                        atend.data_inicio.isoformat()
                        if atend.data_inicio
                        else "",
                        atend.data_ultima_mensagem.isoformat()
                        if atend.data_ultima_mensagem
                        else "",
                    ]
                )

        response = StreamingHttpResponse(
            _rows(), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="atendimentos.csv"'
        )
        return response


class NotificationsUnreadCountView(View):
    """Total de mensagens não lidas para o sino da topbar."""

    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        atendente = _resolve_atendente(request)
        total = contar_nao_lidos_global(
            atendente=atendente, is_owner=_is_owner_user(request)
        )
        return JsonResponse({"total": int(total)})


class EtiquetasListView(View):
    """Catálogo de etiquetas disponíveis."""

    @_require_workspace
    def get(self, request: HttpRequest) -> HttpResponse:
        return JsonResponse({"etiquetas": list_etiquetas()})


class ConversationEtiquetasView(View):
    """Etiquetas aplicadas a um atendimento."""

    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        return JsonResponse(
            {"etiquetas": list_etiquetas_do_atendimento(int(atendimento_id))}
        )


@method_decorator(csrf_protect, name="dispatch")
class ConversationEtiquetaToggleView(View):
    """Adiciona ou remove etiqueta de um atendimento."""

    @_require_workspace
    def post(
        self,
        request: HttpRequest,
        atendimento_id: int,
        etiqueta_id: int,
    ) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        atendente_id = atendente.id if atendente else None
        try:
            result = toggle_etiqueta(
                atendimento_id=int(atendimento_id),
                etiqueta_id=int(etiqueta_id),
                atendente_id=atendente_id,
            )
        except Exception as exc:
            return _err(str(exc), "validation", 400)
        return JsonResponse(result)


@method_decorator(csrf_protect, name="dispatch")
class ConversationNotasView(View):
    """Lista e cria notas de um atendimento."""

    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        return JsonResponse({"notas": list_notas(int(atendimento_id))})

    @_require_workspace
    def post(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        body = _load_body(request)
        texto = (body.get("texto") or "").strip()
        if not texto:
            return _err("Texto vazio.", "validation", 400)
        atendente = _resolve_atendente(request)
        atendente_id = atendente.id if atendente else None
        try:
            nota = criar_nota(
                atendimento_id=int(atendimento_id),
                texto=texto,
                atendente_id=atendente_id,
            )
        except Exception as exc:
            return _err(str(exc), "validation", 400)
        if atendente is not None:
            nota["criado_por_nome"] = atendente.nome
        return JsonResponse(nota, status=201)


@method_decorator(csrf_protect, name="dispatch")
class ConversationNotaDeleteView(View):
    """Remove nota (apenas o autor pode)."""

    @_require_workspace
    def delete(
        self,
        request: HttpRequest,
        atendimento_id: int,
        nota_id: int,
    ) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        atendente = _resolve_atendente(request)
        atendente_id = atendente.id if atendente else None
        ok = deletar_nota(nota_id=int(nota_id), atendente_id=atendente_id)
        if not ok:
            return _err(
                "Nota não encontrada ou sem permissão.", "not_found", 404
            )
        return JsonResponse({"deleted": True})


class ConversationMediasView(View):
    """Lista mídias e arquivos do atendimento."""

    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        return JsonResponse({"medias": list_medias(int(atendimento_id))})


class ConversationTimelineView(View):
    """Linha do tempo agregada do atendimento."""

    @_require_workspace
    def get(self, request: HttpRequest, atendimento_id: int) -> HttpResponse:
        if not _can_access_atendimento(request, int(atendimento_id)):
            return _err(
                "Sem permissão para este fluxo.", "forbidden_flow", 403
            )
        return JsonResponse({"timeline": build_timeline(int(atendimento_id))})


@method_decorator(csrf_protect, name="dispatch")
class BoardTransferFluxoView(View):
    """Transfere atendimento entre Fluxos de Atendimento."""

    @_require_workspace
    def post(self, request: HttpRequest) -> HttpResponse:
        body = _load_body(request)
        atendimento_id = _get_int(body.get("atendimento_id"))
        fluxo_destino_id = _get_int(body.get("fluxo_destino_id"))
        if atendimento_id is None or fluxo_destino_id is None:
            return _err(
                "Campos `atendimento_id` e `fluxo_destino_id` obrigatórios.",
                "validation",
                400,
            )
        if not _can_access_atendimento(request, atendimento_id):
            return _err(
                "Sem permissão sobre o fluxo de origem.",
                "forbidden_flow",
                403,
            )
        if not _can_access_fluxo(request, fluxo_destino_id):
            return _err(
                "Sem permissão sobre o fluxo de destino.",
                "forbidden_flow",
                403,
            )
        atendente = _resolve_atendente(request)
        try:
            result = transferir_fluxo(
                atendimento_id=atendimento_id,
                fluxo_destino_id=fluxo_destino_id,
                atendente_actor=atendente,
                motivo=(body.get("motivo") or None),
            )
        except BoardMoveError as exc:
            return _err(str(exc), "board_move", 400)
        except Exception as exc:
            logger.exception("Falha ao transferir fluxo: {}", exc)
            return _err(str(exc), "validation", 400)
        return JsonResponse(
            {
                "atendimento_id": result.atendimento.id,
                "etapa_id": result.atendimento.etapa_atual_id,
                "fluxo_id": result.atendimento.fluxo_atendimento_id,
                "cross_board": result.cross_board,
            }
        )


def _get_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None


def _get_datetime(value: Any):
    if not value:
        return None
    try:
        from django.utils.dateparse import parse_datetime

        return parse_datetime(str(value))
    except Exception:
        return None
