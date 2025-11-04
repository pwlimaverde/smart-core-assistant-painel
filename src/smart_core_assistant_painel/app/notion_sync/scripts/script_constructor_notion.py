"""
Script para construção de databases no Notion com Relacionamentos.

Este script cria as databases necessárias para sincronização de modelos do Django
com o Notion, utilizando a API 2025-09-03 e configurando relacionamentos
bidirecionais entre as databases.

Módulos disponíveis:
1. Clientes/Contatos - Cria databases para Cliente e Contato com relacionamento
2. Operacional - Cria databases para Departamento e Atendente com relacionamento
3. Atendimentos - Cria databases para Atendimento e Mensagem com relacionamento
4. Full - Executa toda a sequência de construção em ordem correta

Uso:
    # Para construir databases de clientes/contatos
    uv run python manage.py shell < notion_sync/scripts/script_constructor_notion.py
    uv run python -m notion_sync.scripts.script_constructor_notion.py

    # Para construir databases operacionais (departamento/atendente)
    from notion_sync.scripts.script_constructor_notion import run
    run("operacional")

    # Para construir databases de atendimentos (após executar operacional)
    from notion_sync.scripts.script_constructor_notion import run_atendimentos
    run_atendimentos()

    # Para executar toda a sequência de construção (recomendado)
    from notion_sync.scripts.script_constructor_notion import run_full
    run_full()

    # Ou usando a função run com tipo "full"
    from notion_sync.scripts.script_constructor_notion import run
    run("full")

    # Para testar apenas a construção de atendimentos (após operacional)
    from notion_sync.scripts.script_constructor_notion import test_atendimentos_construction
    test_atendimentos_construction()
"""

import os
import sys
import asyncio
import logging
from typing import Any, Dict, Optional
from asgiref.sync import sync_to_async

from dotenv import load_dotenv
from notion_py_client import NotionAsyncClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Ajuste de política de loop para Windows (evita 'Event loop is closed')
try:
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )
except Exception:
    # Falha segura caso a política não esteja disponível
    pass

# Adicionar o path do projeto ao sys.path para importar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configurar Django
# Bypass de serviços ao rodar este script: evita Firebase/WhatsApp.
os.environ.setdefault("DISABLE_APP_SERVICES_INIT", "1")
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
import django

django.setup()

from smart_core_assistant_painel.app.notion_sync.models import (
    NotionDatabaseConfig,
)


