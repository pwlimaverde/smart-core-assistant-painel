"""
Script para construção de databases no Notion para Contatos e Clientes com Relacionamentos.

Este script cria as databases necessárias para sincronização dos modelos Contato e Cliente
do Django com o Notion, utilizando a API 2025-09-03 e configurando
relacionamentos bidirecionais entre as databases.

Uso:
    uv run python manage.py shell < notion_sync/scripts/script_constructor_notion.py
    ou
    uv run python -m notion_sync.scripts.script_constructor_notion.py
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
import django
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig


class NotionDatabaseConstructor:
    """
    Construtor de databases no Notion com relacionamentos configurados corretamente.
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

    async def create_cliente_database(self) -> Any:
        """Cria a database de Clientes no Notion (simples, sem relacionamentos iniciais)."""
        logger.info("Criando database de Clientes no Notion...")

        # Propriedades básicas para Clientes
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
            if created.data_sources:
                logger.info(f"🔑 Data Source ID Clientes: {created.data_sources[0]['id']}")
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Clientes: {e}")
            raise

    async def create_contato_database(self, cliente_db: Any) -> Any:
        """
        Cria a database de Contatos no Notion COM RELACIONAMENTO para Clientes.
        """
        logger.info("Criando database de Contatos no Notion com relacionamento...")

        # Obter o data_source_id da database de clientes
        if not cliente_db.data_sources:
            raise ValueError("Database de clientes não possui data_source")

        cliente_data_source_id = cliente_db.data_sources[0]['id']

        # Propriedades para Contatos COM O RELACIONAMENTO
        properties = {
            "Nome Contato": {"title": {}},
            "Telefone": {"phone_number": {}},
            "Email": {"email": {}},
            "Nome Perfil WhatsApp": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Cadastro": {"date": {}},
            "Última Interação": {"date": {}},
            # Propriedade relation apontando para Clientes
            "Clientes Relacionados": {
                "relation": {
                    "data_source_id": cliente_data_source_id,
                    "single_property": {},
                    "dual_property": {
                        "synced_property_name": "Contatos Relacionados"
                    }
                }
            }
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
            if created.data_sources:
                logger.info(f"🔑 Data Source ID Contatos: {created.data_sources[0]['id']}")
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Contatos: {e}")
            raise

    async def add_relation_to_cliente_database(self, contato_db: Any, cliente_db: Any) -> None:
        """
        Adiciona o campo de relacionamento "Contatos Relacionados" na database de Clientes.
        """
        logger.info("Adicionando campo 'Contatos Relacionados' na database de Clientes...")

        try:
            # Obter data_source_ids
            contato_data_source_id = contato_db.data_sources[0]['id']
            cliente_data_source_id = cliente_db.data_sources[0]['id']

            # Adicionar campo "Contatos Relacionados" no data source de Clientes (API 2025-09-03)
            update_params = {
                "properties": {
                    "Contatos Relacionados": {
                        "type": "relation",
                        "relation": {
                            "data_source_id": contato_data_source_id,
                            # Para manter bidirecionalidade com o campo já criado em Contatos
                            "single_property": {},
                            "dual_property": {
                                "synced_property_name": "Clientes Relacionados"
                            }
                        }
                    }
                }
            }

            # Atualizar via endpoint de data sources
            response = await self.client.request(
                method="patch",
                path=f"data_sources/{cliente_data_source_id}",
                body=update_params
            )

            logger.info("✅ Campo 'Contatos Relacionados' adicionado na database de Clientes")

        except Exception as e:
            logger.error(f"❌ Erro ao adicionar relacionamento na database de Clientes: {e}")
            raise

    async def create_example_pages_and_relation(self, contato_db: Any, cliente_db: Any) -> None:
        """
        Cria páginas de exemplo e estabelece o relacionamento entre elas.
        """
        logger.info("Criando páginas de exemplo para testar relacionamento...")

        try:
            # Obter data_source_ids
            contato_data_source_id = contato_db.data_sources[0]['id']
            cliente_data_source_id = cliente_db.data_sources[0]['id']

            # 1. Criar página de cliente exemplo
            logger.info("Criando página de cliente exemplo...")
            cliente_page_params = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": cliente_data_source_id
                },
                "properties": {
                    "Nome Fantasia": {
                        "title": [
                            {"text": {"content": "Empresa Exemplo LTDA"}}
                        ]
                    },
                    "Tipo": {"select": {"name": "juridica"}},

                    "Telefone": {
                        "phone_number": "+55 11 99999-8888"
                    }
                }
            }

            # Criar página de cliente exemplo via endpoint /pages
            cliente_page_body = {
                "parent": {
                    "type": "database_id",
                    "database_id": cliente_db.id
                },
                "properties": cliente_page_params["properties"]
            }
            cliente_page = await self.client.request(
                method="post",
                path="pages",
                body=cliente_page_body
            )
            cliente_page_id = cliente_page.get("id") or getattr(cliente_page, "id", None)
            logger.info(f"✅ Página de cliente exemplo criada: {cliente_page_id}")

            # 2. Criar página de contato exemplo via endpoint /pages
            logger.info("Criando página de contato exemplo...")
            contato_properties = {
                "Nome Contato": {
                    "title": [
                        {"text": {"content": "João Silva Exemplo"}}
                    ]
                },
                "Email": {"email": "joao@exemplo.com"},
                "Telefone": {"phone_number": "+55 11 99999-7777"},
                "Ativo": {"checkbox": True}
            }
            contato_page_body = {
                "parent": {
                    "type": "database_id",
                    "database_id": contato_db.id
                },
                "properties": contato_properties
            }
            contato_page = await self.client.request(
                method="post",
                path="pages",
                body=contato_page_body
            )
            contato_page_id = contato_page.get("id") or getattr(contato_page, "id", None)
            logger.info(f"✅ Página de contato exemplo criada: {contato_page_id}")

            # Aguardar um pouco antes de criar relacionamento
            await asyncio.sleep(2)

            # 3. Vincular o contato ao cliente (relação principal)
            logger.info("Vinculando contato ao cliente...")
            contato_update_params = {
                "properties": {
                    "Clientes Relacionados": {
                        "relation": [
                            {"id": cliente_page_id}
                        ]
                    }
                }
            }

            await self.client.request(
                method="patch",
                path=f"pages/{contato_page_id}",
                body=contato_update_params
            )

            logger.info("✅ Relacionamento criado: Contato → Cliente")

            # 4. Vincular o cliente ao contato (relação inversa)
            logger.info("Vinculando cliente ao contato...")
            cliente_update_params = {
                "properties": {
                    "Contatos Relacionados": {
                        "relation": [
                            {"id": contato_page_id}
                        ]
                    }
                }
            }

            await self.client.request(
                method="patch",
                path=f"pages/{cliente_page_id}",
                body=cliente_update_params
            )

            logger.info("✅ Relacionamento criado: Cliente → Contato")
            logger.info("🎉 Relacionamento bidirecional testado com sucesso!")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar exemplo: {e}")
            logger.info("💡 Isso não afeta a criação das databases, apenas os testes")

    @sync_to_async
    def save_database_configs(self, contato_db: Any, cliente_db: Any) -> None:
        """
        Salva as configurações das databases no modelo NotionDatabaseConfig.
        """
        logger.info("💾 Salvando configurações no modelo NotionDatabaseConfig...")

        try:
            # Obter data_source_ids
            contato_data_source_id = contato_db.data_sources[0]['id'] if contato_db.data_sources else None
            cliente_data_source_id = cliente_db.data_sources[0]['id'] if cliente_db.data_sources else None

            # Configuração para Clientes
            cliente_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_clientes_cliente",
                defaults={
                    "name": "🏢 Clientes CRM",
                    "description": "Database para sincronização de clientes do sistema",
                    "notion_database_id": cliente_db.id,
                    "data_source_id": cliente_data_source_id,
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
                        "Número": {"rich_text": {}},
                        "Contatos Relacionados": {
                            "relation": {
                                "data_source_id": contato_data_source_id,
                                "single_property": {},
                                "dual_property": {
                                    "synced_property_name": "Clientes Relacionados"
                                }
                            }
                        }
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
                        "numero": "Número",
                        "contatos_relacionados": "Contatos Relacionados"
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 9,
                    "auto_sync": True,
                }
            )
            logger.info(f"✅ Configuração de Clientes salva: {cliente_config[0].id}")

            # Configuração para Contatos
            contato_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_clientes_contato",
                defaults={
                    "name": "👥 Contatos CRM",
                    "description": "Database para sincronização de contatos do sistema",
                    "notion_database_id": contato_db.id,
                    "data_source_id": contato_data_source_id,
                    "django_model": "ui.clientes.Contato",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Nome Contato": {"title": {}},
                        "Telefone": {"phone_number": {}},
                        "Email": {"email": {}},
                        "Nome Perfil WhatsApp": {"rich_text": {}},
                        "Ativo": {"checkbox": {}},
                        "Data Cadastro": {"date": {}},
                        "Última Interação": {"date": {}},
                        "Clientes Relacionados": {
                            "relation": {
                                "data_source_id": cliente_data_source_id,
                                "single_property": {},
                                "dual_property": {
                                    "synced_property_name": "Contatos Relacionados"
                                }
                            }
                        }
                    },
                    "field_mappings": {
                        "nome_contato": "Nome Contato",
                        "telefone": "Telefone",
                        "email": "Email",
                        "nome_perfil_whatsapp": "Nome Perfil WhatsApp",
                        "ativo": "Ativo",
                        "data_cadastro": "Data Cadastro",
                        "ultima_interacao": "Última Interação",
                        "clientes_relacionados": "Clientes Relacionados"
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 10,
                    "auto_sync": True,
                }
            )
            logger.info(f"✅ Configuração de Contatos salva: {contato_config[0].id}")

            # Atualizar last_sync_at para indicar que as databases estão prontas
            from django.utils import timezone
            cliente_config[0].last_sync_at = timezone.now()
            cliente_config[0].save()

            contato_config[0].last_sync_at = timezone.now()
            contato_config[0].save()

            logger.info("🎉 Configurações salvas com sucesso no NotionDatabaseConfig!")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações: {e}")
            raise

    async def construct_all_databases(self) -> None:
        """Constrói todas as databases necessárias com relacionamentos corretos."""
        logger.info("🚀 Iniciando construção de databases no Notion com relacionamentos...")

        try:
            # 1. Criar database de Clientes primeiro (simples, sem relacionamentos)
            cliente_db = await self.create_cliente_database()

            # 2. Criar database de Contatos COM RELACIONAMENTO para Clientes
            contato_db = await self.create_contato_database(cliente_db)

            # 3. Aguardar um momento para as databases serem processadas
            await asyncio.sleep(2)

            # 4. Adicionar campo de relacionamento na database de Clientes
            await self.add_relation_to_cliente_database(contato_db, cliente_db)

            # 5. Aguardar um momento antes de criar exemplos
            await asyncio.sleep(2)

            # 6. Criar páginas de exemplo para testar relacionamento
            await self.create_example_pages_and_relation(contato_db, cliente_db)

            # Exibir informações importantes das databases criadas
            logger.info("🎉 Databases criadas com sucesso no Notion!")
            logger.info(f"📋 Contatos: https://www.notion.so/{contato_db.id.replace('-', '')}")
            logger.info(f"📋 Clientes: https://www.notion.so/{cliente_db.id.replace('-', '')}")
            logger.info(f"🔑 ID Contatos: {contato_db.id}")
            logger.info(f"🔑 ID Clientes: {cliente_db.id}")

            if contato_db.data_sources:
                logger.info(f"🔑 Data Source ID Contatos: {contato_db.data_sources[0]['id']}")
            if cliente_db.data_sources:
                logger.info(f"🔑 Data Source ID Clientes: {cliente_db.data_sources[0]['id']}")

            # Salvar configurações no modelo NotionDatabaseConfig
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
    try:
        asyncio.run(run_construction())
    except KeyboardInterrupt:
        logger.info("⏹️ Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise


if __name__ == "__main__":
    # Execução direta do script.
    run()
