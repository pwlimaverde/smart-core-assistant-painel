"""
Mapper para conversão de dados do model Contato (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Contato
do Django para o formato de propriedades da API do Notion e vice-versa.
"""

from typing import Any

from ...exceptions import MappingError


class ContatoMapper:
    """
    Mapper para conversão de dados entre Contato (Django) e Notion.

    Esta classe implementa métodos para converter dados do model Contato
    para o formato esperado pela API do Notion e vice-versa.
    """

    @staticmethod
    def to_notion_properties(contato: Any) -> dict[str, Any]:
        """
        Converte um objeto Contato do Django para propriedades do Notion.

        Args:
            contato: Instância do model Contato.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> contato = Contato.objects.get(id=1)
            >>> properties = ContatoMapper.to_notion_properties(contato)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            properties: dict[str, Any] = {}

            # Nome do contato (título da página no Notion)
            if contato.nome_contato:
                properties["Nome"] = {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": contato.nome_contato}
                        }
                    ]
                }
            else:
                # Se não tem nome, usa o telefone como título
                properties["Nome"] = {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"Contato {contato.telefone}"}
                        }
                    ]
                }

            # Telefone (rich text)
            properties["Telefone"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": contato.telefone}
                    }
                ]
            }

            # Email (email ou rich_text)
            if contato.email:
                properties["Email"] = {
                    "email": contato.email
                }

            # Nome do perfil WhatsApp (rich text)
            if contato.nome_perfil_whatsapp:
                properties["WhatsApp"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": contato.nome_perfil_whatsapp}
                        }
                    ]
                }

            # Status ativo (checkbox)
            properties["Ativo"] = {
                "checkbox": contato.ativo
            }

            # Data de cadastro (date)
            if contato.data_cadastro:
                properties["Data Cadastro"] = {
                    "date": {
                        "start": contato.data_cadastro.isoformat()
                    }
                }

            # Última interação (date)
            if contato.ultima_interacao:
                properties["Última Interação"] = {
                    "date": {
                        "start": contato.ultima_interacao.isoformat()
                    }
                }

            # ID do Django (number - para referência)
            properties["Django ID"] = {
                "number": contato.id
            }

            return properties

        except AttributeError as e:
            raise MappingError(
                message="Erro ao acessar atributo do Contato",
                field_name=str(e),
                source_value=contato,
            ) from e
        except Exception as e:
            raise MappingError(
                message=f"Erro ao mapear Contato para Notion: {str(e)}",
                source_value=contato,
            ) from e

    @staticmethod
    def from_notion_properties(properties: dict[str, Any]) -> dict[str, Any]:
        """
        Converte propriedades do Notion para formato Django (Contato).

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
            data: dict[str, Any] = {}

            # Nome do contato (do título)
            if "Nome" in properties and properties["Nome"].get("title"):
                title_list = properties["Nome"]["title"]
                if title_list:
                    data["nome_contato"] = "".join(
                        item["plain_text"] for item in title_list
                    )

            # Telefone (de rich_text)
            if "Telefone" in properties and properties["Telefone"].get("rich_text"):
                text_list = properties["Telefone"]["rich_text"]
                if text_list:
                    data["telefone"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # Email
            if "Email" in properties and properties["Email"].get("email"):
                data["email"] = properties["Email"]["email"]

            # Nome do perfil WhatsApp
            if "WhatsApp" in properties and properties["WhatsApp"].get("rich_text"):
                text_list = properties["WhatsApp"]["rich_text"]
                if text_list:
                    data["nome_perfil_whatsapp"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # Status ativo
            if "Ativo" in properties and "checkbox" in properties["Ativo"]:
                data["ativo"] = properties["Ativo"]["checkbox"]

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
    def get_database_schema() -> dict[str, Any]:
        """
        Retorna o schema do database do Notion para Contatos.

        Este schema pode ser usado para criar ou validar o database no Notion.

        Returns:
            Dicionário com definição das propriedades do database.

        Example:
            >>> schema = ContatoMapper.get_database_schema()
            >>> # Use para criar database no Notion
        """
        return {
            "Nome": {"title": {}},  # Título da página
            "Telefone": {"rich_text": {}},
            "Email": {"email": {}},
            "WhatsApp": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Cadastro": {"date": {}},
            "Última Interação": {"date": {}},
            "Django ID": {"number": {}},
        }
