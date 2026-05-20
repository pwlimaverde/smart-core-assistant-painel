"""[EVO-GO-TASKS] Tasks Celery do evolution_sync.

Inclui o keep-alive da sessão WhatsApp do Evolution Go: o servidor baseado em
whatsmeow derruba a sessão (``connected=false``) quando fica ocioso, e sem ela
nenhum webhook de mensagem é entregue. Esta task verifica periodicamente o
estado de conexão de cada instância ativa e chama ``/instance/reconnect`` quando
necessário, mantendo o atendimento sempre operante.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def keepalive_evolution_instances(self) -> str:  # type: ignore[no-untyped-def]
    """Mantém as instâncias do Evolution Go conectadas (reconnect on-demand).

    Para cada ``TenantEvolution`` configurado, lista as instâncias via
    ``/instance/all`` (Global API Key) e, para cada ``EvolutionInstance`` ativa
    cujo ``connected`` esteja ``false``, dispara ``/instance/reconnect`` com o
    token da instância. É best-effort: erros por tenant/instância são logados e
    não interrompem os demais.

    Returns:
        Resumo ``"keepalive: checked=<n> reconnected=<n>"``.
    """
    from smart_core_assistant_painel.app.evolution_sync.models import (
        EvolutionInstance,
    )
    from smart_core_assistant_painel.app.evolution_sync.services import (
        EvolutionGoAdapter,
    )
    from smart_core_assistant_painel.app.tenants.middleware import (
        set_current_tenant,
    )
    from smart_core_assistant_painel.app.tenants.models import TenantEvolution

    adapter = EvolutionGoAdapter()
    checked = 0
    reconnected = 0

    configs = (
        TenantEvolution.objects.select_related("tenant")
        .exclude(server_url="")
        .exclude(api_key="")
    )

    for cfg in configs:
        tenant = cfg.tenant
        base = (cfg.server_url or "").rstrip("/")
        if not base:
            continue
        try:
            set_current_tenant(tenant)

            # Estado por instância via /instance/all (Global API Key).
            try:
                remote = adapter.fetch_instances(base, cfg.api_key)
            except Exception as exc:
                logger.warning(
                    f"keepalive: falha ao listar instâncias de "
                    f"{tenant.slug}: {exc}"
                )
                continue

            by_name = {
                str(d.get("name")): d
                for d in remote
                if isinstance(d, dict) and d.get("name")
            }

            for inst in EvolutionInstance.objects.filter(active=True):
                checked += 1
                data = by_name.get(inst.name) or {}
                connected = bool(data.get("connected"))
                if connected or not inst.api_key:
                    continue
                try:
                    adapter.reconnect_instance(
                        base_url=base,
                        api_key=inst.api_key,
                        name=inst.name,
                    )
                    reconnected += 1
                    logger.info(
                        f"keepalive: reconnect disparado para "
                        f"{tenant.slug}/{inst.name}"
                    )
                except Exception as exc:
                    logger.warning(
                        f"keepalive: reconnect falhou para "
                        f"{tenant.slug}/{inst.name}: {exc}"
                    )
        except Exception as exc:
            logger.warning(f"keepalive: erro no tenant {tenant.slug}: {exc}")
        finally:
            set_current_tenant(None)

    return f"keepalive: checked={checked} reconnected={reconnected}"
