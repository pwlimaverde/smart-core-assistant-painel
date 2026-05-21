# ruff: noqa: E402
import os
import sys

import django

try:
    # Resolve o caminho do diretório 'src' e insere no sys.path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_dir = os.path.join(base_dir, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
except NameError:
    # Se __file__ não estiver disponível (ex: executado via stdin)
    pass

# Inicializa o contexto do Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.core.settings"
)
django.setup()

from loguru import logger

from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionInstance,
)
from smart_core_assistant_painel.app.evolution_sync.services import (
    EvolutionGoAdapter,
)
from smart_core_assistant_painel.app.tenants.models import TenantEvolution


def main():
    logger.info("Iniciando correção em lote das instâncias existentes...")
    instances = EvolutionInstance.objects.filter(active=True)
    adapter = EvolutionGoAdapter()

    count_success = 0
    count_error = 0

    for inst in instances:
        instance_name = inst.name or inst.phone_number or inst.instance_id
        token = inst.api_key
        instance_id = inst.instance_id

        if not instance_name or not token or not instance_id:
            logger.warning(
                f"Instância PK={inst.id} com dados incompletos. Pulando."
            )
            continue

        # Resolve o base_url com base no tenant
        base_url = ""
        tenant_id = getattr(inst, "tenant_id", None)
        if tenant_id:
            tenant_cfg = TenantEvolution.objects.filter(
                tenant_id=tenant_id
            ).first()
            if tenant_cfg and tenant_cfg.server_url:
                base_url = str(tenant_cfg.server_url).rstrip("/")

        if not base_url:
            logger.warning(
                f"Não foi possível resolver server_url para a instância {instance_name} (PK={inst.id}). Pulando."
            )
            continue

        logger.info(
            f"Atualizando instância: {instance_name} (ID: {instance_id}) em {base_url}"
        )

        try:
            adapter.set_advanced_settings(
                base_url=base_url,
                api_key=str(token),
                instance_id=str(instance_id),
                always_online=True,
                read_messages=False,  # Desativando a leitura automática
            )
            logger.info(f"Instância {instance_name} atualizada com sucesso.")
            count_success += 1
        except Exception as e:
            logger.error(f"Erro ao atualizar instância {instance_name}: {e}")
            count_error += 1

    logger.info(
        f"Correção finalizada. Sucesso: {count_success}, Erros: {count_error}"
    )


if __name__ == "__main__":
    main()
