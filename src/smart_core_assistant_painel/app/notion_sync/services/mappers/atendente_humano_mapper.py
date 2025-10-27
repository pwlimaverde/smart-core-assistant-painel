"""
Mapper para conversão de dados do model AtendenteHumano (Django ↔ Notion).

Este módulo contém a classe responsável por mapear dados do model AtendenteHumano
do Django para o formato de propriedades da API do Notion e vice-versa,
seguindo o planejamento de integração definido.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...exceptions import MappingError


class AtendenteHumanoMapper:
    """
    Mapper para conversão de dados entre AtendenteHumano (Django) e Notion.

    Esta classe implementa métodos para converter dados do model AtendenteHumano
    para o formato esperado pela API do Notion e vice-versa, incluindo
    formatação de telefones, status, cargos e relacionamentos.
    """

    @staticmethod
    def to_notion_properties(atendente_sync: Any) -> Dict[str, Any]:
        """
        Converte um objeto AtendenteHumanoSync do Django para propriedades do Notion.

        Este método utiliza os dados pré-processados do AtendenteHumanoSync para
        gerar as propriedades no formato esperado pela API do Notion.

        Args:
            atendente_sync: Instância do model AtendenteHumanoSync.

        Returns:
            Dicionário com propriedades formatadas para a API do Notion.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> atendente_sync = AtendenteHumanoSync.objects.get(id=1)
            >>> properties = AtendenteHumanoMapper.to_notion_properties(atendente_sync)
            >>> # Retorna dict com estrutura do Notion
        """
        try:
            atendente = atendente_sync.atendente
            properties: Dict[str, Any] = {}

            # Campo obrigatório: Nome (Title)
            properties['Nome'] = {
                'title': [
                    {'text': {'content': atendente.nome or 'Sem Nome'}}
                ]
            }

            # Cargo (Rich Text)
            if atendente.cargo:
                properties['Cargo'] = {
                    'rich_text': [
                        {'text': {'content': atendente.cargo.strip()}}
                    ]
                }

            # Departamento (Rich Text)
            if atendente.departamento:
                properties['Departamento'] = {
                    'rich_text': [
                        {'text': {'content': atendente.departamento.nome}}
                    ]
                }

            # Email (Email)
            if atendente.email:
                properties['Email'] = {
                    'email': atendente.email.lower().strip()
                }

            # Telefone (Phone Number)
            if atendente.telefone:
                telefone_formatado = AtendenteHumanoMapper._format_phone(atendente.telefone)
                properties['Telefone'] = {
                    'phone_number': telefone_formatado
                }

            # Status (Select)
            status_nome = "Ativo" if atendente.ativo else "Inativo"
            properties['Status'] = {
                'select': {'name': status_nome}
            }

            # Disponibilidade (Select)
            disp_nome = "Disponível" if atendente.disponivel else "Indisponível"
            properties['Disponibilidade'] = {
                'select': {'name': disp_nome}
            }

            # Capacidade Máxima (Number)
            properties['Capacidade Máxima'] = {
                'number': atendente.max_atendimentos_simultaneos
            }

            # Carga Atual (Number) - calculada em tempo real
            carga_atual = atendente.get_atendimentos_ativos()
            properties['Carga Atual'] = {
                'number': carga_atual
            }

            # Percentual de Ocupação (Formula - não suportado diretamente, usamos Number)
            if atendente.max_atendimentos_simultaneos > 0:
                ocupacao_pct = (carga_atual / atendente.max_atendimentos_simultaneos) * 100
                properties['% Ocupação'] = {
                    'number': round(ocupacao_pct, 1)
                }

            # Data de Cadastro (Date)
            if atendente.data_cadastro:
                properties['Data de Cadastro'] = {
                    'date': {
                        'start': atendente.data_cadastro.isoformat()
                    }
                }

            # Última Atividade (Date)
            if atendente.ultima_atividade:
                properties['Última Atividade'] = {
                    'date': {
                        'start': atendente.ultima_atividade.isoformat()
                    }
                }

            # Especialidades (Multi-select)
            especialidades = []
            if atendente.especialidades:
                if isinstance(atendente.especialidades, list):
                    especialidades = [
                        espec.strip().title()
                        for espec in atendente.especialidades
                        if espec.strip()
                    ]
                elif isinstance(atendente.especialidades, str):
                    especialidades = [
                        espec.strip().title()
                        for espec in atendente.especialidades.split(',')
                        if espec.strip()
                    ]

            if especialidades:
                properties['Especialidades'] = {
                    'multi_select': [{'name': espec} for espec in especialidades]
                }

            # Usuário do Sistema (Rich Text)
            if atendente.usuario_sistema:
                properties['Usuário Sistema'] = {
                    'rich_text': [
                        {'text': {'content': atendente.usuario_sistema}}
                    ]
                }

            # Horário de Trabalho (Rich Text - JSON formatado)
            if atendente.horario_trabalho:
                import json
                properties['Horário Trabalho'] = {
                    'rich_text': [
                        {'text': {'content': json.dumps(atendente.horario_trabalho, ensure_ascii=False)}}
                    ]
                }

            # Metadados (Rich Text - JSON formatado)
            if atendente.metadados:
                import json
                properties['Metadados'] = {
                    'rich_text': [
                        {'text': {'content': json.dumps(atendente.metadados, ensure_ascii=False)}}
                    ]
                }

            return properties

        except Exception as exc:
            raise MappingError(f"Erro ao converter AtendenteHumano para Notion: {exc}") from exc

    @staticmethod
    def from_notion_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para dados do model AtendenteHumano.

        Este método converte as propriedades vindas da API do Notion
        para o formato esperado pelo model AtendenteHumano do Django.

        Args:
            properties: Dicionário com propriedades do Notion.

        Returns:
            Dicionário com dados formatados para o model AtendenteHumano.

        Raises:
            MappingError: Se houver erro na conversão dos dados.

        Example:
            >>> notion_data = {'properties': {...}}
            >>> atendente_data = AtendenteHumanoMapper.from_notion_properties(notion_data['properties'])
            >>> # Retorna dict com dados para o model Django
        """
        try:
            data: Dict[str, Any] = {}

            # Nome (Title)
            if 'Nome' in properties and properties['Nome'].get('title'):
                data['nome'] = properties['Nome']['title'][0]['text']['content'].strip()

            # Cargo (Rich Text)
            if 'Cargo' in properties and properties['Cargo'].get('rich_text'):
                data['cargo'] = properties['Cargo']['rich_text'][0]['text']['content'].strip()

            # Email (Email)
            if 'Email' in properties and properties['Email'].get('email'):
                data['email'] = properties['Email']['email'].lower().strip()

            # Telefone (Phone Number)
            if 'Telefone' in properties and properties['Telefone'].get('phone_number'):
                data['telefone'] = properties['Telefone']['phone_number']

            # Status (Select)
            if 'Status' in properties and properties['Status'].get('select'):
                status_nome = properties['Status']['select']['name']
                data['ativo'] = status_nome.lower() == 'ativo'

            # Disponibilidade (Select)
            if 'Disponibilidade' in properties and properties['Disponibilidade'].get('select'):
                disp_nome = properties['Disponibilidade']['select']['name']
                data['disponivel'] = disp_nome.lower() == 'disponível'

            # Capacidade Máxima (Number)
            if 'Capacidade Máxima' in properties and properties['Capacidade Máxima'].get('number') is not None:
                data['max_atendimentos_simultaneos'] = int(properties['Capacidade Máxima']['number'])

            # Data de Cadastro (Date)
            if 'Data de Cadastro' in properties and properties['Data de Cadastro'].get('date'):
                data['data_cadastro'] = datetime.fromisoformat(
                    properties['Data de Cadastro']['date']['start']
                )

            # Última Atividade (Date)
            if 'Última Atividade' in properties and properties['Última Atividade'].get('date'):
                data['ultima_atividade'] = datetime.fromisoformat(
                    properties['Última Atividade']['date']['start']
                )

            # Especialidades (Multi-select)
            if 'Especialidades' in properties and properties['Especialidades'].get('multi_select'):
                especialidades = [
                    item['name'] for item in properties['Especialidades']['multi_select']
                ]
                data['especialidades'] = especialidades

            # Usuário do Sistema (Rich Text)
            if 'Usuário Sistema' in properties and properties['Usuário Sistema'].get('rich_text'):
                data['usuario_sistema'] = properties['Usuário Sistema']['rich_text'][0]['text']['content'].strip()

            # Horário de Trabalho (Rich Text)
            if 'Horário Trabalho' in properties and properties['Horário Trabalho'].get('rich_text'):
                horario_text = properties['Horário Trabalho']['rich_text'][0]['text']['content']
                try:
                    import json
                    data['horario_trabalho'] = json.loads(horario_text)
                except (json.JSONDecodeError, ValueError):
                    # Se não for JSON válido, ignora
                    pass

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
            raise MappingError(f"Erro ao converter Notion para AtendenteHumano: {exc}") from exc

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
        digits = re.sub(r'\D', '', phone)

        # Verifica se tem código do Brasil
        if digits.startswith('55') and len(digits) > 11:
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
        Valida se os dados do Notion são compatíveis com o model AtendenteHumano.

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

        # Validar cargo se existe
        if 'Cargo' in properties and properties['Cargo'].get('rich_text'):
            cargo = properties['Cargo']['rich_text'][0]['text']['content'].strip()
            if len(cargo) > 100:
                errors.append("Campo 'Cargo' não pode ter mais de 100 caracteres")

        # Validar email se existe
        if 'Email' in properties and properties['Email'].get('email'):
            email = properties['Email']['email']
            if '@' not in email or '.' not in email:
                errors.append("Campo 'Email' deve ser um endereço válido")

        # Validar capacidade máxima se existe
        if 'Capacidade Máxima' in properties and properties['Capacidade Máxima'].get('number') is not None:
            capacidade = properties['Capacidade Máxima']['number']
            if capacidade < 1 or capacidade > 100:
                errors.append("Campo 'Capacidade Máxima' deve estar entre 1 e 100")

        # Validar status se existe
        if 'Status' in properties and properties['Status'].get('select'):
            status_nome = properties['Status']['select']['name']
            if status_nome.lower() not in ['ativo', 'inativo']:
                errors.append("Campo 'Status' deve ser 'Ativo' ou 'Inativo'")

        # Validar disponibilidade se existe
        if 'Disponibilidade' in properties and properties['Disponibilidade'].get('select'):
            disp_nome = properties['Disponibilidade']['select']['name']
            if disp_nome.lower() not in ['disponível', 'indisponível']:
                errors.append("Campo 'Disponibilidade' deve ser 'Disponível' ou 'Indisponível'")

        # Validar especialidades se existe
        if 'Especialidades' in properties and properties['Especialidades'].get('multi_select'):
            especialidades = properties['Especialidades']['multi_select']
            if len(especialidades) > 30:
                errors.append("Máximo de 30 especialidades permitidas")

            for espec in especialidades:
                if len(espec.get('name', '')) > 50:
                    errors.append(f"Especialidade '{espec.get('name', '')}' excede 50 caracteres")

        return errors

    @staticmethod
    def get_notion_schema() -> Dict[str, Any]:
        """
        Retorna o schema esperado para a database de Atendentes Humanos no Notion.

        Returns:
            Schema da database no formato da API do Notion.
        """
        return {
            "Nome": {
                "title": {}
            },
            "Cargo": {
                "rich_text": {}
            },
            "Departamento": {
                "rich_text": {}
            },
            "Email": {
                "email": {}
            },
            "Telefone": {
                "phone_number": {}
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Ativo", "color": "green"},
                        {"name": "Inativo", "color": "red"}
                    ]
                }
            },
            "Disponibilidade": {
                "select": {
                    "options": [
                        {"name": "Disponível", "color": "green"},
                        {"name": "Indisponível", "color": "red"}
                    ]
                }
            },
            "Capacidade Máxima": {
                "number": {
                    "format": "number"
                }
            },
            "Carga Atual": {
                "number": {
                    "format": "number"
                }
            },
            "% Ocupação": {
                "number": {
                    "format": "percent"
                }
            },
            "Data de Cadastro": {
                "date": {}
            },
            "Última Atividade": {
                "date": {}
            },
            "Especialidades": {
                "multi_select": {
                    "options": []
                }
            },
            "Usuário Sistema": {
                "rich_text": {}
            },
            "Horário Trabalho": {
                "rich_text": {}
            },
            "Metadados": {
                "rich_text": {}
            }
        }