class NotionClientesDatabaseConstructor:
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
                        {"name": "juridica", "color": "green"},
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
            "Bairro": {"rich_text": {}},
            "Cidade": {"rich_text": {}},
            "UF": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [
                {"type": "text", "text": {"content": "🏢 Clientes CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "🏢"},
            "initial_data_source": {
                "name": "Clientes",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Clientes criada: {created.id}")
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Clientes: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Clientes: {e}")
            raise

    async def create_contato_database(self, cliente_db: Any) -> Any:
        """
        Cria a database de Contatos no Notion COM RELACIONAMENTO para Clientes.
        """
        logger.info(
            "Criando database de Contatos no Notion com relacionamento..."
        )

        # Obter o data_source_id da database de clientes
        if not cliente_db.data_sources:
            raise ValueError("Database de clientes não possui data_source")

        cliente_data_source_id = cliente_db.data_sources[0]["id"]

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
                    },
                }
            },
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [
                {"type": "text", "text": {"content": "👥 Contatos CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "👥"},
            "initial_data_source": {
                "name": "Contatos",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Contatos criada: {created.id}")
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Contatos: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Contatos: {e}")
            raise

    async def add_relation_to_cliente_database(
        self, contato_db: Any, cliente_db: Any
    ) -> None:
        """
        Adiciona o campo de relacionamento "Contatos Relacionados" na database de Clientes.
        """
        logger.info(
            "Adicionando campo 'Contatos Relacionados' na database de Clientes..."
        )

        try:
            # Obter data_source_ids
            contato_ds_id = contato_db.data_sources[0]["id"]
            cliente_ds_id = cliente_db.data_sources[0]["id"]

            # Buscar IDs das propriedades para vincular corretamente
            contato_db_info = await self.client.request(
                method="get", path=f"databases/{contato_db.id}"
            )
            cliente_db_info = await self.client.request(
                method="get", path=f"databases/{cliente_db.id}"
            )

            def _prop_id(db_info: Dict[str, Any], name: str) -> Optional[str]:
                """Obtém o ID da propriedade por nome, priorizando data_sources.

                Comentários em Português conforme padrão do projeto.
                """
                # Primeiro tenta dentro de cada data_source
                for ds in db_info.get("data_sources") or []:
                    props_ds: Dict[str, Any] = ds.get("properties", {})
                    prop_ds = props_ds.get(name)
                    if prop_ds:
                        return prop_ds.get("id") or getattr(
                            prop_ds, "id", None
                        )
                # Fallback para propriedades raiz
                props_root: Dict[str, Any] = db_info.get("properties", {})
                prop_root = props_root.get(name)
                if not prop_root:
                    return None
                return prop_root.get("id") or getattr(prop_root, "id", None)

            clientes_rel_prop_id = _prop_id(
                contato_db_info, "Clientes Relacionados"
            )

            # Montar atualização garantindo sincronização por ID
            update_params = {
                "properties": {
                    "Contatos Relacionados": {
                        "type": "relation",
                        "relation": {
                            "data_source_id": contato_ds_id,
                            "single_property": {},
                            "dual_property": (
                                {"synced_property_id": clientes_rel_prop_id}
                                if clientes_rel_prop_id
                                else {
                                    "synced_property_name": "Clientes Relacionados"
                                }
                            ),
                        },
                    }
                }
            }

            # Atualizar via endpoint de data sources
            await self.client.request(
                method="patch",
                path=f"data_sources/{cliente_ds_id}",
                body=update_params,
            )

            logger.info(
                "✅ Campo 'Contatos Relacionados' verificado/atualizado em Clientes"
            )

        except Exception as e:
            logger.error(
                f"❌ Erro ao configurar relacionamento na database de Clientes: {e}"
            )
            raise

    async def create_example_pages_and_relation(
        self, contato_db: Any, cliente_db: Any
    ) -> None:
        """
        Cria páginas de exemplo e estabelece o relacionamento entre elas.
        """
        logger.info("Criando páginas de exemplo para testar relacionamento...")

        try:
            # Obter data_source_ids
            contato_data_source_id = contato_db.data_sources[0]["id"]
            cliente_data_source_id = cliente_db.data_sources[0]["id"]

            # 1. Criar página de cliente exemplo
            logger.info("Criando página de cliente exemplo...")
            cliente_page_params = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": cliente_data_source_id,
                },
                "properties": {
                    "Nome Fantasia": {
                        "title": [
                            {"text": {"content": "Empresa Exemplo LTDA"}}
                        ]
                    },
                    "Tipo": {"select": {"name": "juridica"}},
                    "Telefone": {"phone_number": "+55 11 99999-8888"},
                },
            }

            # Criar página de cliente exemplo via endpoint /pages
            cliente_page_body = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": cliente_data_source_id,
                },
                "properties": cliente_page_params["properties"],
            }
            cliente_page = await self.client.request(
                method="post", path="pages", body=cliente_page_body
            )
            cliente_page_id = cliente_page.get("id") or getattr(
                cliente_page, "id", None
            )
            logger.info(
                f"✅ Página de cliente exemplo criada: {cliente_page_id}"
            )

            # 2. Criar página de contato exemplo via endpoint /pages
            logger.info("Criando página de contato exemplo...")
            contato_properties = {
                "Nome Contato": {
                    "title": [{"text": {"content": "João Silva Exemplo"}}]
                },
                "Email": {"email": "joao@exemplo.com"},
                "Telefone": {"phone_number": "+55 11 99999-7777"},
                "Ativo": {"checkbox": True},
            }
            contato_page_body = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": contato_data_source_id,
                },
                "properties": contato_properties,
            }
            contato_page = await self.client.request(
                method="post", path="pages", body=contato_page_body
            )
            contato_page_id = contato_page.get("id") or getattr(
                contato_page, "id", None
            )
            logger.info(
                f"✅ Página de contato exemplo criada: {contato_page_id}"
            )

            # Aguardar um pouco antes de criar relacionamento
            await asyncio.sleep(2)

            # 3. Vincular o contato ao cliente (relação principal)
            logger.info("Vinculando contato ao cliente...")
            contato_update_params = {
                "properties": {
                    "Clientes Relacionados": {
                        "relation": [{"id": cliente_page_id}]
                    }
                }
            }

            await self.client.request(
                method="patch",
                path=f"pages/{contato_page_id}",
                body=contato_update_params,
            )

            logger.info("✅ Relacionamento criado: Contato → Cliente")
            # 4. Vincular o cliente ao contato (espelhado explicitamente)
            # Para garantir que a visualização em Clientes reflita de imediato.
            logger.info("Vinculando cliente ao contato (espelhado)...")
            cliente_update_params = {
                "properties": {
                    "Contatos Relacionados": {
                        "relation": [{"id": contato_page_id}]
                    }
                }
            }

            await self.client.request(
                method="patch",
                path=f"pages/{cliente_page_id}",
                body=cliente_update_params,
            )

            logger.info("✅ Relacionamento criado: Cliente → Contato")
            logger.info("🎉 Relacionamento bidirecional testado com sucesso!")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar exemplo: {e}")
            logger.info(
                "💡 Isso não afeta a criação das databases, apenas os testes"
            )

    @sync_to_async
    def save_database_configs(self, contato_db: Any, cliente_db: Any) -> None:
        """
        Salva as configurações das databases no modelo NotionDatabaseConfig.
        """
        logger.info(
            "💾 Salvando configurações no modelo NotionDatabaseConfig..."
        )

        try:
            # Obter data_source_ids
            contato_data_source_id = (
                contato_db.data_sources[0]["id"]
                if contato_db.data_sources
                else None
            )
            cliente_data_source_id = (
                cliente_db.data_sources[0]["id"]
                if cliente_db.data_sources
                else None
            )

            # Configuração para Clientes
            cliente_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_clientes_cliente",
                defaults={
                    "name": "🏢 Clientes CRM",
                    "description": "Database para sincronização de clientes do sistema",
                    "notion_database_id": cliente_db.id,
                    "data_source_id": cliente_data_source_id,
                    "django_model": "clientes.Cliente",
                    "django_app_label": "clientes",
                    "notion_schema": {
                        "Nome Fantasia": {"title": {}},
                        "Razão Social": {"rich_text": {}},
                        "Tipo": {
                            "select": {
                                "options": [
                                    {"name": "fisica", "color": "blue"},
                                    {"name": "juridica", "color": "green"},
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
                                },
                            }
                        },
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
                        "contatos_relacionados": "Contatos Relacionados",
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 9,
                    "auto_sync": True,
                },
            )
            logger.info(
                f"✅ Configuração de Clientes salva: {cliente_config[0].id}"
            )

            # Configuração para Contatos
            contato_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_clientes_contato",
                defaults={
                    "name": "👥 Contatos CRM",
                    "description": "Database para sincronização de contatos do sistema",
                    "notion_database_id": contato_db.id,
                    "data_source_id": contato_data_source_id,
                    "django_model": "clientes.Contato",
                    "django_app_label": "clientes",
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
                                },
                            }
                        },
                    },
                    "field_mappings": {
                        "nome_contato": "Nome Contato",
                        "telefone": "Telefone",
                        "email": "Email",
                        "nome_perfil_whatsapp": "Nome Perfil WhatsApp",
                        "ativo": "Ativo",
                        "data_cadastro": "Data Cadastro",
                        "ultima_interacao": "Última Interação",
                        "clientes_relacionados": "Clientes Relacionados",
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 10,
                    "auto_sync": True,
                },
            )
            logger.info(
                f"✅ Configuração de Contatos salva: {contato_config[0].id}"
            )

            # Atualizar last_sync_at para indicar que as databases estão prontas
            from django.utils import timezone

            cliente_config[0].last_sync_at = timezone.now()
            cliente_config[0].save()

            contato_config[0].last_sync_at = timezone.now()
            contato_config[0].save()

            logger.info(
                "🎉 Configurações salvas com sucesso no NotionDatabaseConfig!"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações: {e}")
            raise

    async def construct_clientes_databases(self) -> None:
        """Constrói todas as databases necessárias com relacionamentos corretos."""
        logger.info(
            "🚀 Iniciando construção de databases no Notion com relacionamentos..."
        )

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
            await self.create_example_pages_and_relation(
                contato_db, cliente_db
            )

            # Exibir informações importantes das databases criadas
            logger.info("🎉 Databases criadas com sucesso no Notion!")
            logger.info(
                f"📋 Contatos: https://www.notion.so/{contato_db.id.replace('-', '')}"
            )
            logger.info(
                f"📋 Clientes: https://www.notion.so/{cliente_db.id.replace('-', '')}"
            )
            logger.info(f"🔑 ID Contatos: {contato_db.id}")
            logger.info(f"🔑 ID Clientes: {cliente_db.id}")

            if contato_db.data_sources:
                logger.info(
                    f"🔑 Data Source ID Contatos: {contato_db.data_sources[0]['id']}"
                )
            if cliente_db.data_sources:
                logger.info(
                    f"🔑 Data Source ID Clientes: {cliente_db.data_sources[0]['id']}"
                )

            # Salvar configurações no modelo NotionDatabaseConfig
            await self.save_database_configs(contato_db, cliente_db)
            logger.info("✅ Configurações salvas com sucesso no Django!")

            # Verificar configurações salvas
            contato_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_clientes_contato")
            cliente_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_clientes_cliente")

            logger.info("✅ Configurações verificadas no Django:")
            logger.info(f"   - Contato Config ID: {contato_config.id}")
            logger.info(f"   - Cliente Config ID: {cliente_config.id}")
            logger.info(
                f"   - Ambas prontas para sincronização: {contato_config.is_ready_for_sync() and cliente_config.is_ready_for_sync()}"
            )

        except Exception as e:
            logger.error(f"❌ Falha na construção das databases: {e}")
            raise


class NotionOperacionalDatabaseConstructor:
    """
    Construtor de databases no Notion para Departamento e Atendente Humano
    com relacionamentos configurados corretamente.
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

    async def create_departamento_database(self) -> Any:
        """Cria a database de Departamentos no Notion (simples, sem relacionamentos iniciais)."""
        logger.info("Criando database de Departamentos no Notion...")

        # Propriedades básicas para Departamentos
        properties = {
            "Nome": {"title": {}},
            "Descrição": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Criação": {"date": {}},
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [
                {"type": "text", "text": {"content": "🏛️ Departamentos CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "🏛️"},
            "initial_data_source": {
                "name": "Departamentos",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Departamentos criada: {created.id}")
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Departamentos: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Departamentos: {e}")
            raise

    async def create_atendente_database(self, departamento_db: Any) -> Any:
        """
        Cria a database de Atendentes no Notion COM RELACIONAMENTO para Departamentos.
        """
        logger.info(
            "Criando database de Atendentes no Notion com relacionamento..."
        )

        # Obter o data_source_id da database de departamentos
        if not departamento_db.data_sources:
            raise ValueError(
                "Database de departamentos não possui data_source"
            )

        departamento_data_source_id = departamento_db.data_sources[0]["id"]

        # Propriedades para Atendentes Humanos COM O RELACIONAMENTO
        properties = {
            "Nome": {"title": {}},
            "Email": {"email": {}},
            "Telefone": {"phone_number": {}},
            "Cargo": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Disponível": {"checkbox": {}},
            "Capacidade Máxima": {"number": {"format": "number"}},
            "Horário Trabalho": {"rich_text": {}},
            "Departamentos Relacionados": {
                "relation": {
                    "data_source_id": departamento_data_source_id,
                    "single_property": {},
                    "dual_property": {
                        "synced_property_name": "Atendentes Relacionados"
                    },
                }
            },
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [
                {
                    "type": "text",
                    "text": {"content": "👨‍💼 Atendentes CRM"},
                }
            ],
            "icon": {"type": "emoji", "emoji": "👨‍💼"},
            "initial_data_source": {
                "name": "Atendentes",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Atendentes criada: {created.id}")
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Atendentes: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Atendentes: {e}")
            raise

    async def add_relation_to_departamento_database(
        self, atendente_db: Any, departamento_db: Any
    ) -> None:
        """
        Adiciona o campo de relacionamento "Atendentes Relacionados" na database de Departamentos.
        """
        logger.info(
            "Adicionando campo 'Atendentes Relacionados' na database de Departamentos..."
        )

        try:
            # Obter data_source_ids
            atendente_ds_id = atendente_db.data_sources[0]["id"]
            departamento_ds_id = departamento_db.data_sources[0]["id"]

            # Buscar IDs das propriedades para vincular corretamente
            atendente_db_info = await self.client.request(
                method="get", path=f"databases/{atendente_db.id}"
            )
            departamento_db_info = await self.client.request(
                method="get", path=f"databases/{departamento_db.id}"
            )

            def _prop_id(db_info: Dict[str, Any], name: str) -> Optional[str]:
                """Obtém o ID da propriedade por nome, priorizando data_sources."""
                for ds in db_info.get("data_sources") or []:
                    props_ds: Dict[str, Any] = ds.get("properties", {})
                    prop_ds = props_ds.get(name)
                    if prop_ds:
                        return prop_ds.get("id") or getattr(
                            prop_ds, "id", None
                        )
                props_root: Dict[str, Any] = db_info.get("properties", {})
                prop_root = props_root.get(name)
                if not prop_root:
                    return None
                return prop_root.get("id") or getattr(prop_root, "id", None)

            dep_rel_prop_id = _prop_id(
                atendente_db_info, "Departamentos Relacionados"
            )

            # Montar atualização garantindo sincronização por ID
            update_params = {
                "properties": {
                    "Atendentes Relacionados": {
                        "type": "relation",
                        "relation": {
                            "data_source_id": atendente_ds_id,
                            "single_property": {},
                            "dual_property": (
                                {"synced_property_id": dep_rel_prop_id}
                                if dep_rel_prop_id
                                else {
                                    "synced_property_name": "Departamentos Relacionados"
                                }
                            ),
                        },
                    }
                }
            }

            # Atualizar via endpoint de data sources
            await self.client.request(
                method="patch",
                path=f"data_sources/{departamento_ds_id}",
                body=update_params,
            )

            logger.info(
                "✅ Campo 'Atendentes Relacionados' verificado/atualizado em Departamentos"
            )

        except Exception as e:
            logger.error(
                f"❌ Erro ao configurar relacionamento na database de Departamentos: {e}"
            )
            raise

    async def create_example_pages_and_relation(
        self, atendente_db: Any, departamento_db: Any
    ) -> None:
        """
        Cria páginas de exemplo e estabelece o relacionamento entre elas.
        """
        logger.info(
            "Criando páginas de exemplo para testar relacionamento operacional..."
        )

        try:
            # Obter data_source_ids
            atendente_data_source_id = atendente_db.data_sources[0]["id"]
            departamento_data_source_id = departamento_db.data_sources[0]["id"]

            # 1. Criar página de departamento exemplo
            logger.info("Criando página de departamento exemplo...")
            departamento_page_params = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": departamento_data_source_id,
                },
                "properties": {
                    "Nome": {
                        "title": [{"text": {"content": "Suporte Técnico"}}]
                    },
                    "Setor": {"select": {"name": "suporte"}},
                    "Responsável": {
                        "rich_text": [{"text": {"content": "João Gestor"}}]
                    },
                    "Ativo": {"checkbox": True},
                },
            }

            # Criar página de departamento exemplo via endpoint /pages
            departamento_page_body = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": departamento_data_source_id,
                },
                "properties": departamento_page_params["properties"],
            }
            departamento_page = await self.client.request(
                method="post", path="pages", body=departamento_page_body
            )
            departamento_page_id = departamento_page.get("id") or getattr(
                departamento_page, "id", None
            )
            logger.info(
                f"✅ Página de departamento exemplo criada: {departamento_page_id}"
            )

            # 2. Criar página de atendente humano exemplo via endpoint /pages
            logger.info("Criando página de atendente humano exemplo...")
            atendente_properties = {
                "Nome": {
                    "title": [{"text": {"content": "Maria Atendente Exemplo"}}]
                },
                "Email": {"email": "maria.atendente@empresa.com"},
                "Telefone": {"phone_number": "+55 11 99999-5555"},
                "Cargo": {
                    "rich_text": [
                        {"text": {"content": "Analista de Suporte Nível 2"}}
                    ]
                },
                "Setor": {"select": {"name": "suporte"}},
                "Ativo": {"checkbox": True},
            }
            atendente_page_body = {
                "parent": {
                    "type": "data_source_id",
                    "data_source_id": atendente_data_source_id,
                },
                "properties": atendente_properties,
            }
            atendente_page = await self.client.request(
                method="post", path="pages", body=atendente_page_body
            )
            atendente_page_id = atendente_page.get("id") or getattr(
                atendente_page, "id", None
            )
            logger.info(
                f"✅ Página de atendente humano exemplo criada: {atendente_page_id}"
            )

            # Aguardar um pouco antes de criar relacionamento
            await asyncio.sleep(2)

            # 3. Vincular o atendente ao departamento (relação principal)
            logger.info("Vinculando atendente ao departamento...")
            atendente_update_params = {
                "properties": {
                    "Departamentos Relacionados": {
                        "relation": [{"id": departamento_page_id}]
                    }
                }
            }

            await self.client.request(
                method="patch",
                path=f"pages/{atendente_page_id}",
                body=atendente_update_params,
            )

            logger.info("✅ Relacionamento criado: Atendente → Departamento")
            # 4. Vincular o departamento ao atendente (espelhado explicitamente)
            # Para garantir que a visualização em Departamentos reflita de imediato.
            logger.info("Vinculando departamento ao atendente (espelhado)...")
            departamento_update_params = {
                "properties": {
                    "Atendentes Relacionados": {
                        "relation": [{"id": atendente_page_id}]
                    }
                }
            }

            await self.client.request(
                method="patch",
                path=f"pages/{departamento_page_id}",
                body=departamento_update_params,
            )

            logger.info("✅ Relacionamento criado: Departamento → Atendente")
            logger.info(
                "🎉 Relacionamento bidirecional operacional testado com sucesso!"
            )

        except Exception as e:
            logger.warning(f"⚠️ Erro ao criar exemplo operacional: {e}")
            logger.info(
                "💡 Isso não afeta a criação das databases, apenas os testes"
            )

    @sync_to_async
    def save_database_configs(
        self, atendente_db: Any, departamento_db: Any
    ) -> None:
        """
        Salva as configurações das databases no modelo NotionDatabaseConfig.
        """
        logger.info(
            "💾 Salvando configurações operacionais no modelo NotionDatabaseConfig..."
        )

        try:
            # Obter data_source_ids
            atendente_data_source_id = (
                atendente_db.data_sources[0]["id"]
                if atendente_db.data_sources
                else None
            )
            departamento_data_source_id = (
                departamento_db.data_sources[0]["id"]
                if departamento_db.data_sources
                else None
            )

            # Configuração para Departamentos
            departamento_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_operacional_departamento",
                defaults={
                    "name": "🏛️ Departamentos CRM",
                    "description": "Database para sincronização de departamentos do sistema",
                    "notion_database_id": departamento_db.id,
                    "data_source_id": departamento_data_source_id,
                    "django_model": "ui.operacional.Departamento",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Nome": {"title": {}},
                        "Descrição": {"rich_text": {}},
                        "Setor": {
                            "select": {
                                "options": [
                                    {"name": "suporte", "color": "blue"},
                                    {"name": "vendas", "color": "green"},
                                    {"name": "financeiro", "color": "yellow"},
                                    {"name": "marketing", "color": "purple"},
                                    {"name": "ti", "color": "red"},
                                ]
                            }
                        },
                        "Responsável": {"rich_text": {}},
                        "Telefone Interno": {"phone_number": {}},
                        "Email Interno": {"email": {}},
                        "Ativo": {"checkbox": {}},
                        "Data Criação": {"date": {}},
                        "Observações": {"rich_text": {}},
                        "Atendentes Relacionados": {
                            "relation": {
                                "data_source_id": atendente_data_source_id,
                                "single_property": {},
                                "dual_property": {
                                    "synced_property_name": "Departamentos Relacionados"
                                },
                            }
                        },
                    },
                    "field_mappings": {
                        "nome": "Nome",
                        "descricao": "Descrição",
                        "setor": "Setor",
                        "responsavel": "Responsável",
                        "telefone_interno": "Telefone Interno",
                        "email_interno": "Email Interno",
                        "ativo": "Ativo",
                        "data_criacao": "Data Criação",
                        "observacoes": "Observações",
                        "atendentes_relacionados": "Atendentes Relacionados",
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 7,
                    "auto_sync": True,
                },
            )
            logger.info(
                f"✅ Configuração de Departamentos salva: {departamento_config[0].id}"
            )

            # Configuração para Atendentes Humanos
            atendente_config = NotionDatabaseConfig.objects.update_or_create(
                slug="ui_operacional_atendente",
                defaults={
                    "name": "👨‍💼 Atendentes CRM",
                    "description": "Database para sincronização de atendentes do sistema",
                    "notion_database_id": atendente_db.id,
                    "data_source_id": atendente_data_source_id,
                    "django_model": "ui.operacional.Atendente",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Nome": {"title": {}},
                        "Email": {"email": {}},
                        "Telefone": {"phone_number": {}},
                        "Cargo": {"rich_text": {}},
                        "Matrícula": {"rich_text": {}},
                        "Ativo": {"checkbox": {}},
                        "Data Admissão": {"date": {}},
                        "Setor": {
                            "select": {
                                "options": [
                                    {"name": "suporte", "color": "blue"},
                                    {"name": "vendas", "color": "green"},
                                    {"name": "financeiro", "color": "yellow"},
                                    {"name": "marketing", "color": "purple"},
                                    {"name": "ti", "color": "red"},
                                ]
                            }
                        },
                        "Especialidade": {"rich_text": {}},
                        "Horário Trabalho": {"rich_text": {}},
                        "Departamentos Relacionados": {
                            "relation": {
                                "data_source_id": departamento_data_source_id,
                                "single_property": {},
                                "dual_property": {
                                    "synced_property_name": "Atendentes Relacionados"
                                },
                            }
                        },
                    },
                    "field_mappings": {
                        "nome": "Nome",
                        "email": "Email",
                        "telefone": "Telefone",
                        "cargo": "Cargo",
                        "matricula": "Matrícula",
                        "ativo": "Ativo",
                        "data_admissao": "Data Admissão",
                        "setor": "Setor",
                        "especialidade": "Especialidade",
                        "horario_trabalho": "Horário Trabalho",
                        "departamentos_relacionados": "Departamentos Relacionados",
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 8,
                    "auto_sync": True,
                },
            )
            logger.info(
                f"✅ Configuração de Atendentes Humanos salva: {atendente_config[0].id}"
            )

            # Atualizar last_sync_at para indicar que as databases estão prontas
            from django.utils import timezone

            departamento_config[0].last_sync_at = timezone.now()
            departamento_config[0].save()

            atendente_config[0].last_sync_at = timezone.now()
            atendente_config[0].save()

            logger.info(
                "🎉 Configurações operacionais salvas com sucesso no NotionDatabaseConfig!"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações operacionais: {e}")
            raise

    async def construct_operacional_databases(self) -> None:
        """Constrói todas as databases operacionais necessárias com relacionamentos corretos."""
        logger.info(
            "🚀 Iniciando construção de databases operacionais no Notion com relacionamentos..."
        )

        try:
            # 1. Criar database de Departamentos primeiro (simples, sem relacionamentos)
            departamento_db = await self.create_departamento_database()

            # 2. Criar database de Atendentes COM RELACIONAMENTO para Departamentos
            atendente_db = await self.create_atendente_database(
                departamento_db
            )

            # 3. Aguardar um momento para as databases serem processadas
            await asyncio.sleep(2)

            # 4. Adicionar campo de relacionamento na database de Departamentos
            await self.add_relation_to_departamento_database(
                atendente_db, departamento_db
            )

            # 5. Aguardar um momento antes de criar exemplos
            await asyncio.sleep(2)

            # 6. Criar páginas de exemplo para testar relacionamento
            await self.create_example_pages_and_relation(
                atendente_db, departamento_db
            )

            # Exibir informações importantes das databases criadas
            logger.info(
                "🎉 Databases operacionais criadas com sucesso no Notion!"
            )
            logger.info(
                f"📋 Atendentes Humanos: https://www.notion.so/{atendente_db.id.replace('-', '')}"
            )
            logger.info(
                f"📋 Departamentos: https://www.notion.so/{departamento_db.id.replace('-', '')}"
            )
            logger.info(f"🔑 ID Atendentes Humanos: {atendente_db.id}")
            logger.info(f"🔑 ID Departamentos: {departamento_db.id}")

            if atendente_db.data_sources:
                logger.info(
                    f"🔑 Data Source ID Atendentes Humanos: {atendente_db.data_sources[0]['id']}"
                )
            if departamento_db.data_sources:
                logger.info(
                    f"🔑 Data Source ID Departamentos: {departamento_db.data_sources[0]['id']}"
                )

            # Salvar configurações no modelo NotionDatabaseConfig
            await self.save_database_configs(atendente_db, departamento_db)
            logger.info(
                "✅ Configurações operacionais salvas com sucesso no Django!"
            )

            # Verificar configurações salvas
            atendente_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_operacional_atendente")
            departamento_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_operacional_departamento")

            logger.info("✅ Configurações operacionais verificadas no Django:")
            logger.info(
                f"   - Atendente Humano Config ID: {atendente_config.id}"
            )
            logger.info(
                f"   - Departamento Config ID: {departamento_config.id}"
            )
            logger.info(
                f"   - Ambas prontas para sincronização: {atendente_config.is_ready_for_sync() and departamento_config.is_ready_for_sync()}"
            )

        except Exception as e:
            logger.error(
                f"❌ Falha na construção das databases operacionais: {e}"
            )
            raise


class NotionAtendimentosDatabaseConstructor:
    """
    Construtor de databases no Notion para Atendimento e Mensagem
    com relacionamentos configurados corretamente.
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

    async def create_atendimento_database(self) -> Any:
        """Cria a database de Atendimentos no Notion (sem relacionamentos iniciais)."""
        logger.info("Criando database de Atendimentos no Notion...")

        # Propriedades básicas para Atendimentos (sem relacionamentos iniciais)
        properties = {
            # Assunto passa a ser o título principal
            "Assunto": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "fila", "color": "gray"},
                        {"name": "em_atendimento", "color": "blue"},
                        {"name": "aguardando_retorno", "color": "yellow"},
                        {"name": "resolvido", "color": "green"},
                        {"name": "cancelado", "color": "red"},
                    ]
                }
            },
            "Prioridade": {
                "select": {
                    "options": [
                        {"name": "baixa", "color": "gray"},
                        {"name": "normal", "color": "blue"},
                        {"name": "alta", "color": "orange"},
                        {"name": "urgente", "color": "red"},
                    ]
                }
            },
            # Novo campo de contexto da conversa
            "Contexto Conversa": {"rich_text": {}},
            "Data Início": {"date": {}},
            "Data Fim": {"date": {}},
            "Data Última Mensagem": {"date": {}},
            "Canal": {
                "select": {
                    "options": [
                        {"name": "whatsapp", "color": "green"},
                        {"name": "email", "color": "blue"},
                        {"name": "telefone", "color": "orange"},
                        {"name": "web", "color": "purple"},
                    ]
                }
            },
            "Tags": {"multi_select": {"options": []}},
            "Avaliação": {"number": {"format": "number"}},
            "Feedback": {"rich_text": {}},
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [
                {"type": "text", "text": {"content": "🎯 Atendimentos CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "🎯"},
            "initial_data_source": {
                "name": "Atendimentos",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Atendimentos criada: {created.id}")
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Atendimentos: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Atendimentos: {e}")
            raise

    async def create_mensagem_database(self, atendimento_db: Any) -> Any:
        """
        Cria a database de Mensagens no Notion COM RELACIONAMENTO para Atendimentos.
        """
        logger.info(
            "Criando database de Mensagens no Notion com relacionamento..."
        )

        # Obter o data_source_id da database de atendimentos
        if not atendimento_db.data_sources:
            raise ValueError("Database de atendimentos não possui data_source")

        atendimento_data_source_id = atendimento_db.data_sources[0]["id"]

        # Propriedades para Mensagens COM O RELACIONAMENTO
        properties = {
            "Conteúdo": {"title": {}},
            "Atendimento Relacionado": {
                "relation": {
                    "data_source_id": atendimento_data_source_id,
                    "single_property": {},
                    "dual_property": {
                        "synced_property_name": "Mensagens Relacionadas"
                    },
                }
            },
            # Campos de IA adicionais
            "Intenção Detectada": {"rich_text": {}},
            "Entidades Extraídas": {"rich_text": {}},
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "Texto", "color": "blue"},
                        {"name": "Imagem", "color": "green"},
                        {"name": "Vídeo", "color": "purple"},
                        {"name": "Áudio", "color": "orange"},
                        {"name": "Documento", "color": "gray"},
                        {"name": "Sticker", "color": "pink"},
                        {"name": "Localização", "color": "red"},
                        {"name": "Contato", "color": "blue"},
                        {"name": "Lista", "color": "yellow"},
                        {"name": "Botões", "color": "purple"},
                        {"name": "Enquete", "color": "green"},
                        {"name": "Reação", "color": "pink"},
                    ]
                }
            },
            "Remetente": {
                "select": {
                    "options": [
                        {"name": "contato", "color": "blue"},
                        {"name": "bot", "color": "gray"},
                        {"name": "atendente_humano", "color": "green"},
                    ]
                }
            },
            "Timestamp": {"date": {}},
            "Message ID WhatsApp": {"rich_text": {}},
            "Respondida": {"checkbox": {}},
            "Resposta Bot": {"rich_text": {}},
            "Confiança Resposta": {"number": {"format": "percent"}},
            "Metadados": {"rich_text": {}},
        }

        parameters = {
            "parent": {"type": "page_id", "page_id": self.notion_page_id},
            "title": [
                {
                    "type": "text",
                    "text": {"content": "💬 Mensagens CRM"},
                }
            ],
            "icon": {"type": "emoji", "emoji": "💬"},
            "initial_data_source": {
                "name": "Mensagens",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(f"✅ Database de Mensagens criada: {created.id}")
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Mensagens: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(f"❌ Erro ao criar database de Mensagens: {e}")
            raise

    async def add_all_relations_to_atendimento_database(
        self, mensagem_db: Any, atendimento_db: Any
    ) -> None:
        """
        Adiciona todos os relacionamentos na database de Atendimentos e
        cria as propriedades reversas em Contatos, Departamentos e
        Atendentes.

        Comentários em Português conforme padrão do projeto.
        """
        logger.info(
            "Adicionando relacionamentos na database de Atendimentos..."
        )

        # Buscar configs para obter IDs das outras databases
        try:
            contato_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_clientes_contato")
            departamento_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_operacional_departamento")
            atendente_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_operacional_atendente")
        except NotionDatabaseConfig.DoesNotExist as exc:
            logger.error(f"❌ Configuração não encontrada: {exc}")
            raise ValueError(
                "Execute primeiro clientes/contatos e operacional"
            )

        # Recuperar databases para extrair data_source_ids
        contato_db = await self.client.databases.retrieve(
            {"database_id": str(contato_config.notion_database_id)}
        )
        departamento_db = await self.client.databases.retrieve(
            {"database_id": str(departamento_config.notion_database_id)}
        )
        atendente_db_existing = await self.client.databases.retrieve(
            {"database_id": str(atendente_config.notion_database_id)}
        )

        contato_ds_id = (
            contato_db.data_sources[0]["id"]
            if contato_db.data_sources
            else None
        )
        departamento_ds_id = (
            departamento_db.data_sources[0]["id"]
            if departamento_db.data_sources
            else None
        )
        atendente_ds_id = (
            atendente_db_existing.data_sources[0]["id"]
            if atendente_db_existing.data_sources
            else None
        )
        mensagem_ds_id = (
            mensagem_db.data_sources[0]["id"]
            if mensagem_db.data_sources
            else None
        )
        atendimento_ds_id = (
            atendimento_db.data_sources[0]["id"]
            if atendimento_db.data_sources
            else None
        )

        if not all(
            [
                contato_ds_id,
                departamento_ds_id,
                atendente_ds_id,
                mensagem_ds_id,
                atendimento_ds_id,
            ]
        ):
            raise ValueError(
                "Uma ou mais databases não possuem data_source_id"
            )

        # Função auxiliar para obter o ID de uma propriedade por nome
        def _prop_id(db_info: Dict[str, Any], name: str) -> Optional[str]:
            """Obtém o ID da propriedade por nome, compatível com dict/obj."""

            def _get(obj: Any, key: str) -> Any:
                try:
                    return getattr(obj, key)
                except Exception:
                    return obj.get(key) if isinstance(obj, dict) else None

            data_sources = _get(db_info, "data_sources") or []
            for ds in data_sources:
                props_ds: Dict[str, Any] = _get(ds, "properties") or {}
                prop_ds = props_ds.get(name)
                if prop_ds:
                    return prop_ds.get("id") or getattr(prop_ds, "id", None)
            props_root: Dict[str, Any] = _get(db_info, "properties") or {}
            prop_root = props_root.get(name)
            if not prop_root:
                return None
            return prop_root.get("id") or getattr(prop_root, "id", None)

        # Obter IDs das propriedades existentes para garantir idempotência
        # Comentários em Português conforme padrão do projeto.
        # Mensagens: ID de "Atendimento Relacionado" (evita duplicatas)
        atendimento_rel_prop_id: Optional[str] = None
        try:
            if mensagem_db.data_sources:
                props_ds: Dict[str, Any] = mensagem_db.data_sources[0].get(
                    "properties", {}
                )
                rel_prop = props_ds.get("Atendimento Relacionado")
                if rel_prop:
                    atendimento_rel_prop_id = rel_prop.get("id")
        except Exception:
            atendimento_rel_prop_id = None
        if not atendimento_rel_prop_id:
            mensagem_db_info = await self.client.databases.retrieve(
                {"database_id": str(mensagem_db.id)}
            )
            atendimento_rel_prop_id = _prop_id(
                mensagem_db_info, "Atendimento Relacionado"
            )

        # Atendimentos: IDs de "Contato", "Departamento",
        # "Atendente" e "Mensagens Relacionadas"
        atendimento_db_info_pre = await self.client.request(
            method="get",
            path=f"databases/{atendimento_db.id}",
        )
        contato_prop_id_pre = _prop_id(atendimento_db_info_pre, "Contato")
        departamento_prop_id_pre = _prop_id(
            atendimento_db_info_pre, "Departamento"
        )
        atendente_prop_id_pre = _prop_id(atendimento_db_info_pre, "Atendente")
        mensagens_rel_prop_id_pre = _prop_id(
            atendimento_db_info_pre, "Mensagens Relacionadas"
        )

        # Atualiza o data source de Atendimentos com TODAS as relações
        # Montar atualização usando IDs quando disponíveis (evita duplicatas)
        update_atendimento = {
            "properties": {
                "Contato": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": contato_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimentos Relacionados",
                        },
                    },
                },
                "Departamento": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": departamento_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimentos Relacionados",
                        },
                    },
                },
                "Atendente": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": atendente_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimentos Relacionados",
                        },
                    },
                },
                "Mensagens Relacionadas": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": mensagem_ds_id,
                        # Sempre definir single_property para atender validação da API
                        "single_property": {},
                        # Usar dual_property por ID quando disponível; caso contrário, por nome
                        **(
                            {
                                "dual_property": {
                                    "synced_property_id": atendimento_rel_prop_id
                                }
                            }
                            if atendimento_rel_prop_id
                            else {
                                "dual_property": {
                                    "synced_property_name": "Atendimento Relacionado"
                                }
                            }
                        ),
                    },
                },
            }
        }

        try:
            await self.client.request(
                method="patch",
                path=f"data_sources/{atendimento_ds_id}",
                body=update_atendimento,
            )
            logger.info("✅ Relações principais adicionadas em Atendimentos")
        except Exception as exc:
            logger.error(
                f"❌ Erro ao atualizar relações em Atendimentos: {exc}"
            )
            raise

        # Obter IDs das props finais em Atendimentos para vincular reversos
        atendimento_db_info = await self.client.request(
            method="get", path=f"databases/{atendimento_db.id}"
        )
        contato_prop_id = _prop_id(atendimento_db_info, "Contato")
        departamento_prop_id = _prop_id(atendimento_db_info, "Departamento")
        atendente_prop_id = _prop_id(atendimento_db_info, "Atendente")

        # Criar propriedades reversas nas outras databases
        try:
            # Contatos: Atendimentos Relacionados
            # Atualizar/ criar reversos usando ID como chave quando existir
            contato_db_info = await self.client.request(
                method="get", path=f"databases/{contato_db.id}"
            )
            update_contato = {
                "properties": {
                    "Atendimentos Relacionados": {
                        "type": "relation",
                        "relation": {
                            "data_source_id": atendimento_ds_id,
                            "single_property": {},
                            "dual_property": (
                                {"synced_property_id": contato_prop_id}
                                if contato_prop_id
                                else {
                                    "synced_property_name": "Contato",
                                }
                            ),
                        },
                    }
                }
            }
            await self.client.request(
                method="patch",
                path=f"data_sources/{contato_ds_id}",
                body=update_contato,
            )

            # Departamentos: Atendimentos Relacionados
            departamento_db_info = await self.client.request(
                method="get", path=f"databases/{departamento_db.id}"
            )
            update_departamento = {
                "properties": {
                    "Atendimentos Relacionados": {
                        "type": "relation",
                        "relation": {
                            "data_source_id": atendimento_ds_id,
                            "single_property": {},
                            "dual_property": (
                                {
                                    "synced_property_id": departamento_prop_id,
                                }
                                if departamento_prop_id
                                else {
                                    "synced_property_name": "Departamento",
                                }
                            ),
                        },
                    }
                }
            }
            await self.client.request(
                method="patch",
                path=f"data_sources/{departamento_ds_id}",
                body=update_departamento,
            )

            # Atendentes: Atendimentos Relacionados
            atendente_db_info = await self.client.request(
                method="get", path=f"databases/{atendente_db_existing.id}"
            )
            update_atendente = {
                "properties": {
                    "Atendimentos Relacionados": {
                        "type": "relation",
                        "relation": {
                            "data_source_id": atendimento_ds_id,
                            "single_property": {},
                            "dual_property": (
                                {
                                    "synced_property_id": atendente_prop_id,
                                }
                                if atendente_prop_id
                                else {
                                    "synced_property_name": "Atendente",
                                }
                            ),
                        },
                    }
                }
            }
            await self.client.request(
                method="patch",
                path=f"data_sources/{atendente_ds_id}",
                body=update_atendente,
            )

            logger.info(
                "✅ Relações reversas adicionadas em Contatos, Departamentos e"
            )
            logger.info("   Atendentes")
        except Exception as exc:
            logger.error(f"❌ Erro ao adicionar relações reversas: {exc}")
            raise

        # Após configurar, executar limpeza de duplicatas
        try:
            await self.cleanup_duplicate_relations(
                atendimento_db=atendimento_db,
                mensagem_db=mensagem_db,
            )
            logger.info("🧹 Limpeza de relações duplicadas concluída")
        except Exception as exc:
            logger.warning(f"⚠️ Falha ao limpar duplicatas de relações: {exc}")

    async def repair_atendimento_relations(self) -> None:
        """Repara apenas os relacionamentos da database de Atendimentos.

        - Não recria bancos.
        - Usa IDs existentes quando disponíveis para evitar duplicações.
        - Configura relação bidirecional com Mensagens via synced_property_id.
        """
        logger.info("🛠️ Reparando relacionamentos em Atendimentos...")

        # Recuperar Mensagens e Atendimentos via config, com fallback por busca
        atendimento_db: Any = None
        mensagem_db: Any = None

        try:
            atendimento_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_atendimentos_atendimento")
            atendimento_db = await self.client.databases.retrieve(
                {"database_id": str(atendimento_config.notion_database_id)}
            )
        except Exception:
            logger.warning(
                "⚠️ Config de Atendimentos não encontrada; tentando busca"
            )
            try:
                res = await self.client.request(
                    method="post",
                    path="search",
                    body={
                        "query": "Atendimentos CRM",
                        "filter": {
                            "value": "database",
                            "property": "object",
                        },
                    },
                )
                results = (
                    res.get("results")
                    if isinstance(res, dict)
                    else getattr(res, "results", None)
                )
                atendimento_db = results[0] if results else None
            except Exception:
                atendimento_db = None

        try:
            mensagem_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_atendimentos_mensagem")
            mensagem_db = await self.client.databases.retrieve(
                {"database_id": str(mensagem_config.notion_database_id)}
            )
        except Exception:
            logger.warning(
                "⚠️ Config de Mensagens não encontrada; tentando busca"
            )
            try:
                res = await self.client.request(
                    method="post",
                    path="search",
                    body={
                        "query": "Mensagens CRM",
                        "filter": {
                            "value": "database",
                            "property": "object",
                        },
                    },
                )
                results = (
                    res.get("results")
                    if isinstance(res, dict)
                    else getattr(res, "results", None)
                )
                mensagem_db = results[0] if results else None
            except Exception:
                mensagem_db = None

        if not (atendimento_db and mensagem_db):
            raise ValueError(
                "Não foi possível localizar as databases de Atendimentos/Mensagens"
            )

        # Reaplicar configuração de relacionamentos de forma idempotente
        await self.add_all_relations_to_atendimento_database(
            mensagem_db=mensagem_db, atendimento_db=atendimento_db
        )
        logger.info(
            "✅ Reparação de relacionamentos concluída em Atendimentos"
        )

    async def create_example_pages_and_relation(
        self, mensagem_db: Any, atendimento_db: Any
    ) -> None:
        """Cria páginas de exemplo para testar o relacionamento."""
        logger.info(
            "Criando páginas de exemplo para Atendimentos e Mensagens..."
        )

        try:
            # Obter data_source_ids
            atendimento_data_source_id = (
                atendimento_db.data_sources[0]["id"]
                if atendimento_db.data_sources
                else None
            )
            mensagem_data_source_id = (
                mensagem_db.data_sources[0]["id"]
                if mensagem_db.data_sources
                else None
            )

            # 1. Criar uma página de Atendimento exemplo
            atendimento_page = await self.client.pages.create(
                parent={
                    "type": "data_source_id",
                    "data_source_id": atendimento_data_source_id,
                },
                properties={
                    "Assunto": {
                        "title": [
                            {"text": {"content": "Dúvida sobre produto"}}
                        ]
                    },
                    "Status": {"select": {"name": "em_atendimento"}},
                    "Prioridade": {"select": {"name": "normal"}},
                    "Contexto Conversa": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Cliente perguntando sobre políticas de troca."
                                }
                            }
                        ]
                    },
                    "Data Início": {
                        "date": {"start": "2024-01-15T09:00:00.000Z"}
                    },
                    "Canal": {"select": {"name": "whatsapp"}},
                },
            )
            logger.info(
                f"✅ Página de Atendimento exemplo criada: {atendimento_page.id}"
            )

            # 2. Criar uma página de Mensagem exemplo relacionada ao atendimento
            mensagem_page = await self.client.pages.create(
                parent={
                    "type": "data_source_id",
                    "data_source_id": mensagem_data_source_id,
                },
                properties={
                    "Conteúdo": {
                        "title": [
                            {
                                "text": {
                                    "content": "Olá, gostaria de saber mais sobre o produto X"
                                }
                            }
                        ]
                    },
                    "Atendimento Relacionado": {
                        "relation": [{"id": atendimento_page.id}]
                    },
                    "Tipo": {"select": {"name": "Texto"}},
                    "Remetente": {"select": {"name": "contato"}},
                    "Timestamp": {
                        "date": {"start": "2024-01-15T09:00:00.000Z"}
                    },
                    "Respondida": {"checkbox": False},
                },
            )
            logger.info(
                f"✅ Página de Mensagem exemplo criada: {mensagem_page.id}"
            )

            # 3. Não forçar o vínculo no atendimento.
            #    Evitamos duplicação criando a relação apenas no lado da Mensagem.
            #    O Notion mantém a relação bidirecional automaticamente via dual_property.
            logger.info(
                "✅ Relação criada pelo lado da Mensagem; Notion sincroniza o reverso"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao criar páginas de exemplo: {e}")
            raise

    async def save_database_configs(
        self, atendimento_db: Any, mensagem_db: Any
    ) -> None:
        """
        Salva as configurações das databases no modelo NotionDatabaseConfig.
        """
        logger.info(
            "💾 Salvando configurações de atendimentos no modelo NotionDatabaseConfig..."
        )

        try:
            # Obter data_source_ids
            atendimento_data_source_id = (
                atendimento_db.data_sources[0]["id"]
                if atendimento_db.data_sources
                else None
            )
            mensagem_data_source_id = (
                mensagem_db.data_sources[0]["id"]
                if mensagem_db.data_sources
                else None
            )

            # Configuração para Atendimentos
            atendimento_config = await sync_to_async(
                NotionDatabaseConfig.objects.update_or_create
            )(
                slug="ui_atendimentos_atendimento",
                defaults={
                    "name": "🎯 Atendimentos CRM",
                    "description": "Database para sincronização de atendimentos do sistema",
                    "notion_database_id": atendimento_db.id,
                    "data_source_id": atendimento_data_source_id,
                    "django_model": "ui.atendimentos.Atendimento",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Protocolo": {"title": {}},
                        "Contato": {"relation": {}},
                        "Departamento": {"relation": {}},
                        "Atendente": {"relation": {}},
                        "Status": {
                            "select": {
                                "options": [
                                    {"name": "fila", "color": "gray"},
                                    {
                                        "name": "em_atendimento",
                                        "color": "blue",
                                    },
                                    {
                                        "name": "aguardando_retorno",
                                        "color": "yellow",
                                    },
                                    {"name": "resolvido", "color": "green"},
                                    {"name": "cancelado", "color": "red"},
                                ]
                            }
                        },
                        "Prioridade": {
                            "select": {
                                "options": [
                                    {"name": "baixa", "color": "gray"},
                                    {"name": "normal", "color": "blue"},
                                    {"name": "alta", "color": "orange"},
                                    {"name": "urgente", "color": "red"},
                                ]
                            }
                        },
                        "Assunto": {"rich_text": {}},
                        "Data Início": {"date": {}},
                        "Data Fim": {"date": {}},
                        "Data Última Mensagem": {"date": {}},
                        "Canal": {
                            "select": {
                                "options": [
                                    {"name": "whatsapp", "color": "green"},
                                    {"name": "email", "color": "blue"},
                                    {"name": "telefone", "color": "orange"},
                                    {"name": "web", "color": "purple"},
                                ]
                            }
                        },
                        "Tags": {"multi_select": {"options": []}},
                        "Avaliação": {"number": {"format": "number"}},
                        "Feedback": {"rich_text": {}},
                        "Mensagens Relacionadas": {"relation": {}},
                    },
                    "field_mappings": {
                        "protocolo": "Protocolo",
                        "contato": "Contato",
                        "departamento": "Departamento",
                        "atendente_humano": "Atendente",
                        "status": "Status",
                        "prioridade": "Prioridade",
                        "assunto": "Assunto",
                        "data_inicio": "Data Início",
                        "data_fim": "Data Fim",
                        "data_ultima_mensagem": "Data Última Mensagem",
                        "canal": "Canal",
                        "tags": "Tags",
                        "avaliacao": "Avaliação",
                        "feedback": "Feedback",
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 7,  # Alta prioridade para atendimentos
                    "auto_sync": True,
                },
            )

            # Configuração para Mensagens
            mensagem_config = await sync_to_async(
                NotionDatabaseConfig.objects.update_or_create
            )(
                slug="ui_atendimentos_mensagem",
                defaults={
                    "name": "💬 Mensagens CRM",
                    "description": "Database para sincronização de mensagens do sistema",
                    "notion_database_id": mensagem_db.id,
                    "data_source_id": mensagem_data_source_id,
                    "django_model": "ui.atendimentos.Mensagem",
                    "django_app_label": "ui",
                    "notion_schema": {
                        "Conteúdo": {"title": {}},
                        "Atendimento Relacionado": {"relation": {}},
                        "Tipo": {
                            "select": {
                                "options": [
                                    {"name": "Texto", "color": "blue"},
                                    {"name": "Imagem", "color": "green"},
                                    {"name": "Vídeo", "color": "purple"},
                                    {"name": "Áudio", "color": "orange"},
                                    {"name": "Documento", "color": "gray"},
                                    {"name": "Sticker", "color": "pink"},
                                    {"name": "Localização", "color": "red"},
                                    {"name": "Contato", "color": "blue"},
                                    {"name": "Lista", "color": "yellow"},
                                    {"name": "Botões", "color": "purple"},
                                    {"name": "Enquete", "color": "green"},
                                    {"name": "Reação", "color": "pink"},
                                ]
                            }
                        },
                        "Remetente": {
                            "select": {
                                "options": [
                                    {"name": "contato", "color": "blue"},
                                    {"name": "bot", "color": "gray"},
                                    {
                                        "name": "atendente_humano",
                                        "color": "green",
                                    },
                                ]
                            }
                        },
                        "Timestamp": {"date": {}},
                        "Message ID WhatsApp": {"rich_text": {}},
                        "Respondida": {"checkbox": {}},
                        "Resposta Bot": {"rich_text": {}},
                        "Confiança Resposta": {
                            "number": {"format": "percent"}
                        },
                        "Metadados": {"rich_text": {}},
                    },
                    "field_mappings": {
                        "conteudo": "Conteúdo",
                        "atendimento": "Atendimento Relacionado",
                        "tipo": "Tipo",
                        "remetente": "Remetente",
                        "timestamp": "Timestamp",
                        "message_id_whatsapp": "Message ID WhatsApp",
                        "respondida": "Respondida",
                        "resposta_bot": "Resposta Bot",
                        "confianca_resposta": "Confiança Resposta",
                        "metadados": "Metadados",
                    },
                    "sync_enabled": True,
                    "sync_direction": "bidirectional",
                    "sync_priority": 8,  # Prioridade ainda maior para mensagens
                    "auto_sync": True,
                },
            )
            logger.info("✅ Configurações de atendimentos salvas com sucesso:")
            logger.info(f"   - Atendimento Config: {atendimento_config[0].id}")
            logger.info(f"   - Mensagem Config: {mensagem_config[0].id}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações: {e}")
            raise

    async def cleanup_duplicate_relations(
        self, atendimento_db: Any, mensagem_db: Any
    ) -> None:
        """
        Remove propriedades de relação duplicadas (ex.: "... 1") nas
        databases de Atendimentos e Mensagens.

        - Usa IDs das propriedades para remoção segura.
        - Mantém apenas os nomes canônicos definidos pelo script.

        Comentários em Português conforme padrão do projeto.
        """

        # Recuperar data_source_ids
        atendimento_ds_id = (
            atendimento_db.data_sources[0]["id"]
            if atendimento_db.data_sources
            else None
        )
        mensagem_ds_id = (
            mensagem_db.data_sources[0]["id"]
            if mensagem_db.data_sources
            else None
        )

        if not atendimento_ds_id or not mensagem_ds_id:
            raise ValueError(
                "Databases não possuem data_source_id para limpeza"
            )

        # Buscar propriedades atuais
        atendimento_info = await self.client.request(
            method="get", path=f"databases/{atendimento_db.id}"
        )
        mensagem_info = await self.client.request(
            method="get", path=f"databases/{mensagem_db.id}"
        )

        # Nomes canônicos em Atendimentos
        canonical_at = {
            "Contato",
            "Departamento",
            "Atendente",
            "Mensagens Relacionadas",
        }
        # Deduplicar: remover qualquer relation com sufixo numérico
        props_to_delete_at: Dict[str, None] = {}
        for name, prop in (atendimento_info.get("properties") or {}).items():
            if prop.get("type") == "relation":
                last = name.split(" ")[-1] if " " in name else ""
                is_number = last.isdigit()
                base = name.rsplit(" ", 1)[0] if is_number else name
                if is_number and base in canonical_at:
                    props_to_delete_at[name] = None
                elif name not in canonical_at:
                    # Se não é canônico, é potencial duplicata
                    props_to_delete_at[name] = None

        if props_to_delete_at:
            await self.client.request(
                method="patch",
                path=f"data_sources/{atendimento_ds_id}",
                body={"properties": props_to_delete_at},
            )
        # Remover propriedades canônicas dos data_sources adicionais
        at_data_sources = [
            ds.get("id") for ds in (atendimento_info.get("data_sources") or [])
        ]
        if at_data_sources and len(at_data_sources) > 1:
            for ds_id in at_data_sources[1:]:
                await self.client.request(
                    method="patch",
                    path=f"data_sources/{ds_id}",
                    body={"properties": {name: None for name in canonical_at}},
                )

        # Nomes canônicos em Mensagens
        canonical_msg = {"Atendimento Relacionado"}
        props_to_delete_msg: Dict[str, None] = {}
        for name, prop in (mensagem_info.get("properties") or {}).items():
            if prop.get("type") == "relation":
                last = name.split(" ")[-1] if " " in name else ""
                is_number = last.isdigit()
                base = name.rsplit(" ", 1)[0] if is_number else name
                if is_number and base in canonical_msg:
                    props_to_delete_msg[name] = None
                elif name not in canonical_msg:
                    props_to_delete_msg[name] = None

        if props_to_delete_msg:
            await self.client.request(
                method="patch",
                path=f"data_sources/{mensagem_ds_id}",
                body={"properties": props_to_delete_msg},
            )
        # Remover propriedades canônicas dos data_sources adicionais (Mensagens)
        msg_data_sources = [
            ds.get("id") for ds in (mensagem_info.get("data_sources") or [])
        ]
        if msg_data_sources and len(msg_data_sources) > 1:
            for ds_id in msg_data_sources[1:]:
                await self.client.request(
                    method="patch",
                    path=f"data_sources/{ds_id}",
                    body={
                        "properties": {name: None for name in canonical_msg}
                    },
                )

        # Limpeza adicional nas databases de Contatos, Departamentos e Atendentes
        try:
            contato_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_clientes_contato")
            departamento_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_operacional_departamento")
            atendente_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_operacional_atendente")
        except NotionDatabaseConfig.DoesNotExist:
            # Caso não existam, prossegue sem limpar esses bancos
            contato_config = None
            departamento_config = None
            atendente_config = None

        async def _delete_rev_dups(
            db_id: Optional[str], ds_id: Optional[str]
        ) -> None:
            if not db_id or not ds_id:
                return
            info = await self.client.request(
                method="get", path=f"databases/{db_id}"
            )
            props_to_delete: Dict[str, None] = {}
            for name, prop in (info.get("properties") or {}).items():
                if prop.get("type") != "relation":
                    continue
                last = name.split(" ")[-1] if " " in name else ""
                is_number = last.isdigit()
                base = name.rsplit(" ", 1)[0] if is_number else name
                if base == "Atendimentos Relacionados" and is_number:
                    props_to_delete[name] = None
            if props_to_delete:
                await self.client.request(
                    method="patch",
                    path=f"data_sources/{ds_id}",
                    body={"properties": props_to_delete},
                )
            # Remover propriedade canônica de data_sources adicionais
            ds_ids = [ds.get("id") for ds in (info.get("data_sources") or [])]
            if ds_ids and len(ds_ids) > 1:
                for extra_ds_id in ds_ids[1:]:
                    await self.client.request(
                        method="patch",
                        path=f"data_sources/{extra_ds_id}",
                        body={
                            "properties": {"Atendimentos Relacionados": None}
                        },
                    )

        # Limpeza ampla de duplicatas em Contatos, Departamentos e Atendentes
        async def _clean_extra_ds_canonicals(
            cfg: Optional[NotionDatabaseConfig], canonicals: set
        ) -> None:
            if not cfg:
                return
            # Recupera database e lista todos data_sources
            db = await self.client.databases.retrieve(
                {"database_id": str(cfg.notion_database_id)}
            )
            info = await self.client.request(
                method="get", path=f"databases/{db.id}"
            )
            ds_ids = [ds.get("id") for ds in (info.get("data_sources") or [])]
            # Apaga propriedades com sufixo numérico e remove canônicos dos DS extras
            # 1) apagar duplicatas com sufixo
            props_dups: Dict[str, None] = {}
            for name, prop in (info.get("properties") or {}).items():
                if prop.get("type") != "relation":
                    continue
                last = name.split(" ")[-1] if " " in name else ""
                is_number = last.isdigit()
                base = name.rsplit(" ", 1)[0] if is_number else name
                if base in canonicals and is_number:
                    props_dups[name] = None
            if props_dups and ds_ids:
                await self.client.request(
                    method="patch",
                    path=f"data_sources/{ds_ids[0]}",
                    body={"properties": props_dups},
                )
            # 2) remover canônicos dos data_sources adicionais
            if ds_ids and len(ds_ids) > 1:
                for extra_ds_id in ds_ids[1:]:
                    await self.client.request(
                        method="patch",
                        path=f"data_sources/{extra_ds_id}",
                        body={
                            "properties": {name: None for name in canonicals}
                        },
                    )

        await _clean_extra_ds_canonicals(
            contato_config,
            {"Clientes Relacionados", "Atendimentos Relacionados"},
        )
        await _clean_extra_ds_canonicals(
            departamento_config,
            {"Atendentes Relacionados", "Atendimentos Relacionados"},
        )
        await _clean_extra_ds_canonicals(
            atendente_config,
            {"Departamentos Relacionados", "Atendimentos Relacionados"},
        )

        # Executa limpeza por nome nas três bases
        if contato_config:
            contato_db = await self.client.databases.retrieve(
                {"database_id": str(contato_config.notion_database_id)}
            )
            contato_ds_id = (
                contato_db.data_sources[0]["id"]
                if contato_db.data_sources
                else None
            )
            await _delete_rev_dups(
                str(contato_config.notion_database_id), contato_ds_id
            )

        if departamento_config:
            departamento_db = await self.client.databases.retrieve(
                {"database_id": str(departamento_config.notion_database_id)}
            )
            departamento_ds_id = (
                departamento_db.data_sources[0]["id"]
                if departamento_db.data_sources
                else None
            )
            await _delete_rev_dups(
                str(departamento_config.notion_database_id),
                departamento_ds_id,
            )

        if atendente_config:
            atendente_db = await self.client.databases.retrieve(
                {"database_id": str(atendente_config.notion_database_id)}
            )
            atendente_ds_id = (
                atendente_db.data_sources[0]["id"]
                if atendente_db.data_sources
                else None
            )
            await _delete_rev_dups(
                str(atendente_config.notion_database_id), atendente_ds_id
            )

    async def construct_atendimentos_databases(self) -> None:
        """Constrói todas as databases de atendimentos necessárias com relacionamentos corretos."""
        logger.info(
            "🚀 Iniciando construção de databases de atendimentos no Notion com relacionamentos..."
        )

        try:
            # 1. Criar database de Atendimentos primeiro (sem relacionamentos)
            atendimento_db = await self.create_atendimento_database()

            # 2. Criar database de Mensagens COM RELACIONAMENTO para Atendimentos
            mensagem_db = await self.create_mensagem_database(atendimento_db)

            # 3. Aguardar um momento para as databases serem processadas
            await asyncio.sleep(2)

            # 4. Adicionar todos os relacionamentos na database de Atendimentos
            await self.add_all_relations_to_atendimento_database(
                mensagem_db, atendimento_db
            )

            # 5. Aguardar um momento antes de criar exemplos
            await asyncio.sleep(2)

            # 6. Criar páginas de exemplo para testar relacionamento
            try:
                await self.create_example_pages_and_relation(
                    mensagem_db, atendimento_db
                )
            except Exception as e:
                logger.warning(f"⚠️ Erro ao criar páginas de exemplo: {e}")
                logger.info(
                    "💡 Isso não afeta a criação das databases, apenas os testes"
                )

            # Exibir informações importantes das databases criadas
            logger.info(
                "🎉 Databases de atendimentos criadas com sucesso no Notion!"
            )
            logger.info(
                f"📋 Atendimentos: https://www.notion.so/{atendimento_db.id.replace('-', '')}"
            )
            logger.info(
                f"📋 Mensagens: https://www.notion.so/{mensagem_db.id.replace('-', '')}"
            )
            logger.info(f"🔑 ID Atendimentos: {atendimento_db.id}")
            logger.info(f"🔑 ID Mensagens: {mensagem_db.id}")

            if atendimento_db.data_sources:
                logger.info(
                    f"🔑 Data Source ID Atendimentos: {atendimento_db.data_sources[0]['id']}"
                )
            if mensagem_db.data_sources:
                logger.info(
                    f"🔑 Data Source ID Mensagens: {mensagem_db.data_sources[0]['id']}"
                )

            # Salvar configurações no modelo NotionDatabaseConfig
            await self.save_database_configs(atendimento_db, mensagem_db)
            logger.info(
                "✅ Configurações de atendimentos salvas com sucesso no Django!"
            )

            # Verificar configurações salvas
            atendimento_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_atendimentos_atendimento")
            mensagem_config = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_atendimentos_mensagem")

            logger.info(
                "✅ Configurações de atendimentos verificadas no Django:"
            )
            logger.info(f"   - Atendimento Config ID: {atendimento_config.id}")
            logger.info(f"   - Mensagem Config ID: {mensagem_config.id}")
            logger.info(
                f"   - Ambas prontas para sincronização: {atendimento_config.is_ready_for_sync() and mensagem_config.is_ready_for_sync()}"
            )

        except Exception as e:
            logger.error(
                f"❌ Falha na construção das databases de atendimentos: {e}"
            )
            raise


async def run_construction_clientes() -> None:
    """Função principal que executa a construção das databases de clientes/contatos."""
    try:
        constructor = NotionClientesDatabaseConstructor()
        await constructor.construct_clientes_databases()
    except Exception as e:
        logger.error(f"❌ Erro durante a execução: {e}")
        raise


async def run_construction_operacional() -> None:
    """Função principal que executa a construção das databases operacionais."""
    try:
        constructor = NotionOperacionalDatabaseConstructor()
        await constructor.construct_operacional_databases()
    except Exception as e:
        logger.error(f"❌ Erro durante a execução operacional: {e}")
        raise


async def run_construction_atendimentos() -> None:
    """Função principal que executa a construção das databases de atendimentos/mensagens."""
    try:
        constructor = NotionAtendimentosDatabaseConstructor()
        await constructor.construct_atendimentos_databases()
    except Exception as e:
        logger.error(f"❌ Erro durante a execução de atendimentos: {e}")
        raise


async def run_repair_atendimentos_relations() -> None:
    """Executa somente a rotina de reparo dos relacionamentos de Atendimentos."""
    try:
        constructor = NotionAtendimentosDatabaseConstructor()
        await constructor.repair_atendimento_relations()
    except Exception as e:
        logger.error(f"❌ Erro durante a reparação de relacionamentos: {e}")
        raise


def run_atendimentos() -> None:
    """Função de conveniência para executar apenas a construção de atendimentos."""
    try:
        asyncio.run(run_construction_atendimentos())
    except KeyboardInterrupt:
        logger.info("⏹️ Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal na construção de atendimentos: {e}")
        raise


async def run_full_construction_sequence() -> None:
    """
    Executa a sequência completa de construção:
    1. Clientes/Contatos
    2. Operacional (Departamento/Atendente)
    3. Atendimentos/Mensagens (depende das anteriores)
    """
    logger.info(
        "🚀 Iniciando sequência completa de construção de databases no Notion..."
    )

    try:
        # 1. Construir databases de clientes/contatos
        logger.info(
            "📋 Etapa 1/3: Construindo databases de clientes/contatos..."
        )
        await run_construction_clientes()
        logger.info("✅ Etapa 1/3 concluída com sucesso")

        # Aguardar um momento entre as etapas
        await asyncio.sleep(3)

        # 2. Construir databases operacionais
        logger.info("🏛️ Etapa 2/3: Construindo databases operacionais...")
        await run_construction_operacional()
        logger.info("✅ Etapa 2/3 concluída com sucesso")

        # Aguardar um momento entre as etapas
        await asyncio.sleep(3)

        # 3. Construir databases de atendimentos (depende das anteriores)
        logger.info(
            "🎯 Etapa 3/3: Construindo databases de atendimentos/mensagens..."
        )
        await run_construction_atendimentos()
        logger.info("✅ Etapa 3/3 concluída com sucesso")

        logger.info(
            "🎉 Sequência completa de construção finalizada com sucesso!"
        )
        logger.info("📊 Todas as databases estão prontas para sincronização:")
        logger.info("   - Clientes e Contatos")
        logger.info("   - Departamentos e Atendentes")
        logger.info("   - Atendimentos e Mensagens")

    except Exception as e:
        logger.error(f"❌ Erro na sequência completa de construção: {e}")
        raise


def run_full() -> None:
    """Função de conveniência para executar toda a sequência de construção."""
    try:
        asyncio.run(run_full_construction_sequence())
    except KeyboardInterrupt:
        logger.info("⏹️ Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal na construção completa: {e}")
        raise


# =============================================================================
# RESUMO DA IMPLEMENTAÇÃO - INTEGRAÇÃO ATENDIMENTOS/ MENSAGENS
# =============================================================================
#
# Nova classe adicionada: NotionAtendimentosDatabaseConstructor
#
# Funcionalidades implementadas:
# 1. Criação da database de Atendimentos com relacionamentos para:
#    - Contato (relacionamento existente)
#    - Departamento (relacionamento existente)
#    - Atendente (relacionamento existente)
#    - Mensagens (relacionamento bidirecional)
#
# 2. Criação da database de Mensagens com:
#    - Relacionamento com Atendimento (pai-filho)
#    - Suporte a todos os tipos de mensagem do sistema
#    - Metadados para respostas de bot e confiança
#
# 3. Configuração automática no Django com:
#    - NotionDatabaseConfig para Atendimento (slug: ui_atendimentos_atendimento)
#    - NotionDatabaseConfig para Mensagem (slug: ui_atendimentos_mensagem)
#    - Prioridade alta para sincronização (7 e 8 respectivamente)
#
# 4. Páginas de exemplo criadas para demonstrar o funcionamento
#
# Uso recomendado:
# # Executar após asyncio.run(run_construction_operacional())
# from notion_sync.scripts.script_constructor_notion import run_atendimentos
# run_atendimentos()
#
# Ou executar sequência completa:
# from notion_sync.scripts.script_constructor_notion import run_full
# run_full()
#
# A implementação segue exatamente o mesmo padrão das classes existentes,
# garantindo consistência e manutenibilidade do código.
# =============================================================================


def test_atendimentos_construction() -> None:
    """
    Função de teste para validar a construção de atendimentos após a operacional.
    Esta função deve ser usada apenas em ambiente de desenvolvimento/teste.
    """
    logger.info("🧪 Iniciando teste de construção de atendimentos...")

    try:
        # Verificar se as databases necessárias existem
        configs_necessarias = [
            "ui_clientes_contato",
            "ui_operacional_departamento",
            "ui_operacional_atendente",
        ]

        for slug in configs_necessarias:
            try:
                NotionDatabaseConfig.objects.get(slug=slug)
                logger.info(f"✅ Configuração {slug} encontrada")
            except NotionDatabaseConfig.DoesNotExist:
                logger.error(f"❌ Configuração {slug} não encontrada")
                logger.error(
                    "Execute primeiro a construção de clientes e operacional"
                )
                return

        # Executar a construção de atendimentos
        logger.info("🎯 Executando construção de atendimentos...")
        asyncio.run(run_construction_atendimentos())

        # Verificar se as novas configs foram criadas
        novas_configs = [
            "ui_atendimentos_atendimento",
            "ui_atendimentos_mensagem",
        ]

        for slug in novas_configs:
            try:
                config = NotionDatabaseConfig.objects.get(slug=slug)
                logger.info(
                    f"✅ Nova configuração {slug} criada com ID: {config.id}"
                )
                logger.info(f"   Database ID: {config.notion_database_id}")
                logger.info(f"   Data Source ID: {config.data_source_id}")
                logger.info(
                    f"   Pronta para sync: {config.is_ready_for_sync()}"
                )
            except NotionDatabaseConfig.DoesNotExist:
                logger.error(f"❌ Nova configuração {slug} não foi criada")

        logger.info("🧪 Teste de construção de atendimentos concluído!")

    except Exception as e:
        logger.error(f"❌ Erro no teste de construção: {e}")
        raise


def run(construction_type: str = "clientes") -> None:
    """
    Entry point para execução do script.

    Args:
        construction_type: Tipo de construção a ser executada ("clientes", "operacional", "atendimentos" ou "full")
    """
    try:
        if construction_type == "clientes":
            asyncio.run(run_construction_clientes())
        elif construction_type == "operacional":
            asyncio.run(run_construction_operacional())
        elif construction_type == "atendimentos":
            asyncio.run(run_construction_atendimentos())
        elif construction_type in [
            "repair_atendimentos",
            "repair_atendimentos_relations",
            "repair",
        ]:
            asyncio.run(run_repair_atendimentos_relations())
        elif construction_type == "full":
            asyncio.run(run_full_construction_sequence())
        else:
            raise ValueError(
                "Tipo de construção inválido. Use: clientes, operacional, atendimentos ou full"
            )
    except KeyboardInterrupt:
        logger.info("⏹️ Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise


def run_operacional() -> None:
    """Função de conveniência para executar apenas a construção operacional."""
    run("operacional")


if __name__ == "__main__":
    """Permite execução direta do script com argumentos de linha de comando."""
    import sys

    if len(sys.argv) > 1:
        construction_type = sys.argv[1]
        if construction_type in [
            "clientes",
            "operacional",
            "atendimentos",
            "full",
            "repair",
            "repair_atendimentos",
            "repair_atendimentos_relations",
        ]:
            run(construction_type)
        else:
            print("❌ Argumento inválido!")
            print("💡 Uso:")
            print("   python script_constructor_notion.py clientes")
            print("   python script_constructor_notion.py operacional")
            print("   python script_constructor_notion.py atendimentos")
            print("   python script_constructor_notion.py full")
            print("   python script_constructor_notion.py repair")
    else:
        # Default: executa a sequência completa
        run("full")
