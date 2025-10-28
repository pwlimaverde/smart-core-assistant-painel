"""
Script para construção de databases no Notion com Relacionamentos.

Este script cria as databases necessárias para sincronização de modelos do Django
com o Notion, utilizando a API 2025-09-03 e configurando relacionamentos
bidirecionais entre as databases.

Módulos disponíveis:
1. Clientes/Contatos - Cria databases para Cliente e Contato com relacionamento
2. Operacional - Cria databases para Departamento e AtendenteHumano com relacionamento

Uso:
    # Para construir databases de clientes/contatos
    uv run python manage.py shell < notion_sync/scripts/script_constructor_notion.py
    uv run python -m notion_sync.scripts.script_constructor_notion.py

    # Para construir databases operacionais (departamento/atendente)
    from notion_sync.scripts.script_constructor_notion import run
    run("operacional")
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

# Adicionar o path do projeto ao sys.path para importar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configurar Django
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
                props: Dict[str, Any] = db_info.get("properties", {})
                prop = props.get(name)
                if not prop:
                    return None
                return prop.get("id") or getattr(prop, "id", None)

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
                    "type": "database_id",
                    "database_id": cliente_db.id,
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
                    "type": "database_id",
                    "database_id": contato_db.id,
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
                    "django_model": "ui.clientes.Cliente",
                    "django_app_label": "ui",
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

    async def create_atendente_humano_database(
        self, departamento_db: Any
    ) -> Any:
        """
        Cria a database de Atendentes Humanos no Notion COM RELACIONAMENTO para Departamentos.
        """
        logger.info(
            "Criando database de Atendentes Humanos no Notion com relacionamento..."
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
            # Propriedade relation apontando para Departamentos
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
                    "text": {"content": "👨‍💼 Atendentes Humanos CRM"},
                }
            ],
            "icon": {"type": "emoji", "emoji": "👨‍💼"},
            "initial_data_source": {
                "name": "AtendentesHumanos",
                "properties": properties,
            },
        }

        try:
            created = await self.client.databases.create(parameters)
            logger.info(
                f"✅ Database de Atendentes Humanos criada: {created.id}"
            )
            if created.data_sources:
                logger.info(
                    f"🔑 Data Source ID Atendentes Humanos: {created.data_sources[0]['id']}"
                )
            return created
        except Exception as e:
            logger.error(
                f"❌ Erro ao criar database de Atendentes Humanos: {e}"
            )
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
                props: Dict[str, Any] = db_info.get("properties", {})
                prop = props.get(name)
                if not prop:
                    return None
                return prop.get("id") or getattr(prop, "id", None)

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
                    "type": "database_id",
                    "database_id": departamento_db.id,
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
                    "type": "database_id",
                    "database_id": atendente_db.id,
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
                slug="ui_operacional_atendentehumano",
                defaults={
                    "name": "👨‍💼 Atendentes Humanos CRM",
                    "description": "Database para sincronização de atendentes humanos do sistema",
                    "notion_database_id": atendente_db.id,
                    "data_source_id": atendente_data_source_id,
                    "django_model": "ui.operacional.AtendenteHumano",
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

            # 2. Criar database de Atendentes Humanos COM RELACIONAMENTO para Departamentos
            atendente_db = await self.create_atendente_humano_database(
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
            )(slug="ui_operacional_atendentehumano")
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


def run(construction_type: str = "clientes") -> None:
    """
    Entry point para execução do script.

    Args:
        construction_type: Tipo de construção a ser executada ("clientes" ou "operacional")
    """
    try:
        asyncio.run(run_construction_clientes())
        asyncio.run(run_construction_operacional())

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
        if construction_type in ["clientes", "operacional"]:
            run(construction_type)
        else:
            print("❌ Argumento inválido!")
            print("💡 Uso:")
            print("   python script_constructor_notion.py clientes")
            print("   python script_constructor_notion.py operacional")
    else:
        # Default: constrói databases de clientes
        run("clientes")
