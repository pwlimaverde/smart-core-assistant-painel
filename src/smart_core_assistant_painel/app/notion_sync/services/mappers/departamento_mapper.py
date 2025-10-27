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
            properties['Nome'] = {
                'title': [
                    {'text': {'content': departamento.nome or 'Sem Nome'}}
                ]
            }

            # Slug (Rich Text)
            if departamento.slug:
                properties['Slug'] = {
                    'rich_text': [
                        {'text': {'content': departamento.slug}}
                    ]
                }

            # Descrição (Rich Text)
            if departamento.descricao:
                properties['Descrição'] = {
                    'rich_text': [
                        {'text': {'content': departamento.descricao.strip()}}
                    ]
                }

            # Status (Select)
            status_nome = "Ativo" if departamento.ativo else "Inativo"
            properties['Status'] = {
                'select': {'name': status_nome}
            }

            # Data de Criação (Date)
            if departamento.data_criacao:
                properties['Data de Criação'] = {
                    'date': {
                        'start': departamento.data_criacao.isoformat()
                    }
                }

            # Contador de Atendentes (Number)
            count_atendentes = departamento.atendentes.filter(ativo=True).count()
            properties['Qtd. Atendentes'] = {
                'number': count_atendentes
            }

            # Contador de Atendentes Totais (Number)
            count_total = departamento.atendentes.count()
            properties['Qtd. Atendentes Total'] = {
                'number': count_total
            }

            # Especialidades (Multi-select)
            especialidades = []
            if departamento.configuracoes and 'especialidades' in departamento.configuracoes:
                especs = departamento.configuracoes['especialidades']
                if isinstance(especs, list):
                    especialidades = [espec.strip().title() for espec in especs if espec.strip()]
                elif isinstance(especs, str):
                    especialidades = [espec.strip().title() for espec in especs.split(',') if espec.strip()]

            if especialidades:
                properties['Especialidades'] = {
                    'multi_select': [{'name': espec} for espec in especialidades]
                }

            # Metadados adicionais
            if departamento.metadados:
                # Converte metadados para JSON string
                import json
                properties['Metadados'] = {
                    'rich_text': [
                        {'text': {'content': json.dumps(departamento.metadados, ensure_ascii=False)}}
                    ]
                }

            return properties

        except Exception as exc:
            raise MappingError(f"Erro ao converter Departamento para Notion: {exc}") from exc

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
            if 'Nome' in properties and properties['Nome'].get('title'):
                data['nome'] = properties['Nome']['title'][0]['text']['content'].strip()

            # Slug (Rich Text)
            if 'Slug' in properties and properties['Slug'].get('rich_text'):
                data['slug'] = properties['Slug']['rich_text'][0]['text']['content'].strip()

            # Descrição (Rich Text)
            if 'Descrição' in properties and properties['Descrição'].get('rich_text'):
                data['descricao'] = properties['Descrição']['rich_text'][0]['text']['content'].strip()

            # Status (Select)
            if 'Status' in properties and properties['Status'].get('select'):
                status_nome = properties['Status']['select']['name']
                data['ativo'] = status_nome.lower() == 'ativo'

            # Data de Criação (Date)
            if 'Data de Criação' in properties and properties['Data de Criação'].get('date'):
                data['data_criacao'] = datetime.fromisoformat(
                    properties['Data de Criação']['date']['start']
                )

            # Especialidades (Multi-select)
            if 'Especialidades' in properties and properties['Especialidades'].get('multi_select'):
                especialidades = [
                    item['name'] for item in properties['Especialidades']['multi_select']
                ]
                # Salva nas configurações
                if 'configuracoes' not in data:
                    data['configuracoes'] = {}
                data['configuracoes']['especialidades'] = especialidades

            # Metadados (Rich Text)
            if 'Metadados' in properties and properties['Metadados'].get('rich_text'):
                metadados_text = properties['Metadados']['rich_text'][0]['text']['content']
                try:
                    import json
                    data['metadados'] = json.loads(metadados_text)
                except (json.JSONDecodeError, ValueError):
                    # Se não for JSON válido, ignora
                    pass

            return data

        except Exception as exc:
            raise MappingError(f"Erro ao converter Notion para Departamento: {exc}") from exc

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
        if 'Nome' not in properties or not properties['Nome'].get('title'):
            errors.append("Campo 'Nome' é obrigatório")

        # Validar nome se existe
        if 'Nome' in properties and properties['Nome'].get('title'):
            nome = properties['Nome']['title'][0]['text']['content'].strip()
            if not nome:
                errors.append("Campo 'Nome' não pode estar vazio")
            elif len(nome) > 100:
                errors.append("Campo 'Nome' não pode ter mais de 100 caracteres")

        # Validar status se existe
        if 'Status' in properties and properties['Status'].get('select'):
            status_nome = properties['Status']['select']['name']
            if status_nome.lower() not in ['ativo', 'inativo']:
                errors.append("Campo 'Status' deve ser 'Ativo' ou 'Inativo'")

        # Validar especialidades se existe
        if 'Especialidades' in properties and properties['Especialidades'].get('multi_select'):
            especialidades = properties['Especialidades']['multi_select']
            if len(especialidades) > 20:
                errors.append("Máximo de 20 especialidades permitidas")

            for espec in especialidades:
                if len(espec.get('name', '')) > 50:
                    errors.append(f"Especialidade '{espec.get('name', '')}' excede 50 caracteres")

        return errors

    @staticmethod
    def get_notion_schema() -> Dict[str, Any]:
        """
        Retorna o schema esperado para a database de Departamentos no Notion.

        Returns:
            Schema da database no formato da API do Notion.
        """
        return {
            "Nome": {
                "title": {}
            },
            "Slug": {
                "rich_text": {}
            },
            "Descrição": {
                "rich_text": {}
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Ativo", "color": "green"},
                        {"name": "Inativo", "color": "red"}
                    ]
                }
            },
            "Data de Criação": {
                "date": {}
            },
            "Qtd. Atendentes": {
                "number": {
                    "format": "number"
                }
            },
            "Qtd. Atendentes Total": {
                "number": {
                    "format": "number"
                }
            },
            "Especialidades": {
                "multi_select": {
                    "options": []
                }
            },
            "Metadados": {
                "rich_text": {}
            }
        }
