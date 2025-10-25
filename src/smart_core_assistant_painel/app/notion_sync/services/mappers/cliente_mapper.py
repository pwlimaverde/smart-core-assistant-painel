"""
Mapper para conversão de dados do model Cliente (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Cliente
do Django para o formato de propriedades da API do Notion e vice-versa,
seguindo o planejamento de integração definido.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...exceptions import MappingError


class ClienteMapper:
    """
    Mapper para conversão de dados entre Cliente (Django) e Notion.

    Esta classe implementa métodos para converter dados do model Cliente
    para o formato esperado pela API do Notion e vice-versa, incluindo
    formatação de CNPJ, endereços e dados empresariais.
    """

    @staticmethod
    def to_notion_properties(cliente_sync: Any) -> Dict[str, Any]:
        """
        Converte um objeto ClienteSync do Django para propriedades do Notion.

        Este método utiliza os dados pré-processados do ClienteSync para
        gerar as propriedades no formato esperado pela API do Notion.

        Args:
            cliente_sync: Instância do model ClienteSync.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> cliente_sync = ClienteSync.objects.get(id=1)
            >>> properties = ClienteMapper.to_notion_properties(cliente_sync)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            cliente = cliente_sync.cliente
            properties: Dict[str, Any] = {}

            # Nome Fantasia (formatado) - Campo principal (title)
            nome_fantasia = cliente_sync.nome_fantasia_formatado or cliente.nome_fantasia
            properties["Nome Fantasia"] = {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": nome_fantasia.strip()}
                    }
                ]
            }

            # Razão Social (formatada)
            if cliente_sync.razao_social_formatada:
                properties["Razão Social"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente_sync.razao_social_formatada}
                        }
                    ]
                }

            # Tipo (select)
            tipo_options = [
                {"name": "Pessoa Jurídica", "color": "green"},
                {"name": "Pessoa Física", "color": "blue"}
            ]

            if cliente.tipo:
                tipo_map = {
                    "juridica": "Pessoa Jurídica",
                    "fisica": "Pessoa Física"
                }
                tipo_notion = tipo_map.get(cliente.tipo, cliente.tipo.title())

                # Garante que o tipo existe nas opções
                if not any(opt["name"] == tipo_notion for opt in tipo_options):
                    tipo_options.append({"name": tipo_notion, "color": "gray"})

                properties["Tipo"] = {
                    "select": {"name": tipo_notion}
                }

            # CNPJ (formatado - apenas dígitos)
            if cliente_sync.cnpj_formatado:
                properties["CNPJ"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente_sync.cnpj_formatado}
                        }
                    ]
                }

            # CPF (se presente)
            if cliente.cpf:
                cpf_limpo = re.sub(r'\D', '', cliente.cpf)
                properties["CPF"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cpf_limpo}
                        }
                    ]
                }

            # Telefone (formatado)
            if cliente_sync.telefone_formatado:
                properties["Telefone"] = {
                    "phone_number": cliente_sync.telefone_formatado
                }



            # Observações (se presentes)
            if cliente.observacoes:
                properties["Observações"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.observacoes[:2000]}  # Limite
                        }
                    ]
                }

            return properties

        except AttributeError as e:
            raise MappingError(
                message="Erro ao acessar atributo do ClienteSync",
                field_name=str(e),
                source_value=cliente_sync,
            ) from e
        except Exception as e:
            raise MappingError(
                message=f"Erro ao mapear ClienteSync para Notion: {str(e)}",
                source_value=cliente_sync,
            ) from e

    @staticmethod
    def from_notion_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para formato Django (Cliente).

        Este método extrai dados das propriedades do Notion e os converte
        para o formato esperado pelo model Cliente do Django.

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
            data: Dict[str, Any] = {}

            # Nome Fantasia (do título)
            if "Nome Fantasia" in properties and properties["Nome Fantasia"].get("title"):
                title_list = properties["Nome Fantasia"]["title"]
                if title_list:
                    nome_fantasia = "".join(
                        item.get("plain_text", "")
                        for item in title_list
                    ).strip()
                    if nome_fantasia:
                        data["nome_fantasia"] = nome_fantasia

            # Razão Social
            if "Razão Social" in properties:
                rs_field = properties["Razão Social"]
                if rs_field.get("rich_text"):
                    text_list = rs_field["rich_text"]
                    if text_list:
                        razao_social = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if razao_social:
                            data["razao_social"] = razao_social

            # Tipo
            if "Tipo" in properties:
                tipo_field = properties["Tipo"]
                if tipo_field.get("select"):
                    tipo_notion = tipo_field["select"].get("name", "")
                    tipo_map_reverse = {
                        "Pessoa Jurídica": "juridica",
                        "Pessoa Física": "fisica"
                    }
                    data["tipo"] = tipo_map_reverse.get(tipo_notion, "juridica")

            # CNPJ
            if "CNPJ" in properties:
                cnpj_field = properties["CNPJ"]
                if cnpj_field.get("rich_text"):
                    text_list = cnpj_field["rich_text"]
                    if text_list:
                        cnpj = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if cnpj:
                            data["cnpj"] = ClienteMapper._format_cnpj(cnpj)

            # CPF
            if "CPF" in properties:
                cpf_field = properties["CPF"]
                if cpf_field.get("rich_text"):
                    text_list = cpf_field["rich_text"]
                    if text_list:
                        cpf = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if cpf:
                            data["cpf"] = ClienteMapper._format_cpf(cpf)

            # Telefone
            if "Telefone" in properties:
                tel_field = properties["Telefone"]
                if tel_field.get("phone_number"):
                    data["telefone"] = tel_field["phone_number"]

            # Site
            if "Website" in properties:
                site_field = properties["Website"]
                if site_field.get("url"):
                    data["site"] = site_field["url"]

            # Ramo de Atividade
            if "Ramo de Atividade" in properties:
                ramo_field = properties["Ramo de Atividade"]
                if ramo_field.get("rich_text"):
                    text_list = ramo_field["rich_text"]
                    if text_list:
                        ramo = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if ramo:
                            data["ramo_atividade"] = ramo

            # Endereço (campo completo)
            if "Endereço" in properties:
                end_field = properties["Endereço"]
                if end_field.get("rich_text"):
                    text_list = end_field["rich_text"]
                    if text_list:
                        endereco = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if endereco:
                            # Armazena endereço completo nos metadados
                            if "metadados" not in data:
                                data["metadados"] = {}
                            data["metadados"]["endereco_completo"] = endereco

            # Componentes do Endereço
            endereco_campos = ["CEP", "Cidade", "UF", "País"]
            for campo in endereco_campos:
                if campo in properties:
                    campo_field = properties[campo]
                    if campo_field.get("rich_text"):
                        text_list = campo_field["rich_text"]
                        if text_list:
                            valor = "".join(
                                item.get("plain_text", "")
                                for item in text_list
                            ).strip()
                            if valor:
                                # Mapeia nomes dos campos
                                campo_map = {
                                    "CEP": "cep",
                                    "Cidade": "cidade",
                                    "UF": "uf",
                                    "País": "pais"
                                }
                                data[campo_map.get(campo, campo.lower())] = valor

            # Status
            if "Status" in properties:
                status_field = properties["Status"]
                if status_field.get("select"):
                    status_name = status_field["select"].get("name", "")
                    data["ativo"] = status_name.lower() in ["ativo", "active", "enabled"]

            # Observações
            if "Observações" in properties:
                obs_field = properties["Observações"]
                if obs_field.get("rich_text"):
                    text_list = obs_field["rich_text"]
                    if text_list:
                        obs = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        ).strip()
                        if obs:
                            data["observacoes"] = obs

            # Datas
            datas_campos = ["Data Cadastro", "Última Atualização"]
            for campo in datas_campos:
                if campo in properties:
                    date_field = properties[campo]
                    if date_field.get("date") and date_field["date"].get("start"):
                        try:
                            data_iso = date_field["date"]["start"].replace('Z', '+00:00')
                            data_obj = datetime.fromisoformat(data_iso)

                            # Mapeia nomes dos campos
                            campo_map = {
                                "Data Cadastro": "data_cadastro",
                                "Última Atualização": "ultima_atualizacao"
                            }
                            data[campo_map.get(campo, campo.lower())] = data_obj
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
    def _format_cnpj(cnpj: str) -> str:
        """
        Formata CNPJ para o padrão brasileiro.

        Args:
            cnpj: CNPJ (apenas dígitos ou formatado).

        Returns:
            CNPJ formatado (XX.XXX.XXX/XXXX-XX).
        """
        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', cnpj)

        # Verifica se tem 14 dígitos
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"

        return cnpj  # Retorna original se não conseguir formatar

    @staticmethod
    def _format_cpf(cpf: str) -> str:
        """
        Formata CPF para o padrão brasileiro.

        Args:
            cpf: CPF (apenas dígitos ou formatado).

        Returns:
            CPF formatado (XXX.XXX.XXX-XX).
        """
        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', cpf)

        # Verifica se tem 11 dígitos
        if len(digits) == 11:
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"

        return cpf  # Retorna original se não conseguir formatar

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
            # Verifica campo obrigatório Nome Fantasia
            if "Nome Fantasia" not in properties or not properties["Nome Fantasia"].get("title"):
                return False

            # Verifica se há conteúdo no título
            title_content = properties["Nome Fantasia"]["title"]
            if not title_content or not any(
                item.get("text", {}).get("content", "").strip()
                for item in title_content
            ):
                return False

            # Valida CNPJ se presente
            if "CNPJ" in properties:
                cnpj_field = properties["CNPJ"]
                if cnpj_field.get("rich_text"):
                    text_list = cnpj_field["rich_text"]
                    if text_list:
                        cnpj = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        )
                        digits = re.sub(r'\D', '', cnpj)
                        if digits and len(digits) != 14:
                            return False

            # Valida CPF se presente
            if "CPF" in properties:
                cpf_field = properties["CPF"]
                if cpf_field.get("rich_text"):
                    text_list = cpf_field["rich_text"]
                    if text_list:
                        cpf = "".join(
                            item.get("plain_text", "")
                            for item in text_list
                        )
                        digits = re.sub(r'\D', '', cpf)
                        if digits and len(digits) != 11:
                            return False

            # Valida URL do site se presente
            if "Website" in properties:
                site = properties["Website"].get("url", "")
                if site and not (site.startswith("http://") or site.startswith("https://")):
                    return False

            return True

        except Exception:
            return False

    @staticmethod
    def get_database_schema() -> Dict[str, Any]:
        """
        Retorna o schema do database do Notion para Clientes.

        Este schema pode ser usado para criar ou validar o database no Notion,
        seguindo as melhores práticas definidas no planejamento.

        Returns:
            Dicionário com definição das propriedades do database.

        Example:
            >>> schema = ClienteMapper.get_database_schema()
            >>> # Use para criar database no Notion
        """
        return {
            "Nome Fantasia": {
                "title": {},
                "description": "Nome comercial do cliente"
            },
            "Razão Social": {
                "rich_text": {},
                "description": "Nome legal/oficial do cliente"
            },
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "Pessoa Jurídica", "color": "green"},
                        {"name": "Pessoa Física", "color": "blue"}
                    ]
                },
                "description": "Tipo de pessoa jurídica"
            },
            "CNPJ": {
                "rich_text": {},
                "description": "CNPJ (apenas dígitos)"
            },
            "CPF": {
                "rich_text": {},
                "description": "CPF (apenas dígitos)"
            },
            "Telefone": {
                "phone_number": {},
                "description": "Telefone no formato internacional"
            },
            "Website": {
                "url": {},
                "description": "Site da empresa"
            },
            "Ramo de Atividade": {
                "rich_text": {},
                "description": "Área de atuação do cliente"
            },
            "Endereço": {
                "rich_text": {},
                "description": "Endereço completo"
            },
            "CEP": {
                "rich_text": {},
                "description": "CEP do endereço"
            },
            "Cidade": {
                "rich_text": {},
                "description": "Cidade do cliente"
            },
            "UF": {
                "select": {
                    "options": [
                        {"name": "AC"}, {"name": "AL"}, {"name": "AP"}, {"name": "AM"},
                        {"name": "BA"}, {"name": "CE"}, {"name": "DF"}, {"name": "ES"},
                        {"name": "GO"}, {"name": "MA"}, {"name": "MT"}, {"name": "MS"},
                        {"name": "MG"}, {"name": "PA"}, {"name": "PB"}, {"name": "PR"},
                        {"name": "PE"}, {"name": "PI"}, {"name": "RJ"}, {"name": "RN"},
                        {"name": "RS"}, {"name": "RO"}, {"name": "RR"}, {"name": "SC"},
                        {"name": "SP"}, {"name": "SE"}, {"name": "TO"}
                    ]
                },
                "description": "Estado (UF)"
            },
            "País": {
                "rich_text": {},
                "description": "País (se não for Brasil)"
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Ativo", "color": "green"},
                        {"name": "Inativo", "color": "red"},
                        {"name": "Suspenso", "color": "yellow"}
                    ]
                },
                "description": "Status atual do cliente"
            },
            "Data Cadastro": {
                "date": {},
                "description": "Data de cadastro no sistema"
            },
            "Última Atualização": {
                "date": {},
                "description": "Data da última atualização"
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
            },
            "Observações": {
                "rich_text": {},
                "description": "Observações adicionais"
            }
        }
