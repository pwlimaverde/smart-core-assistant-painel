"""
Script para construção de databases no Notion para Contatos e Clientes.

Este script cria as databases necessárias para sincronização dos modelos Contato e Cliente
do Django com o Notion, utilizando a API 2025-09-03 e salvando as configurações
no modelo NotionDatabaseConfig.

Uso:
    uv run python manage.py shell < notion_sync/scripts/script_constructor_notion.py
    ou
    uv run python -m notion_sync.scripts.script_constructor_notion
"""
import os
import sys
import asyncio
import logging
from typing import Any, Dict
from asgiref.sync import sync_to_async

from dotenv import load_dotenv
from notion_py_client import NotionAsyncClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o path do projeto ao sys.path para importar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
import django
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig


class NotionDatabaseConstructor:
    """
    Construtor de databases no Notion.
    """

    def __init__(self) -> None:
        """Inicializa o construtor com as configurações necessárias."""
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_page_id = os.getenv("NOTION_PAGE_ID")

        if not self.notion_token or not self.notion_page_id:
            raise ValueError(
                "NOTION_TOKEN e NOTION_PAGE_ID devem ser definidos no .env"
            )

        self.client = NotionAsyncClient(auth=self.notion_token)

    async def create_contato_database(self) -> Any:
        """Cria a database de Contatos no Notion."""
        logger.info("Criando database de Contatos no Notion...")

        # Definição das propriedades para Contato baseadas no modelo Django
        properties = {
            "Nome Contato": {"title": {}},
            "Telefone": {"phone_number": {}},
            "Email": {"email": {}},
            "Nome Perfil WhatsApp": {"rich_text": {}},
            "Ativo": {
                "checkbox": {}
            },
            "Data Cadastro": {"date": {}},
            "Última Interação": {"date": {}}
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [{"type": "text", "text": {"content": "👥 Contatos CRM"}}],
            "icon": {"type": "emoji", "emoji": "👥"},
            "initial_data_source": {
                "name": "Contatos",
                "properties": properties
            }
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Contatos criada: {created.id}")
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Contatos: {e}")
            raise

    async def create_cliente_database(self, contato_db: Any) -> Any:
        """Cria a database de Clientes no Notion com relacionamento para Contatos."""
        logger.info("Criando database de Clientes no Notion...")

        # Primeiro cria a database sem relacionamento
        properties = {
            "Nome Fantasia": {"title": {}},
            "Razão Social": {"rich_text": {}},
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "fisica", "color": "blue"},
                        {"name": "juridica", "color": "green"}
                    ]
                }
            },
            "CNPJ": {"rich_text": {}},
            "CPF": {"rich_text": {}},
            "Telefone": {"phone_number": {}},
            "Site": {"url": {}},
            "Ramo Atividade": {"rich_text": {}},
            "Observações": {"rich_text": {}},
            "CEP": {"rich_text": {}},
            "Logradouro": {"rich_text": {}},
            "Número": {"rich_text": {}}
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [{"type": "text", "text": {"content": "🏢 Clientes CRM"}}],
            "icon": {"type": "emoji", "emoji": "🏢"},
            "initial_data_source": {
                "name": "Clientes",
                "properties": properties
            }
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Clientes criada: {created.id}")
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Clientes: {e}")
            raise

    async def add_relations_between_databases(self, contato_db: Any, cliente_db: Any) -> None:
        """Adiciona relacionamentos bidirecionais entre as databases após criação."""
        logger.info("Verificando se relacionamentos são necessários...")

        # Por enquanto, apenas logamos que os relacionamentos podem ser criados manualmente
        logger.info("✅ Databases criadas com sucesso (relacionamentos opcionais)")

        # Relacionamentos serão criados manualmente ou via UI do Notion
        logger.info("⚠️ Relacionamentos omitidos por simplicidade - podem ser criados manualmente no Notion")

    @sync_to_async
    def save_database_configs(self, contato_db: Any, cliente_db: Any) -> None:
        """
        Salva as configurações das databases no modelo NotionDatabaseConfig.

        Este é o ponto crucial: salva os artefatos criados no NotionDatabaseConfig
        para que o sistema possa recuperar os IDs posteriormente.
        """
        logger.info("💾 Salvando configurações no modelo NotionDatabaseConfig...")

        try:
            # Configuração para Contatos
            contato_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_clientes_contato",
                defaults={
                    "name": "👥 Contatos CRM",
                    "description": "Database para sincronização de contatos do sistema",
                    "notion_database_id": contato_db.id,
                    "data_source_id": contato_db.data_sources[0]['id'] if contato_db.data_sources else None,
                    "django_model": "ui.clientes.Contato",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Nome Contato": {"title": {}},
                        "Telefone": {"phone_number": {}},
                        "Email": {"email": {}},
                        "Nome Perfil WhatsApp": {"rich_text": {}},
                        "Ativo": {"checkbox": {}},
                        "Data Cadastro": {"date": {}},
                        "Última Interação": {"date": {}}
                    },
                    "field_mappings": {
                        "nome_contato": "Nome Contato",
                        "telefone": "Telefone",
                        "email": "Email",
                        "nome_perfil_whatsapp": "Nome Perfil WhatsApp",
                        "ativo": "Ativo",
                        "data_cadastro": "Data Cadastro",
                        "ultima_interacao": "Última Interação"
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 10,
                    "auto_sync": True,
                }
            )
            logger.info(f"✅ Configuração de Contatos salva: {contato_config[0].id}")

            # Configuração para Clientes
            cliente_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_clientes_cliente",
                defaults={
                    "name": "🏢 Clientes CRM",
                    "description": "Database para sincronização de clientes do sistema",
                    "notion_database_id": cliente_db.id,
                    "data_source_id": cliente_db.data_sources[0]['id'] if cliente_db.data_sources else None,
                    "django_model": "ui.clientes.Cliente",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Nome Fantasia": {"title": {}},
                        "Razão Social": {"rich_text": {}},
                        "Tipo": {
                            "select": {
                                "options": [
                                    {"name": "fisica", "color": "blue"},
                                    {"name": "juridica", "color": "green"}
                                ]
                            }
                        },
                        "CNPJ": {"rich_text": {}},
                        "CPF": {"rich_text": {}},
                        "Telefone": {"phone_number": {}},
                        "Site": {"url": {}},
                        "Ramo Atividade": {"rich_text": {}},
                        "Observações": {"rich_text": {}},
                        "CEP": {"rich_text": {}},
                        "Logradouro": {"rich_text": {}},
                        "Número": {"rich_text": {}}
                    },
                    "field_mappings": {
                        "nome_fantasia": "Nome Fantasia",
                        "razao_social": "Razão Social",
                        "tipo": "Tipo",
                        "cnpj": "CNPJ",
                        "cpf": "CPF",
                        "telefone": "Telefone",
                        "site": "Site",
                        "ramo_atividade": "Ramo Atividade",
                        "observacoes": "Observações",
                        "cep": "CEP",
                        "logradouro": "Logradouro",
                        "numero": "Número"
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 9,
                    "auto_sync": True,
                }
            )
            logger.info(f"✅ Configuração de Clientes salva: {cliente_config[0].id}")

            # Atualizar last_sync_at para indicar que as databases estão prontas
            from django.utils import timezone
            contato_config[0].last_sync_at = timezone.now()
            contato_config[0].save()

            cliente_config[0].last_sync_at = timezone.now()
            cliente_config[0].save()

            logger.info("🎉 Configurações salvas com sucesso no NotionDatabaseConfig!")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações: {e}")
            raise

    async def construct_all_databases(self) -> None:
        """Constrói todas as databases necessárias."""
        logger.info("🚀 Iniciando construção de databases no Notion...")

        try:
            # Criar database de Contatos
            contato_db = await self.create_contato_database()

            # Criar database de Clientes (sem relacionamento inicial)
            cliente_db = await self.create_cliente_database(contato_db)

            # Adicionar relacionamentos (se necessário)
            await self.add_relations_between_databases(contato_db, cliente_db)

            # Exibir informações importantes das databases criadas
            logger.info("🎉 Databases criadas com sucesso no Notion!")
            logger.info(f"📋 Contatos: {contato_db.url}")
            logger.info(f"📋 Clientes: {cliente_db.url}")
            logger.info(f"🔑 ID Contatos: {contato_db.id}")
            logger.info(f"🔑 ID Clientes: {cliente_db.id}")

            if contato_db.data_sources:
                logger.info(f"🔑 Data Source ID Contatos: {contato_db.data_sources[0]['id']}")
            if cliente_db.data_sources:
                logger.info(f"🔑 Data Source ID Clientes: {cliente_db.data_sources[0]['id']}")

            # Tentar salvar configurações no modelo NotionDatabaseConfig (separado para evitar erros)
            try:
                await self.save_database_configs(contato_db, cliente_db)
                logger.info("✅ Configurações salvas com sucesso no Django!")

                # Verificar configurações salvas
                contato_config = await sync_to_async(NotionDatabaseConfig.objects.get)(slug="ui_clientes_contato")
                cliente_config = await sync_to_async(NotionDatabaseConfig.objects.get)(slug="ui_clientes_cliente")

                logger.info("✅ Configurações verificadas no Django:")
                logger.info(f"   - Contato Config ID: {contato_config.id}")
                logger.info(f"   - Cliente Config ID: {cliente_config.id}")
                logger.info(f"   - Ambas prontas para sincronização: {contato_config.is_ready_for_sync() and cliente_config.is_ready_for_sync()}")

            except Exception as e:
                logger.warning(f"⚠️ Erro ao salvar configurações no Django: {e}")
                logger.info("💡 As databases foram criadas no Notion, mas você precisará configurar o NotionDatabaseConfig manualmente:")
                logger.info("   1. Acesse o admin do Django")
                logger.info("   2. Crie NotionDatabaseConfig com os seguintes slugs:")
                logger.info(f"      - ui_clientes_contato (ID: {contato_db.id})")
                logger.info(f"      - ui_clientes_cliente (ID: {cliente_db.id})")
                if contato_db.data_sources:
                    logger.info(f"      - Data Source ID Contatos: {contato_db.data_sources[0]['id']}")
                if cliente_db.data_sources:
                    logger.info(f"      - Data Source ID Clientes: {cliente_db.data_sources[0]['id']}")

        except Exception as e:
            logger.error(f"❌ Falha na construção das databases: {e}")
            raise


async def run_construction() -> None:
    """Função principal que executa a construção das databases."""
    try:
        constructor = NotionDatabaseConstructor()
        await constructor.construct_all_databases()
    except Exception as e:
        logger.error(f"❌ Erro durante a execução: {e}")
        raise


def run() -> None:
    """Entry point para execução do script."""
    # Executar a construção assíncrona
    try:
        asyncio.run(run_construction())
    except KeyboardInterrupt:
        logger.info("⏹️ Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise


if __name__ == "__main__":
    """Execução direta do script."""
    run()
