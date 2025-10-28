"""Mapper para conversão de dados do model Cliente (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Cliente
do Django para o formato de propriedades da API do Notion e vice-versa,
seguindo o planejamento de integração definido.
"""

import re
from datetime import datetime
from typing import Any, Dict

from ...exceptions import MappingError


class ClienteMapper:
    """Mapper para conversão de dados entre Cliente (Django) e Notion."""

    @staticmethod
    def to_notion_properties(cliente_sync: Any) -> Dict[str, Any]:
        """Converte um objeto ClienteSync do Django para propriedades do Notion."""
        try:
            cliente = cliente_sync.cliente
            properties: Dict[str, Any] = {}

            # Nome Fantasia (formatado) - Campo principal (title)
            nome_fantasia = (
                cliente_sync.nome_fantasia_formatado or cliente.nome_fantasia
            )
            properties["Nome Fantasia"] = {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": nome_fantasia.strip()},
                    }
                ]
            }

            # Razão Social (formatada)
            if cliente_sync.razao_social_formatada:
                properties["Razão Social"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": cliente_sync.razao_social_formatada
                            },
                        }
                    ]
                }

            # Tipo (select) → usar valores: "juridica" | "fisica"
            if getattr(cliente, "tipo", None):
                tipo_value = str(cliente.tipo).lower()
                if tipo_value not in ["juridica", "fisica"]:
                    tipo_value = "juridica"
                properties["Tipo"] = {"select": {"name": tipo_value}}

            # CNPJ (apenas dígitos)
            if getattr(cliente_sync, "cnpj_formatado", None):
                properties["CNPJ"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente_sync.cnpj_formatado},
                        }
                    ]
                }

            # Relacionamento ManyToMany com Contatos (relation)
            try:
                contatos = cliente.contatos.all()
                from smart_core_assistant_painel.app.notion_sync.models import (
                    ContatoSync,
                )

                contatos_ids: list[str] = []
                for contato in contatos:
                    try:
                        contato_sync = ContatoSync.objects.get(
                            contato_id=contato.id
                        )
                        if contato_sync.external_id:
                            contatos_ids.append(str(contato_sync.external_id))
                    except ContatoSync.DoesNotExist:
                        continue

                properties["Contatos Relacionados"] = {
                    "relation": [{"id": cid} for cid in contatos_ids]
                }
            except Exception:
                pass

            # CPF (se presente)
            if getattr(cliente, "cpf", None):
                cpf_limpo = re.sub(r"\D", "", cliente.cpf)
                properties["CPF"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": cpf_limpo}}
                    ]
                }

            # Telefone (formatado)
            if getattr(cliente_sync, "telefone_formatado", None):
                properties["Telefone"] = {
                    "phone_number": cliente_sync.telefone_formatado
                }

            # Site (url)
            if getattr(cliente, "site", None):
                properties["Site"] = {"url": cliente.site}

            # Ramo Atividade
            if getattr(cliente, "ramo_atividade", None):
                properties["Ramo Atividade"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.ramo_atividade},
                        }
                    ]
                }

            # Endereço componentes (se presentes)
            if getattr(cliente, "cep", None):
                properties["CEP"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": cliente.cep}}
                    ]
                }
            if getattr(cliente, "logradouro", None):
                properties["Logradouro"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cliente.logradouro},
                        }
                    ]
                }
            if getattr(cliente, "numero", None):
                properties["Número"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": cliente.numero}}
                    ]
                }
            if getattr(cliente, "bairro", None):
                properties["Bairro"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": cliente.bairro}}
                    ]
                }
            if getattr(cliente, "cidade", None):
                properties["Cidade"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": cliente.cidade}}
                    ]
                }
            if getattr(cliente, "uf", None):
                properties["UF"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": cliente.uf.upper()}}
                    ]
                }

            # Ativo (checkbox)
            properties["Ativo"] = {"checkbox": bool(getattr(cliente, "ativo", True))}

            # Observações (se presentes)
            if getattr(cliente, "observacoes", None):
                properties["Observações"] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": str(cliente.observacoes)[:2000]
                            },
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
        """Converte propriedades do Notion para formato Django (Cliente)."""
        try:
            data: Dict[str, Any] = {}

            # Nome Fantasia (do título)
            if "Nome Fantasia" in properties and properties["Nome Fantasia"].get("title"):
                title_list = properties["Nome Fantasia"]["title"]
                if title_list:
                    nome_fantasia = "".join(
                        item.get("plain_text", "") for item in title_list
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
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if razao_social:
                            data["razao_social"] = razao_social

            # Tipo (select)
            if "Tipo" in properties:
                tipo_field = properties["Tipo"]
                if tipo_field.get("select"):
                    tipo_notion = tipo_field["select"].get("name", "")
                    if tipo_notion.lower() in ["juridica", "fisica"]:
                        data["tipo"] = tipo_notion.lower()
                    else:
                        tipo_map_reverse = {
                            "Pessoa Jurídica": "juridica",
                            "Pessoa Física": "fisica",
                        }
                        data["tipo"] = tipo_map_reverse.get(tipo_notion, "juridica")

            # Site
            if "Site" in properties:
                site_field = properties["Site"]
                if site_field.get("url"):
                    data["site"] = site_field["url"]

            # Ramo de Atividade
            if "Ramo Atividade" in properties:
                ramo_field = properties["Ramo Atividade"]
                if ramo_field.get("rich_text"):
                    text_list = ramo_field["rich_text"]
                    if text_list:
                        ramo = "".join(
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if ramo:
                            data["ramo_atividade"] = ramo

            # Logradouro e Número
            if "Logradouro" in properties:
                log_field = properties["Logradouro"]
                if log_field.get("rich_text"):
                    text_list = log_field["rich_text"]
                    if text_list:
                        val = "".join(
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if val:
                            data["logradouro"] = val
            if "Número" in properties:
                num_field = properties["Número"]
                if num_field.get("rich_text"):
                    text_list = num_field["rich_text"]
                    if text_list:
                        val = "".join(
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if val:
                            data["numero"] = val

            # Bairro
            if "Bairro" in properties:
                bairro_field = properties["Bairro"]
                if bairro_field.get("rich_text"):
                    text_list = bairro_field["rich_text"]
                    if text_list:
                        bairro = "".join(
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if bairro:
                            data["bairro"] = bairro

            # Cidade
            if "Cidade" in properties:
                cidade_field = properties["Cidade"]
                if cidade_field.get("rich_text"):
                    text_list = cidade_field["rich_text"]
                    if text_list:
                        cidade = "".join(
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if cidade:
                            data["cidade"] = cidade

            # UF
            if "UF" in properties:
                uf_field = properties["UF"]
                if uf_field.get("rich_text"):
                    text_list = uf_field["rich_text"]
                    if text_list:
                        uf = "".join(
                            item.get("plain_text", "") for item in text_list
                        ).strip()
                        if uf:
                            data["uf"] = uf.upper()

            # Ativo (checkbox)
            if "Ativo" in properties and isinstance(properties["Ativo"].get("checkbox"), bool):
                data["ativo"] = properties["Ativo"]["checkbox"]

            # Status (opcional) - mantido para compatibilidade
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
                            item.get("plain_text", "") for item in text_list
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
                            data_iso = date_field["date"]["start"].replace("Z", "+00:00")
                            data_obj = datetime.fromisoformat(data_iso)

                            campo_map = {
                                "Data Cadastro": "data_cadastro",
                                "Última Atualização": "ultima_atualizacao",
                            }
                            data[campo_map.get(campo, campo.lower())] = data_obj
                        except (ValueError, AttributeError):
                            pass

            # Relacionamento com Contatos
            if "metadados" in data and "contatos_vinculados" in data["metadados"]:
                contatos_info = data["metadados"]["contatos_vinculados"]
                if isinstance(contatos_info, list):
                    data["metadados"]["contatos_vinculados_lista"] = contatos_info
                elif "contatos_vinculados_notion" in data["metadados"]:
                    contatos_text = data["metadados"]["contatos_vinculados_notion"]
                    if contatos_text and "|" in contatos_text:
                        contatos_info = [item.strip() for item in contatos_text.split("|")]
                        data["metadados"]["contatos_vinculados_lista"] = contatos_info

            return data

        except Exception as exc:
            raise MappingError(
                message=f"Erro ao converter propriedades do Notion para Cliente: {exc}",
                source_value=properties,
            ) from exc

    @staticmethod
    def _format_cnpj(cnpj: str) -> str:
        """Formata CNPJ para o padrão brasileiro."""
        digits = re.sub(r"\D", "", cnpj)
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
        return cnpj

    @staticmethod
    def _format_cpf(cpf: str) -> str:
        """Formata CPF para o padrão brasileiro."""
        digits = re.sub(r"\D", "", cpf)
        if len(digits) == 11:
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"
        return cpf

    @staticmethod
    def validate_for_notion(cliente_sync: Any) -> list[str]:
        """Valida se o cliente está pronto para sincronização."""
        errors: list[str] = []

        if not cliente_sync.cliente.nome_fantasia:
            errors.append("Nome fantasia é obrigatório")

        if cliente_sync.cliente.cnpj:
            cnpj_limpo = re.sub(r"\D", "", cliente_sync.cliente.cnpj)
            if len(cnpj_limpo) != 14:
                errors.append("CNPJ inválido")

        if cliente_sync.cliente.cpf:
            cpf_limpo = re.sub(r"\D", "", cliente_sync.cliente.cpf)
            if len(cpf_limpo) != 11:
                errors.append("CPF inválido")

        return errors

    @staticmethod
    def get_database_schema() -> Dict[str, Any]:
        """Retorna o schema do database do Notion para Clientes."""
        return {
            "Nome Fantasia": {
                "title": {},
                "description": "Nome comercial do cliente",
            },
            "Razão Social": {
                "rich_text": {},
                "description": "Nome legal/oficial do cliente",
            },
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "fisica", "color": "blue"},
                        {"name": "juridica", "color": "green"},
                    ]
                },
                "description": "Tipo de pessoa jurídica",
            },
            "CNPJ": {"rich_text": {}, "description": "CNPJ (apenas dígitos)"},
            "CPF": {"rich_text": {}, "description": "CPF (apenas dígitos)"},
            "Telefone": {
                "phone_number": {},
                "description": "Telefone no formato internacional",
            },
            "Site": {"url": {}, "description": "Site da empresa"},
            "Ramo Atividade": {
                "rich_text": {},
                "description": "Área de atuação do cliente",
            },
            "CEP": {"rich_text": {}, "description": "CEP do endereço"},
            "Logradouro": {"rich_text": {}, "description": "Logradouro"},
            "Número": {"rich_text": {}, "description": "Número"},
            "Bairro": {"rich_text": {}, "description": "Bairro do cliente"},
            "Cidade": {"rich_text": {}, "description": "Cidade do cliente"},
            "UF": {"rich_text": {}, "description": "Estado (UF) do cliente"},
            "Ativo": {"checkbox": {}, "description": "Status de atividade do cliente"},
            "País": {
                "rich_text": {},
                "description": "País (se não for Brasil)",
            },
            "Data Cadastro": {
                "date": {},
                "description": "Data de cadastro no sistema",
            },
            "Última Atualização": {
                "date": {},
                "description": "Data da última atualização",
            },
            "Django ID": {
                "number": {"format": "number"},
                "description": "ID do registro no Django (referência)",
            },
            "Notion ID": {
                "rich_text": {},
                "description": "ID da página no Notion",
            },
            "Última Sincronização": {
                "date": {},
                "description": "Data da última sincronização",
            },
            "Observações": {
                "rich_text": {},
                "description": "Observações adicionais",
            },
            "Contatos Relacionados": {
                "relation": {},
                "description": "Contatos vinculados a este cliente",
            },
        }
