"""
Mapper para conversão de dados do model Departamento (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model Departamento
do Django para o formato de propriedades da API do Notion e vice-versa,
seguindo o planejamento de integração definido.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ...exceptions import MappingError


class DepartamentoMapper:
    """
    Mapper para conversão de dados entre Departamento (Django) e Notion.

    Esta classe implementa métodos para converter dados do model Departamento
    para o formato esperado pela API do Notion e vice-versa, incluindo
    formatação de status, contadores e especialidades.
    """

    @staticmethod
    def to_notion_properties(departamento_sync: Any) -> Dict[str, Any]:
        """
        Converte um objeto DepartamentoSync do Django para propriedades do Notion.

        Este método utiliza os dados pré-processados do DepartamentoSync para
        gerar as propriedades no formato esperado pela API do Notion.

        Args:
            departamento_sync: Instância do model DepartamentoSync.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> dept_sync = DepartamentoSync.objects.get(id=1)
            >>> properties = DepartamentoMapper.to_notion_properties(dept_sync)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            departamento = departamento_sync.departamento
            properties: Dict[str, Any] = {}

            # Campo obrigatório: Nome (Title)
            properties["Nome"] = {
                "title": [
                    {"text": {"content": departamento.nome or "Sem Nome"}}
                ]
            }

            # Descrição (Rich Text)
            if departamento.descricao:
                properties["Descrição"] = {
                    "rich_text": [
                        {"text": {"content": departamento.descricao.strip()}}
                    ]
                }

            # Ativo (Checkbox)
            properties["Ativo"] = {"checkbox": bool(departamento.ativo)}

            # Data Criação (Date)
            if departamento.data_criacao:
                properties["Data Criação"] = {
                    "date": {"start": departamento.data_criacao.isoformat()}
                }

            # Atendentes Relacionados (Relation)
            # Envia SEMPRE (inclusive vazio) para refletir remoções imediatas
            # e garantir visualização no banco de Departamentos.
            try:
                from django.db.models import Q
                from smart_core_assistant_painel.app.notion_sync.models import (
                    AtendenteSync,
                )

                relacionados = AtendenteSync.objects.filter(
                    Q(departamento_sync=departamento_sync)
                    | Q(atendente__departamento=departamento_sync.departamento)
                )

                external_ids: List[str] = [
                    s.external_id for s in relacionados if s.external_id
                ]

                properties["Atendentes Relacionados"] = {
                    "relation": [{"id": eid} for eid in external_ids]
                }
            except Exception as e:
                # Aviso silencioso: não interrompe a sincronização principal
                print(
                    "Aviso: erro ao montar relação de atendentes do "
                    f"departamento: {e}"
                )

            # Fluxo de Atendimento (Relation inversa 1:N)
            # Envia TODOS os fluxos sincronizados do departamento (ou vazio),
            # espelhando a relação 1:N (Departamento → Fluxos).
            try:
                from django.db.models import Q
                from smart_core_assistant_painel.app.notion_sync.models import (
                    FluxoAtendimentoSync,
                )

                fluxo_syncs = FluxoAtendimentoSync.objects.filter(
                    Q(departamento_sync=departamento_sync)
                    | Q(fluxo__departamento=departamento_sync.departamento)
                )
                fluxo_external_ids: List[str] = [
                    fs.external_id
                    for fs in fluxo_syncs
                    if getattr(fs, "external_id", None)
                ]

                properties["Fluxo de Atendimento"] = {
                    "relation": [{"id": eid} for eid in fluxo_external_ids]
                }
            except Exception as e:
                # Aviso silencioso: não interrompe a sincronização principal
                print(
                    "Aviso: erro ao montar relação de fluxo do "
                    f"departamento: {e}"
                )

            return properties

        except Exception as exc:
            raise MappingError(
                f"Erro ao converter Departamento para Notion: {exc}"
            ) from exc

    @staticmethod
    def from_notion_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para dados do model Departamento.

        Este método converte as propriedades vindas da API do Notion
        para o formato esperado pelo model Departamento do Django.

        Args:
            properties: Dicionário com propriedades do Notion.

        Returns:
            Dicionário com dados formatados para o model Departamento.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> notion_data = {'properties': {...}}
            >>> dept_data = DepartamentoMapper.from_notion_properties(notion_data['properties'])
            >>> # Retorna dict com dados para o model Django
        """
        try:
            data: Dict[str, Any] = {}

            # Nome (Title)
            if "Nome" in properties and properties["Nome"].get("title"):
                data["nome"] = properties["Nome"]["title"][0]["text"][
                    "content"
                ].strip()

            # Descrição (Rich Text)
            if "Descrição" in properties and properties["Descrição"].get(
                "rich_text"
            ):
                data["descricao"] = properties["Descrição"]["rich_text"][0][
                    "text"
                ]["content"].strip()

            # Ativo (Checkbox)
            if "Ativo" in properties and isinstance(
                properties["Ativo"].get("checkbox"), bool
            ):
                data["ativo"] = properties["Ativo"]["checkbox"]

            # Data Criação (Date)
            if "Data Criação" in properties and properties["Data Criação"].get(
                "date"
            ):
                data["data_criacao"] = datetime.fromisoformat(
                    properties["Data Criação"]["date"]["start"]
                )

            # Observações (Rich Text)
            if "Observações" in properties and properties["Observações"].get(
                "rich_text"
            ):
                obs_text = properties["Observações"]["rich_text"][0]["text"][
                    "content"
                ]
                try:
                    import json

                    # Tenta converter para metadados se for JSON
                    data["metadados"] = json.loads(obs_text)
                except (json.JSONDecodeError, ValueError):
                    # Se não for JSON válido, salva como descrição
                    data["descricao"] = obs_text

            return data

        except Exception as exc:
            raise MappingError(
                f"Erro ao converter Notion para Departamento: {exc}"
            ) from exc

    @staticmethod
    def validate_notion_data(properties: Dict[str, Any]) -> List[str]:
        """
        Valida se os dados do Notion são compatíveis com o model Departamento.

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

        return errors

    @staticmethod
    def get_notion_schema() -> Dict[str, Any]:
        """
        Retorna o schema esperado para a database de Departamentos no Notion.

        Returns:
            Schema da database no formato da API do Notion.
        """
        return {
            "Nome": {"title": {}},
            "Descrição": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Criação": {"date": {}},
            "Atendentes Relacionados": {"relation": {}},
            "Fluxo de Atendimento": {"relation": {}},
        }
