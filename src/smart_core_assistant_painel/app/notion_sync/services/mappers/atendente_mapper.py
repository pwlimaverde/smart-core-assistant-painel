"""
Mapper para conversão de dados do model Atendente (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Atendente
do Django para o formato de propriedades da API do Notion e vice-versa,
seguindo o planejamento de integração definido.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...exceptions import MappingError


class AtendenteMapper:
    """
    Mapper para conversão de dados entre Atendente (Django) e Notion.

    Esta classe implementa métodos para converter dados do model Atendente
    para o formato esperado pela API do Notion e vice-versa, incluindo
    formatação de telefones, status, cargos e relacionamentos.
    """

    @staticmethod
    def to_notion_properties(atendente_sync: Any) -> Dict[str, Any]:
        """
        Converte um objeto AtendenteSync do Django para propriedades do Notion.

        Este método utiliza os dados pré-processados do AtendenteSync para
        gerar as propriedades no formato esperado pela API do Notion.

        Args:
            atendente_sync: Instância do model AtendenteSync.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> atendente_sync = AtendenteSync.objects.get(id=1)
            >>> properties = AtendenteMapper.to_notion_properties(atendente_sync)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            atendente = atendente_sync.atendente
            properties: Dict[str, Any] = {}

            # Campo obrigatório: Nome (Title)
            properties["Nome"] = {
                "title": [{"text": {"content": atendente.nome or "Sem Nome"}}]
            }

            # Cargo (Rich Text)
            if atendente.cargo:
                properties["Cargo"] = {
                    "rich_text": [
                        {"text": {"content": atendente.cargo.strip()}}
                    ]
                }

            # Relacionamento com Departamento
            # Envia SEMPRE (inclusive vazio) para refletir remoções imediatas
            # e garantir visualização no banco de Departamentos.
            try:
                relation_list: List[Dict[str, str]] = []
                if atendente.departamento:
                    # Busca sync do departamento
                    from smart_core_assistant_painel.app.notion_sync.models import (
                        DepartamentoSync,
                    )

                    try:
                        dept_sync = DepartamentoSync.objects.get(
                            departamento=atendente.departamento
                        )
                        if dept_sync.external_id:
                            relation_list = [{"id": dept_sync.external_id}]

                            # Metadados auxiliares (backup do vínculo)
                            atendente_sync.metadados[
                                "departamento_vinculado"
                            ] = (
                                f"{atendente.departamento.id}:"
                                f"{atendente.departamento.nome}"
                            )
                    except DepartamentoSync.DoesNotExist:
                        # Sem sync do departamento, mantém lista vazia
                        relation_list = []

                properties["Departamentos Relacionados"] = {
                    "relation": relation_list
                }
            except Exception as e:
                # Log silencioso para não quebrar sincronização principal
                print(
                    f"Aviso: Erro ao processar relacionamento de departamento: {e}"
                )

            # Email (Email)
            if atendente.email:
                properties["Email"] = {
                    "email": atendente.email.lower().strip()
                }

            # Telefone (Phone Number)
            if atendente.telefone:
                telefone_formatado = AtendenteMapper._format_phone(
                    atendente.telefone
                )
                properties["Telefone"] = {"phone_number": telefone_formatado}

            # Horário Trabalho (Rich Text)
            if (
                hasattr(atendente, "horario_trabalho")
                and atendente.horario_trabalho
            ):
                import json

                properties["Horário Trabalho"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": json.dumps(
                                    atendente.horario_trabalho,
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ]
                }

            # Ativo (Checkbox)
            properties["Ativo"] = {"checkbox": bool(atendente.ativo)}

            # Disponível (Checkbox)
            properties["Disponível"] = {"checkbox": bool(atendente.disponivel)}

            # Capacidade Máxima (Number)
            properties["Capacidade Máxima"] = {
                "number": atendente.max_atendimentos_simultaneos
            }

            # Departamentos Relacionados (Relation -暂时不用关联，按用户要求不包含instance链接)
            # Removido conforme solicitação do usuário - não usar relacionamentos

            return properties

        except Exception as exc:
            raise MappingError(
                f"Erro ao converter Atendente para Notion: {exc}"
            ) from exc

    @staticmethod
    def from_notion_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para dados do model Atendente.

        Este método converte as propriedades vindas da API do Notion
        para o formato esperado pelo model Atendente do Django.

        Args:
            properties: Dicionário com propriedades do Notion.

        Returns:
            Dicionário com dados formatados para o model Atendente.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> notion_data = {'properties': {...}}
            >>> atendente_data = AtendenteMapper.from_notion_properties(notion_data['properties'])
            >>> # Retorna dict com dados para o model Django
        """
        try:
            data: Dict[str, Any] = {}

            # Nome (Title)
            if "Nome" in properties and properties["Nome"].get("title"):
                data["nome"] = properties["Nome"]["title"][0]["text"][
                    "content"
                ].strip()

            # Cargo (Rich Text)
            if "Cargo" in properties and properties["Cargo"].get("rich_text"):
                data["cargo"] = properties["Cargo"]["rich_text"][0]["text"][
                    "content"
                ].strip()

            # Email (Email)
            if "Email" in properties and properties["Email"].get("email"):
                data["email"] = properties["Email"]["email"].lower().strip()

            # Telefone (Phone Number)
            if "Telefone" in properties and properties["Telefone"].get(
                "phone_number"
            ):
                data["telefone"] = properties["Telefone"]["phone_number"]

            # Ativo (Checkbox)
            if "Ativo" in properties and isinstance(
                properties["Ativo"].get("checkbox"), bool
            ):
                data["ativo"] = properties["Ativo"]["checkbox"]

            # Disponível (Checkbox)
            if "Disponível" in properties and isinstance(
                properties["Disponível"].get("checkbox"), bool
            ):
                data["disponivel"] = properties["Disponível"]["checkbox"]

            # Capacidade Máxima (Number)
            if (
                "Capacidade Máxima" in properties
                and properties["Capacidade Máxima"].get("number") is not None
            ):
                data["max_atendimentos_simultaneos"] = int(
                    properties["Capacidade Máxima"]["number"]
                )

            # Data de Cadastro (Date)
            if "Data de Cadastro" in properties and properties[
                "Data de Cadastro"
            ].get("date"):
                data["data_cadastro"] = datetime.fromisoformat(
                    properties["Data de Cadastro"]["date"]["start"]
                )

            # Última Atividade (Date)
            if "Última Atividade" in properties and properties[
                "Última Atividade"
            ].get("date"):
                data["ultima_atividade"] = datetime.fromisoformat(
                    properties["Última Atividade"]["date"]["start"]
                )

            # Especialidades (se houver no model, são tratadas como JSON em metadados)
            if hasattr(Atendente, "especialidades"):
                if "Especialidades" in properties and properties[
                    "Especialidades"
                ].get("multi_select"):
                    especialidades = [
                        item["name"]
                        for item in properties["Especialidades"][
                            "multi_select"
                        ]
                    ]
                    data["especialidades"] = especialidades

            # Usuário do Sistema (Rich Text)
            if "Usuário Sistema" in properties and properties[
                "Usuário Sistema"
            ].get("rich_text"):
                data["usuario_sistema"] = properties["Usuário Sistema"][
                    "rich_text"
                ][0]["text"]["content"].strip()

            # Horário de Trabalho (Rich Text)
            if "Horário Trabalho" in properties and properties[
                "Horário Trabalho"
            ].get("rich_text"):
                horario_text = properties["Horário Trabalho"]["rich_text"][0][
                    "text"
                ]["content"]
                try:
                    import json

                    data["horario_trabalho"] = json.loads(horario_text)
                except (json.JSONDecodeError, ValueError):
                    # Se não for JSON válido, ignora
                    pass

            # Metadados (Rich Text)
            if "Metadados" in properties and properties["Metadados"].get(
                "rich_text"
            ):
                metadados_text = properties["Metadados"]["rich_text"][0][
                    "text"
                ]["content"]
                try:
                    import json

                    data["metadados"] = json.loads(metadados_text)
                except (json.JSONDecodeError, ValueError):
                    # Se não for JSON válido, ignora
                    pass

            return data

        except Exception as exc:
            raise MappingError(
                f"Erro ao converter Notion para Atendente: {exc}"
            ) from exc

    @staticmethod
    def _normalize_phone_from_notion(phone: str) -> str:
        """Normaliza telefone vindo do Notion para formato simples."""
        if not phone:
            return ""
        # Remove tudo que não for dígito
        import re

        return re.sub(r"\D", "", phone)

    @staticmethod
    def validate_notion_data(properties: Dict[str, Any]) -> List[str]:
        """
        Valida se os dados do Notion são compatíveis com o model Atendente.

        Args:
            properties: Propriedades do Notion a validar.

        Returns:
            Lista de erros encontrados (vazia se estiver tudo OK).
        """
        errors: List[str] = []

        # Nome é obrigatório
        if "Nome" not in properties or not properties["Nome"].get("title"):
            errors.append("Campo 'Nome' é obrigatório")

        # Validar nome se existe
        if "Nome" in properties and properties["Nome"].get("title"):
            nome = properties["Nome"]["title"][0]["text"]["content"].strip()
            if not nome:
                errors.append("Campo 'Nome' não pode estar vazio")
            elif len(nome) > 100:
                errors.append(
                    "Campo 'Nome' não pode ter mais de 100 caracteres"
                )

        # Validar email se existe
        if "Email" in properties and properties["Email"].get("email"):
            email = properties["Email"]["email"]
            if "@" not in email:
                errors.append("Campo 'Email' deve ser um email válido")

        return errors

    @staticmethod
    def _format_phone(phone: str) -> str:
        """
        Formata telefone para padrão internacional.

        Args:
            phone: Telefone original.

        Returns:
            Telefone formatado.
        """
        # Remove tudo que não é dígito
        digits = re.sub(r"\D", "", phone)

        # Verifica se tem código do Brasil
        if digits.startswith("55") and len(digits) > 11:
            return f"+{digits[:2]} {digits[2:4]} {digits[4:-4]} {digits[-4:]}"
        elif len(digits) == 11:  # Celular com 9
            return f"+55 {digits[0:2]} {digits[2:7]} {digits[7:]}"
        elif len(digits) == 10:  # Fixo
            return f"+55 {digits[0:2]} {digits[2:6]} {digits[6:]}"
        else:
            return phone  # Retorna original se não conseguir formatar

    @staticmethod
    def validate_notion_data(properties: Dict[str, Any]) -> List[str]:
        """
        Valida se os dados do Notion são compatíveis com o model Atendente.

        Args:
            properties: Propriedades do Notion a validar.

        Returns:
            Lista de erros encontrados (vazia se estiver tudo OK).
        """
        errors: List[str] = []

        # Nome é obrigatório
        if "Nome" not in properties or not properties["Nome"].get("title"):
            errors.append("Campo 'Nome' é obrigatório")

        # Validar nome se existe
        if "Nome" in properties and properties["Nome"].get("title"):
            nome = properties["Nome"]["title"][0]["text"]["content"].strip()
            if not nome:
                errors.append("Campo 'Nome' não pode estar vazio")
            elif len(nome) > 100:
                errors.append(
                    "Campo 'Nome' não pode ter mais de 100 caracteres"
                )

        # Validar cargo se existe
        if "Cargo" in properties and properties["Cargo"].get("rich_text"):
            cargo = properties["Cargo"]["rich_text"][0]["text"][
                "content"
            ].strip()
            if len(cargo) > 100:
                errors.append(
                    "Campo 'Cargo' não pode ter mais de 100 caracteres"
                )

        # Validar email se existe
        if "Email" in properties and properties["Email"].get("email"):
            email = properties["Email"]["email"]
            if "@" not in email or "." not in email:
                errors.append("Campo 'Email' deve ser um endereço válido")

        # Validar capacidade máxima se existe
        if (
            "Capacidade Máxima" in properties
            and properties["Capacidade Máxima"].get("number") is not None
        ):
            capacidade = properties["Capacidade Máxima"]["number"]
            if capacidade < 1 or capacidade > 100:
                errors.append(
                    "Campo 'Capacidade Máxima' deve estar entre 1 e 100"
                )

        return errors

    @staticmethod
    def get_notion_schema() -> Dict[str, Any]:
        """
        Retorna o schema esperado para a database de Atendentes no Notion.

        Returns:
            Schema da database no formato da API do Notion.
        """
        return {
            "Nome": {"title": {}},
            "Ativo": {"checkbox": {}},
            "Disponível": {"checkbox": {}},
            "Cargo": {"rich_text": {}},
            "Email": {"email": {}},
            "Telefone": {"phone_number": {}},
            "Capacidade Máxima": {"number": {"format": "number"}},
            "Horário Trabalho": {"rich_text": {}},
            # Campo relation canônico: vínculo com Departamento
            "Departamentos Relacionados": {"relation": {}},
        }
