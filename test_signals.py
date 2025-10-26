"""
Script para testar se os signals de sincronização estão funcionando corretamente.

Este script vai:
1. Criar um cliente
2. Criar um contato
3. Vincular o contato ao cliente
4. Verificar se os signals foram disparados
5. Verificar se a sincronização com o Notion foi executada
"""
import os
import sys
import django
from django.db import transaction

# Configurar ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
django.setup()

from loguru import logger
from smart_core_assistant_painel.app.ui.clientes.models import Cliente, Contato
from smart_core_assistant_painel.app.notion_sync.models import ClienteSync, ContatoSync, SyncLog

def main():
    """Função principal de teste."""
    logger.info("🧪 Iniciando teste de signals de sincronização...")

    try:
        with transaction.atomic():
            # 1. Criar um cliente
            logger.info("1️⃣ Criando cliente de teste...")
            cliente = Cliente.objects.create(
                nome_fantasia="Empresa Teste Signals",
                tipo="juridica",
                cnpj="12.345.678/0001-90",
                telefone="+55 11 99999-8888",
                site="https://empresateste.com.br"
            )
            logger.info(f"   ✅ Cliente criado: {cliente.id} - {cliente.nome_fantasia}")

            # 2. Criar um contato
            logger.info("2️⃣ Criando contato de teste...")
            contato = Contato.objects.create(
                nome_contato="João Teste Signals",
                email="joao@empresateste.com.br",
                telefone="+55 11 99999-7777"
            )
            logger.info(f"   ✅ Contato criado: {contato.id} - {contato.nome_contato}")

            # Aguardar um pouco para processamento dos signals
            import time
            time.sleep(2)

            # 3. Vincular contato ao cliente
            logger.info("3️⃣ Vinculando contato ao cliente...")
            cliente.contatos.add(contato)
            logger.info(f"   🔗 Relacionamento criado: Cliente {cliente.id} ↔ Contato {contato.id}")

            # Aguardar processamento dos signals de relacionamento
            time.sleep(3)

            # 4. Verificar se os sync records foram criados
            logger.info("4️⃣ Verificando registros de sincronização...")

            try:
                cliente_sync = ClienteSync.objects.get(cliente_id=cliente.id)
                logger.info(f"   📄 ClienteSync: status={cliente_sync.sync_status}, external_id={cliente_sync.external_id}")
            except ClienteSync.DoesNotExist:
                logger.error("   ❌ ClienteSync não encontrado!")

            try:
                contato_sync = ContatoSync.objects.get(contato_id=contato.id)
                logger.info(f"   📄 ContatoSync: status={contato_sync.sync_status}, external_id={contato_sync.external_id}")
            except ContatoSync.DoesNotExist:
                logger.error("   ❌ ContatoSync não encontrado!")

            # 5. Verificar logs de sincronização
            logger.info("5️⃣ Verificando logs de sincronização...")

            sync_logs = SyncLog.objects.filter(
                model_name__in=["Cliente", "Contato"]
            ).order_by('-created_at')[:10]

            if sync_logs.exists():
                logger.info(f"   📋 Encontrados {sync_logs.count()} logs recentes:")
                for log in sync_logs:
                    logger.info(f"      - {log.model_name} #{log.instance_id}: {log.operation} - {log.status}")
            else:
                logger.warning("   ⚠️ Nenhum log de sincronização encontrado!")

            # 6. Status final
            logger.info("6️⃣ Status final da sincronização:")

            cliente_sync_ready = hasattr(cliente, 'notion_sync') and cliente.notion_sync.external_id is not None
            contato_sync_ready = hasattr(contato, 'notion_sync') and contato.notion_sync.external_id is not None

            logger.info(f"   🏢 Cliente sincronizado: {cliente_sync_ready}")
            logger.info(f"   👥 Contato sincronizado: {contato_sync_ready}")

            if cliente_sync_ready and contato_sync_ready:
                logger.info("   🎉 Sincronização automática funcionando perfeitamente!")
            else:
                logger.error("   ❌ Problema na sincronização automática!")

    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}")
        logger.exception("Stack trace completo:")
        # Rollback em caso de erro
        logger.info("🔄 Fazendo rollback das alterações...")
        raise

    finally:
        logger.info("🏁 Teste de signals concluído")

if __name__ == "__main__":
    main()
