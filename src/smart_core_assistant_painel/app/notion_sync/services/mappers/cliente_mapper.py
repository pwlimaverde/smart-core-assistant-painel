"""
Mapper para conversão de dados do model Cliente (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Cliente
do Django para o formato de propriedades da API do Notion e vice-versa.
"""

from typing import Any

from ...exceptions import MappingError


class ClienteMapper:
    """
    Mapper para conversão de dados entre Cliente (Django) e Notion.

    Esta classe implementa métodos para converter dados do model Cliente
    para o formato esperado pela API do Notion e vice-versa.
    """

    @staticmethod
    def to_notion_properties(cliente: Any) -> dict[str, Any]:
        """
        Converte um objeto Cliente do Django para propriedades do Notion.

        Args:
            cliente: Instância do model Cliente.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> cliente = Cliente.objects.get(id=1)
            >>> properties = ClienteMapper.to_notion_properties(cliente)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            properties: dict[str, Any] = {}

            # Nome Fantasia (título da página no Notion)
            properties["Nome Fantasia"] = {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": cliente.nome_fantasia}
                    }
                ]
            }

            # Razão Social (rich text)
            if cliente.razao_social:
                properties["Razão Social"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.razao_social}
                        }
                    ]
                }

            # Tipo (select)
            if cliente.tipo:
                tipo_map = {
                    "fisica": "Pessoa Física",
                    "juridica": "Pessoa Jurídica"
                }
                properties["Tipo"] = {
                    "select": {
                        "name": tipo_map.get(cliente.tipo, cliente.tipo)
                    }
                }

            # CNPJ (rich text)
            if cliente.cnpj:
                properties["CNPJ"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.cnpj}
                        }
                    ]
                }

            # CPF (rich text)
            if cliente.cpf:
                properties["CPF"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.cpf}
                        }
                    ]
                }

            # Telefone (phone_number ou rich_text)
            if cliente.telefone:
                properties["Telefone"] = {
                    "phone_number": cliente.telefone
                }

            # Site (url)
            if cliente.site:
                properties["Site"] = {
                    "url": cliente.site
                }

            # Ramo de Atividade (rich text)
            if cliente.ramo_atividade:
                properties["Ramo de Atividade"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.ramo_atividade}
                        }
                    ]
                }

            # Endereço completo (rich text - computed)
            endereco_completo = cliente.get_endereco_completo()
            if endereco_completo:
                properties["Endereço"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": endereco_completo}
                        }
                    ]
                }

            # CEP (rich text)
            if cliente.cep:
                properties["CEP"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.cep}
                        }
                    ]
                }

            # Cidade (rich text)
            if cliente.cidade:
                properties["Cidade"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.cidade}
                        }
                    ]
                }

            # Estado/UF (rich text)
            if cliente.uf:
                properties["UF"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.uf}
                        }
                    ]
                }

            # País (rich text)
            if cliente.pais:
                properties["País"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.pais}
                        }
                    ]
                }

            # Status ativo (checkbox)
            properties["Ativo"] = {
                "checkbox": cliente.ativo
            }

            # Data de cadastro (date)
            if cliente.data_cadastro:
                properties["Data Cadastro"] = {
                    "date": {
                        "start": cliente.data_cadastro.isoformat()
                    }
                }

            # Última atualização (date)
            if cliente.ultima_atualizacao:
                properties["Última Atualização"] = {
                    "date": {
                        "start": cliente.ultima_atualizacao.isoformat()
                    }
                }

            # ID do Django (number - para referência)
            properties["Django ID"] = {
                "number": cliente.id
            }

            return properties

        except AttributeError as e:
            raise MappingError(
                message="Erro ao acessar atributo do Cliente",
                field_name=str(e),
                source_value=cliente,
            ) from e
        except Exception as e:
            raise MappingError(
                message=f"Erro ao mapear Cliente para Notion: {str(e)}",
                source_value=cliente,
            ) from e

    @staticmethod
    def from_notion_properties(properties: dict[str, Any]) -> dict[str, Any]:
        """
        Converte propriedades do Notion para formato Django (Cliente).

        Args:
            properties: Dicionário com propriedades do Notion.

        Returns:
            Dicionário com dados formatados para o model Cliente do Django.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> notion_props = {"Nome Fantasia": {"title": [...]}, ...}
            >>> data = ClienteMapper.from_notion_properties(notion_props)
            >>> # Retorna dict com campos do Django
        """
        try:
            data: dict[str, Any] = {}

            # Nome Fantasia (do título)
            if "Nome Fantasia" in properties and properties["Nome Fantasia"].get("title"):
                title_list = properties["Nome Fantasia"]["title"]
                if title_list:
                    data["nome_fantasia"] = "".join(
                        item["plain_text"] for item in title_list
                    )

            # Razão Social
            if "Razão Social" in properties and properties["Razão Social"].get("rich_text"):
                text_list = properties["Razão Social"]["rich_text"]
                if text_list:
                    data["razao_social"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # Tipo
            if "Tipo" in properties and properties["Tipo"].get("select"):
                tipo_notion = properties["Tipo"]["select"]["name"]
                tipo_map_reverse = {
                    "Pessoa Física": "fisica",
                    "Pessoa Jurídica": "juridica"
                }
                data["tipo"] = tipo_map_reverse.get(tipo_notion, tipo_notion.lower())

            # CNPJ
            if "CNPJ" in properties and properties["CNPJ"].get("rich_text"):
                text_list = properties["CNPJ"]["rich_text"]
                if text_list:
                    data["cnpj"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # CPF
            if "CPF" in properties and properties["CPF"].get("rich_text"):
                text_list = properties["CPF"]["rich_text"]
                if text_list:
                    data["cpf"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # Telefone
            if "Telefone" in properties and properties["Telefone"].get("phone_number"):
                data["telefone"] = properties["Telefone"]["phone_number"]

            # Site
            if "Site" in properties and properties["Site"].get("url"):
                data["site"] = properties["Site"]["url"]

            # Ramo de Atividade
            if "Ramo de Atividade" in properties and properties["Ramo de Atividade"].get("rich_text"):
                text_list = properties["Ramo de Atividade"]["rich_text"]
                if text_list:
                    data["ramo_atividade"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # CEP
            if "CEP" in properties and properties["CEP"].get("rich_text"):
                text_list = properties["CEP"]["rich_text"]
                if text_list:
                    data["cep"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # Cidade
            if "Cidade" in properties and properties["Cidade"].get("rich_text"):
                text_list = properties["Cidade"]["rich_text"]
                if text_list:
                    data["cidade"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # UF
            if "UF" in properties and properties["UF"].get("rich_text"):
                text_list = properties["UF"]["rich_text"]
                if text_list:
                    data["uf"] = "".join(
                        item["plain_text"] for item in text_list
                    )

            # País
            if "País" in properties and properties["País"].get("rich_text"):
                text_list = properties["País"]["rich_text"]
                if text_list:
                    data["pais"] = "".join(
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
        Retorna o schema do database do Notion para Clientes.

        Este schema pode ser usado para criar ou validar o database no Notion.

        Returns:
            Dicionário com definição das propriedades do database.

        Example:
            >>> schema = ClienteMapper.get_database_schema()
            >>> # Use para criar database no Notion
        """
        return {
            "Nome Fantasia": {"title": {}},  # Título da página
            "Razão Social": {"rich_text": {}},
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "Pessoa Física", "color": "blue"},
                        {"name": "Pessoa Jurídica", "color": "green"}
                    ]
                }
            },
            "CNPJ": {"rich_text": {}},
            "CPF": {"rich_text": {}},
            "Telefone": {"phone_number": {}},
            "Site": {"url": {}},
            "Ramo de Atividade": {"rich_text": {}},
            "Endereço": {"rich_text": {}},
            "CEP": {"rich_text": {}},
            "Cidade": {"rich_text": {}},
            "UF": {"rich_text": {}},
            "País": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Cadastro": {"date": {}},
            "Última Atualização": {"date": {}},
            "Django ID": {"number": {}},
        }
