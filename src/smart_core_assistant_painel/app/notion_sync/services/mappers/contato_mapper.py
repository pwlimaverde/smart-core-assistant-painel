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

            # Campo Status removido - não existe na database do Notion
            # Ativo está sendo mapeado como checkbox

            # Tags (multi-select)
            if contato_sync.tags_formatadas:
                # Garante que as tags estão no formato correto
                tags_validas = [
                    tag.strip()[:20]  # Limite de 20 caracteres no Notion
                    for tag in contato_sync.tags_formatadas
                    if tag.strip()
                ]

                if tags_validas:
                    properties["Tags"] = {
                        "multi_select": [
                            {"name": tag} for tag in tags_validas
                        ]
                    }

            # Campo Contato Principal removido - não existe na database do Notion
            # properties["Contato Principal"] = {
            #     "checkbox": contato_sync.principal
            # }

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


            # External ID (rich text - se existir)
            if contato_sync.external_id:
                properties["Notion ID"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": contato_sync.external_id}
                        }
                    ]
                }

            # Última sincronização
            if contato_sync.last_sync_at:
                properties["Última Sincronização"] = {
                    "date": {
                        "start": contato_sync.last_sync_at.isoformat()
                    }
                }

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
            if "Nome" in properties and properties["Nome"].get("title"):
                title_list = properties["Nome"]["title"]
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

                # Tenta phone_number primeiro
                if telefone_field.get("phone_number"):
                    data["telefone"] = ContatoMapper._normalize_phone_from_notion(
                        telefone_field["phone_number"]
                    )
                # Fallback para rich_text
                elif telefone_field.get("rich_text"):
                    text_list = telefone_field["rich_text"]
                    if text_list:
                        telefone = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if telefone:
                            data["telefone"] = ContatoMapper._normalize_phone_from_notion(
                                telefone
                            )

            # Email
            if "Email" in properties and properties["Email"].get("email"):
                email = properties["Email"]["email"].strip().lower()
                if email:
                    data["email"] = email

            # Nome do perfil WhatsApp
            if "WhatsApp Profile" in properties:
                wp_field = properties["WhatsApp Profile"]
                if wp_field.get("rich_text"):
                    text_list = wp_field["rich_text"]
                    if text_list:
                        nome_wp = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if nome_wp:
                            data["nome_perfil_whatsapp"] = nome_wp

            # Status (do select)
            if "Status" in properties:
                status_field = properties["Status"]
                if status_field.get("select"):
                    status_name = status_field["select"].get("name", "")
                    data["ativo"] = status_name.lower() in ["ativo", "active", "enabled"]

            # Tags (do multi-select)
            if "Tags" in properties:
                tags_field = properties["Tags"]
                if tags_field.get("multi_select"):
                    tags = [
                        item.get("name", "").strip()
                        for item in tags_field["multi_select"]
                        if item.get("name")
                    ]
                    if tags:
                        # Armazena como string separada por vírgulas
                        data["tags"] = ", ".join(tags)

            # Contato Principal (do checkbox)
            if "Contato Principal" in properties:
                principal_field = properties["Contato Principal"]
                if "checkbox" in principal_field:
                    # Salva nos metadados
                    if "metadados" not in data:
                        data["metadados"] = {}
                    data["metadados"]["principal"] = principal_field["checkbox"]

            # Datas
            if "Data Cadastro" in properties:
                date_field = properties["Data Cadastro"]
                if date_field.get("date") and date_field["date"].get("start"):
                    try:
                        data["data_cadastro"] = datetime.fromisoformat(
                            date_field["date"]["start"].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass  # Ignora datas inválidas

            if "Última Interação" in properties:
                date_field = properties["Última Interação"]
                if date_field.get("date") and date_field["date"].get("start"):
                    try:
                        data["ultima_interacao"] = datetime.fromisoformat(
                            date_field["date"]["start"].replace('Z', '+00:00')
                        )
                    except (ValueError, AttributeError):
                        pass  # Ignora datas inválidas

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
        """
        Prepara conteúdo no formato rich_text do Notion.

        Args:
            content: Conteúdo a ser formatado.

        Returns:
            Lista formatada para rich_text do Notion.
        """
        if not content or not content.strip():
            return []

        return [
            {
                "type": "text",
                "text": {"content": content.strip()[:2000]}  # Limite de caracteres
            }
        ]

    @staticmethod
    def _normalize_phone_from_notion(phone: str) -> str:
        """
        Normaliza telefone vindo do Notion para formato Django.

        Args:
            phone: Telefone no formato do Notion.

        Returns:
            Telefone normalizado (apenas dígitos, com 55 se brasileiro).
        """
        if not phone:
            return ""

        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', phone)

        # Se não começa com 55 e tem 10-11 dígitos, assume Brasil
        if len(digits) in [10, 11] and not digits.startswith('55'):
            digits = '55' + digits

        return digits

    @staticmethod
    def validate_for_notion(properties: Dict[str, Any]) -> bool:
        """
        Valida se as propriedades são válidas para o Notion.

        Args:
            properties: Propriedades a serem validadas.

        Returns:
            True se válido, False caso contrário.
        """
        try:
            # Verifica campo obrigatório Nome
            if "Nome" not in properties or not properties["Nome"].get("title"):
                return False

            # Verifica se há conteúdo no título
            title_content = properties["Nome"]["title"]
            if not title_content or not any(
                item.get("text", {}).get("content", "").strip()
                for item in title_content
            ):
                return False

            # Valida formato do email se presente
            if "Email" in properties:
                email = properties["Email"].get("email", "")
                if email and "@" not in email:
                    return False

            # Valida formato do telefone se presente
            if "Telefone" in properties:
                phone = properties["Telefone"].get("phone_number", "")
                if phone and not re.match(r'^\+\d{1,3}\s\d{2,}\s\d{4,}\s\d{4}$', phone):
                    # Não impede, mas poderia logar warning
                    pass

            return True

        except Exception:
            return False

    @staticmethod
    def get_database_schema() -> Dict[str, Any]:
        """
        Retorna o schema do database do Notion para Contatos.

        Este schema pode ser usado para criar ou validar o database no Notion,
        seguindo as melhores práticas definidas no planejamento.

        Returns:
            Dicionário com definição das propriedades do database.

        Example:
            >>> schema = ContatoMapper.get_database_schema()
            >>> # Use para criar database no Notion
        """
        return {
            "Nome": {
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
            "WhatsApp Profile": {
                "rich_text": {},
                "description": "Nome do perfil no WhatsApp"
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Ativo", "color": "green"},
                        {"name": "Inativo", "color": "red"},
                        {"name": "Bloqueado", "color": "gray"}
                    ]
                },
                "description": "Status atual do contato"
            },
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "Cliente", "color": "blue"},
                        {"name": "Lead", "color": "yellow"},
                        {"name": "Prospect", "color": "orange"},
                        {"name": "VIP", "color": "purple"}
                    ]
                },
                "description": "Tags para categorização"
            },
            "Contato Principal": {
                "checkbox": {},
                "description": "É o contato principal do cliente?"
            },
            "Data Cadastro": {
                "date": {},
                "description": "Data de cadastro no sistema"
            },
            "Última Interação": {
                "date": {},
                "description": "Data da última interação registrada"
            },
            "Django ID": {
                "number": {
                    "format": "number"
                },
                "description": "ID do registro no Django (referência)"
            },
            "Notion ID": {
                "rich_text": {},
                "description": "ID da página no Notion"
            },
            "Última Sincronização": {
                "date": {},
                "description": "Data da última sincronização"
            }
        }
