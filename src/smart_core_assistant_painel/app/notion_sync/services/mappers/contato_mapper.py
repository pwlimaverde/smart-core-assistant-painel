"""
Mapper para conversão de dados do model Contato (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Contato
do Django para o formato de propriedades da API do Notion e vice-versa,
seguindo o planejamento de integração definido.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...exceptions import MappingError


class ContatoMapper:
    """
    Mapper para conversão de dados entre Contato (Django) e Notion.

    Esta classe implementa métodos para converter dados do model Contato
    para o formato esperado pela API do Notion e vice-versa, incluindo
    formatação de telefones, normalização de emails e preparação de tags.
    """

    @staticmethod
    def to_notion_properties(contato_sync: Any) -> Dict[str, Any]:
        """
        Converte um objeto ContatoSync do Django para propriedades do Notion.

        Este método utiliza os dados pré-processados do ContatoSync para
        gerar as propriedades no formato esperado pela API do Notion.

        Args:
            contato_sync: Instância do model ContatoSync.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> contato_sync = ContatoSync.objects.get(id=1)
            >>> properties = ContatoMapper.to_notion_properties(contato_sync)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            contato = contato_sync.contato
            properties: Dict[str, Any] = {}

            # Nome (formatado) - Campo principal (title)
            nome = contato_sync.nome_formatado or "Sem Nome"
            properties["Nome Contato"] = {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": nome}
                    }
                ]
            }

            # Telefone (formatado para padrão internacional)
            if contato_sync.telefone_formatado:
                properties["Telefone"] = {
                    "phone_number": contato_sync.telefone_formatado
                }

            # Email (normalizado)
            if contato_sync.email_normalizado:
                properties["Email"] = {
                    "email": contato_sync.email_normalizado
                }

            # Nome do perfil WhatsApp
            if contato.nome_perfil_whatsapp:
                properties["Nome Perfil WhatsApp"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": contato.nome_perfil_whatsapp}
                        }
                    ]
                }

            # Ativo como checkbox
            properties["Ativo"] = {"checkbox": bool(contato.ativo)}

            # Datas
            if contato.data_cadastro:
                properties["Data Cadastro"] = {
                    "date": {
                        "start": contato.data_cadastro.isoformat()
                    }
                }

            # Última Interação
            if contato.ultima_interacao:
                properties["Última Interação"] = {
                    "date": {
                        "start": contato.ultima_interacao.isoformat()
                    }
                }

            # Relacionamento ManyToMany com Clientes
            try:
                empresas_vinculadas = contato.clientes.all()
                if empresas_vinculadas.exists():
                    # Prepara lista de empresas para o campo relation
                    empresas_ids = []
                    empresas_nomes = [cliente.nome_fantasia for cliente in empresas_vinculadas]

                    # Busca external_ids dos clientes sincronizados
                    from smart_core_assistant_painel.app.notion_sync.models import ClienteSync
                    for cliente in empresas_vinculadas:
                        try:
                            cliente_sync = ClienteSync.objects.get(cliente_id=cliente.id)
                            if cliente_sync.external_id:
                                empresas_ids.append(cliente_sync.external_id)
                        except ClienteSync.DoesNotExist:
                            # Se não tem sync, pula este cliente
                            continue

                    if empresas_ids:
                        # Usa campo relation nativo do Notion (se existir)
                        properties["Clientes Relacionados"] = {
                            "relation": [
                                {"id": emp_id} for emp_id in empresas_ids
                            ]
                        }

                        # Armazena informações adicionais em metadados (backup)
                        contato_sync.metadados['empresas_vinculadas'] = [
                            f"{cliente.id}:{cliente.nome_fantasia}"
                            for cliente in empresas_vinculadas
                        ]
            except Exception as e:
                # Log silencioso para não quebrar sincronização principal
                print(f"Aviso: Erro ao processar relacionamento de empresas: {e}")

            return properties

        except AttributeError as e:
            raise MappingError(
                message="Erro ao acessar atributo do ContatoSync",
                field_name=str(e),
                source_value=contato_sync,
            ) from e
        except Exception as e:
            raise MappingError(
                message=f"Erro ao mapear ContatoSync para Notion: {str(e)}",
                source_value=contato_sync,
            ) from e

    @staticmethod
    def from_notion_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para formato Django (Contato).

        Este método extrai dados das propriedades do Notion e os converte
        para o formato esperado pelo model Contato do Django.

        Args:
            properties: Dicionário com propriedades do Notion.

        Returns:
            Dicionário com dados formatados para o model Contato do Django.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> notion_props = {"Nome": {"title": [...]}, ...}
            >>> data = ContatoMapper.from_notion_properties(notion_props)
            >>> # Retorna dict com campos do Django
        """
        try:
            data: Dict[str, Any] = {}

            # Nome do contato (do título)
            if "Nome Contato" in properties and properties["Nome Contato"].get("title"):
                title_list = properties["Nome Contato"]["title"]
                if title_list:
                    nome = "".join(
                        item.get("plain_text", "")
                        for item in title_list
                    ).strip()
                    if nome:
                        data["nome_contato"] = nome

            # Telefone (do phone_number ou rich_text)
            if "Telefone" in properties:
                telefone_field = properties["Telefone"]
                if telefone_field.get("phone_number"):
                    data["telefone"] = ContatoMapper._normalize_phone_from_notion(
                        telefone_field["phone_number"]
                    )
                elif telefone_field.get("rich_text"):
                    text_list = telefone_field["rich_text"]
                    if text_list:
                        # compatibilidade legada
                        content = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if content:
                            data["telefone"] = content

            # Email
            if "Email" in properties and properties["Email"].get("email"):
                data["email"] = properties["Email"]["email"].strip()

            # Nome Perfil WhatsApp
            if "Nome Perfil WhatsApp" in properties and properties["Nome Perfil WhatsApp"].get("rich_text"):
                text_list = properties["Nome Perfil WhatsApp"]["rich_text"]
                if text_list:
                    content = "".join(
                        item.get("plain_text", "")
                        for item in text_list
                    ).strip()
                    if content:
                        data["nome_perfil_whatsapp"] = content

            # Ativo
            if "Ativo" in properties and isinstance(properties["Ativo"].get("checkbox"), bool):
                data["ativo"] = bool(properties["Ativo"]["checkbox"])

            # Datas
            if "Data Cadastro" in properties and properties["Data Cadastro"].get("date"):
                date_info = properties["Data Cadastro"]["date"]
                if isinstance(date_info, dict) and date_info.get("start"):
                    data["data_cadastro"] = datetime.fromisoformat(date_info["start"]) if date_info["start"] else None

            if "Última Interação" in properties and properties["Última Interação"].get("date"):
                date_info = properties["Última Interação"]["date"]
                if isinstance(date_info, dict) and date_info.get("start"):
                    data["ultima_interacao"] = datetime.fromisoformat(date_info["start"]) if date_info["start"] else None

            # Validação básica
            ContatoMapper.validate_for_notion(properties)

            return data

        except KeyError as e:
            raise MappingError(
                message="Propriedade esperada não encontrada",
                field_name=str(e),
                source_value=properties,
            ) from e
        except Exception as e:
            raise MappingError(
                message=f"Erro ao mapear propriedades do Notion: {str(e)}",
                source_value=properties,
            ) from e

    @staticmethod
    def _prepare_rich_text(content: str) -> List[Dict[str, Any]]:
        """Prepara rich_text para Notion com formatação simples e segura."""
        if not content:
            return []

        # Remove HTML básico e normaliza espaços
        content = re.sub(r"<[^>]+>", " ", content)
        content = re.sub(r"\s+", " ", content).strip()

        return [{
            "type": "text",
            "text": {"content": content[:2000]}
        }]

    @staticmethod
    def _normalize_phone_from_notion(phone: str) -> str:
        """Normaliza telefone vindo do Notion para formato simples."""
        if not phone:
            return ""
        # Remove tudo que não for dígito
        return re.sub(r"\D", "", phone)

    @staticmethod
    def validate_for_notion(properties: Dict[str, Any]) -> bool:
        """Valida estrutura mínima exigida pelo Notion."""
        # Título é obrigatório
        if "Nome Contato" not in properties:
            raise MappingError(message="Campo 'Nome Contato' é obrigatório no Notion")
        return True

    @staticmethod
    def get_database_schema() -> Dict[str, Any]:
        """
        Retorna definição de schema da database de Contatos no Notion,
        seguindo as melhores práticas definidas no planejamento.

        Returns:
            Dicionário com definição das propriedades do database.

        Example:
            >>> schema = ContatoMapper.get_database_schema()
            >>> # Use para criar database no Notion
        """
        return {
            "Nome Contato": {
                "title": {},
                "description": "Nome completo do contato"
            },
            "Telefone": {
                "phone_number": {},
                "description": "Telefone no formato internacional"
            },
            "Email": {
                "email": {},
                "description": "Endereço de email"
            },
            "Nome Perfil WhatsApp": {
                "rich_text": {},
                "description": "Nome do perfil no WhatsApp"
            },
            "Ativo": {
                "checkbox": {},
                "description": "Status ativo/inativo"
            },
            "Data Cadastro": {
                "date": {},
                "description": "Data de cadastro no sistema"
            },
            "Última Interação": {
                "date": {},
                "description": "Data da última interação registrada"
            },
            # Campo para relacionamento com Clientes (relation)
            "Clientes Relacionados": {
                "relation": {},
                "description": "Clientes vinculados a este contato (campo relation)"
            },
            # 📝 LEGADO: Mantido para compatibilidade com implementação anterior
            # "Empresas Vinculadas": {
            #     "rich_text": {},
            #     "description": "IDs e nomes das empresas vinculadas (formato: id:nome | id2:nome2)"
            # }
            # 📝 LEGADO: Mantido para compatibilidade com implementação anterior
            # "Empresas Vinculadas": {
            #     "rich_text": {},
            #     "description": "IDs e nomes das empresas vinculadas (formato: id:nome | id2:nome2)"
            # }
            # REMOVIDO: Django ID - campo opcional, pode não existir
            # "Django ID": {
            #     "number": {
            #         "format": "number"
            #     },
            #     "description": "ID do registro no Django (referência)"
            # },
            # REMOVIDO: Notion ID - campo não existe no database atual
            # "Notion ID": {
            #     "rich_text": {},
            #     "description": "ID da página no Notion"
            # },
            # REMOVIDO: Última Sincronização - campo não existe no database atual
            # "Última Sincronização": {
            #     "date": {},
            #     "description": "Data da última sincronização"
            # }
        }
