# Exemplos Práticos de Implementação de Fluxos

Este documento contém exemplos práticos para implementar e configurar os fluxos personalizados de atendimento.

## 1. Criação de Fluxos Exemplo

### 1.1. Fluxo Comercial

```python
def criar_fluxo_comercial(departamento: Departamento) -> FluxoAtendimento:
    """Cria o fluxo personalizado para o departamento comercial."""
    
    fluxo = FluxoAtendimento.objects.create(
        departamento=departamento,
        nome="Fluxo Comercial Padrão",
        descricao="Fluxo completo desde a solicitação até o fechamento da venda"
    )
    
    # Etapas do fluxo comercial
    etapas = [
        {
            "nome": "📥 Solicitação de Orçamento",
            "descricao": "Novas solicitações de orçamento recebidas",
            "ordem": 1,
            "cor": "#3B82F6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "automatico": False,
            "campos_obrigatorios": ["assunto", "valor_estimado"]
        },
        {
            "nome": "📞 Em Contato",
            "descricao": "Cliente está sendo contatado pela equipe",
            "ordem": 2,
            "cor": "#10B981",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False
        },
        {
            "nome": "💳 Aguardando Pagamento",
            "descricao": "Proposta enviada, aguardando pagamento do cliente",
            "ordem": 3,
            "cor": "#F59E0B",
            "tipo_etapa": TipoEtapa.ESPERA,
            "permite_atribuicao": False,
            "automatico": True,
            "regras_transicao": {
                "tempo_maximo_espera": 72,  # horas
                "notificar_atendente": True,
                "acao_expiracao": "retorno_para_contato"
            }
        },
        {
            "nome": "📋 Pedido Confirmado",
            "descricao": "Pagamento confirmado, pedido em processamento",
            "ordem": 4,
            "cor": "#8B5CF6",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "automatico": False
        },
        {
            "nome": "✅ Concluído",
            "descricao": "Venda finalizada com sucesso",
            "ordem": 5,
            "cor": "#059669",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False
        },
        {
            "nome": "❌ Perdido",
            "descricao": "Venda não concluída",
            "ordem": 6,
            "cor": "#EF4444",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "automatico": False,
            "campos_obrigatorios": ["motivo_perda"]
        }
    ]
    
    for etapa_data in etapas:
        EtapaFluxo.objects.create(fluxo=fluxo, **etapa_data)
    
    return fluxo
```

### 1.2. Fluxo Financeiro

```python
def criar_fluxo_financeiro(departamento: Departamento) -> FluxoAtendimento:
    """Cria o fluxo personalizado para o departamento financeiro."""
    
    fluxo = FluxoAtendimento.objects.create(
        departamento=departamento,
        nome="Fluxo Financeiro Padrão",
        descricao="Fluxo para análise e processamento financeiro"
    )
    
    etapas = [
        {
            "nome": "📝 Nova Solicitação",
            "descricao": "Novas solicitações financeiras recebidas",
            "ordem": 1,
            "cor": "#3B82F6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True
        },
        {
            "nome": "🔍 Análise de Crédito",
            "descricao": "Análise do perfil de crédito do cliente",
            "ordem": 2,
            "cor": "#6366F1",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True,
            "campos_obrigatorios": ["documento_cliente", "renda_comprovada"]
        },
        {
            "nome": "📧 Aguardando Documentos",
            "descricao": "Aguardando envio de documentos pelo cliente",
            "ordem": 3,
            "cor": "#F59E0B",
            "tipo_etapa": TipoEtapa.ESPERA,
            "permite_atribuicao": False,
            "automatico": True,
            "regras_transicao": {
                "lembrar_cliente": True,
                "intervalo_lembrete": 24,  # horas
                "maximo_lembretes": 3
            }
        },
        {
            "nome": "⚡ Processando Pagamento",
            "descricao": "Pagamento sendo processado",
            "ordem": 4,
            "cor": "#EC4899",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True
        },
        {
            "nome": "✅ Pagamento Confirmado",
            "descricao": "Pagamento processado com sucesso",
            "ordem": 5,
            "cor": "#059669",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False
        }
    ]
    
    for etapa_data in etapas:
        EtapaFluxo.objects.create(fluxo=fluxo, **etapa_data)
    
    return fluxo
```

### 1.3. Fluxo Suporte Técnico

```python
def criar_fluxo_suporte(departamento: Departamento) -> FluxoAtendimento:
    """Cria o fluxo personalizado para o departamento de suporte técnico."""
    
    fluxo = FluxoAtendimento.objects.create(
        departamento=departamento,
        nome="Fluxo Suporte Técnico",
        descricao="Fluxo para atendimento de suporte técnico em níveis"
    )
    
    etapas = [
        {
            "nome": "🆕 Novo Chamado",
            "descricao": "Novos chamados técnicos recebidos",
            "ordem": 1,
            "cor": "#3B82F6",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "campos_obrigatorios": ["categoria_problema", "gravidade"]
        },
        {
            "nome": "🔬 Diagnóstico",
            "descricao": "Análise inicial do problema",
            "ordem": 2,
            "cor": "#6366F1",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True
        },
        {
            "nome": "🛠️ Em Reparo",
            "descricao": "Solução do problema em andamento",
            "ordem": 3,
            "cor": "#10B981",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True
        },
        {
            "nome": "⏳ Aguardando Peças",
            "descricao": "Aguardando peças ou componentes",
            "ordem": 4,
            "cor": "#F59E0B",
            "tipo_etapa": TipoEtapa.ESPERA,
            "permite_atribuicao": False,
            "automatico": True,
            "regras_transicao": {
                "notificar_compras": True,
                "tempo_maximo_espera": 168  # 1 semana
            }
        },
        {
            "nome": "🧪 Testes",
            "descricao": "Testando a solução aplicada",
            "ordem": 5,
            "cor": "#8B5CF6",
            "tipo_etapa": TipoEtapa.TRABALHO,
            "permite_atribuicao": True
        },
        {
            "nome": "✅ Resolvido",
            "descricao": "Problema resolvido com sucesso",
            "ordem": 6,
            "cor": "#059669",
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "permite_atribuicao": False,
            "campos_obrigatorios": ["resumo_solucao", "satisfacao_cliente"]
        },
        {
            "nome": "🔄 Escalado N2",
            "descricao": "Chamado escalado para nível 2",
            "ordem": 7,
            "cor": "#EF4444",
            "tipo_etapa": TipoEtapa.FILA,
            "permite_atribuicao": True,
            "regras_transicao": {
                "notificar_gestor": True,
                "prioridade_automatica": "alta"
            }
        }
    ]
    
    for etapa_data in etapas:
        EtapaFluxo.objects.create(fluxo=fluxo, **etapa_data)
    
    return fluxo
```

## 2. Serviços de Exemplo

### 2.1. Serviço de Movimentação

```python
from typing import Tuple, List, Optional
from django.db import transaction
from django.utils import timezone

class FluxoAtendimentoService:
    """Serviço responsável por gerenciar operações com fluxos de atendimento."""
    
    @staticmethod
    @transaction.atomic
    def mover_atendimento(
        atendimento: "Atendimento",
        etapa_destino: "EtapaFluxo",
        atendente: Optional["Atendente"] = None,
        motivo: Optional[str] = None,
        automatico: bool = False
    ) -> "MovimentoFluxo":
        """
        Move um atendimento para uma nova etapa do fluxo.
        
        Args:
            atendimento: Atendimento a ser movido
            etapa_destino: Nova etapa do fluxo
            atendente: Atendente responsável pelo movimento
            motivo: Motivo da movimentação
            automatico: Se o movimento é automático
            
        Returns:
            MovimentoFluxo criado
            
        Raises:
            ValidationError: Se a movimentação não for permitida
        """
        # Validar se a movimentação é permitida
        valido, erros = FluxoAtendimentoService.validar_movimentacao(
            atendimento, etapa_destino, atendente
        )
        
        if not valido:
            raise ValidationError(f"Movimentação não permitida: {'; '.join(erros)}")
        
        # Buscar etapa atual
        etapa_atual = None
        if atendimento.etapa_atual:
            etapa_atual = atendimento.etapa_atual
        elif atendimento.movimentos_fluxo.exists():
            etapa_atual = atendimento.movimentos_fluxo.first().etapa_destino
        
        # Verificar se precisa atribuir atendente
        atendente_destino = atendente
        if etapa_destino.permite_atribuicao and not atendente_destino:
            # Se não tem atendente e etapa permite, manter o atual ou None
            atendente_destino = atendimento.atendente_humano
        
        # Criar movimento
        movimento = MovimentoFluxo.criar_movimento(
            atendimento=atendimento,
            etapa_destino=etapa_destino,
            atendente_destino=atendente_destino,
            motivo=motivo,
            automatico=automatico,
            atendente_origem=atendente,
            etapa_origem=etapa_atual
        )
        
        # Atualizar timestamp da última mensagem se for movimento interativo
        if not automatico:
            atendimento.data_ultima_mensagem = timezone.now()
            atendimento.save(update_fields=["data_ultima_mensagem"])
        
        # Disparar pós-movimentação
        from .signals import processar_pos_movimentacao
        processar_pos_movimentacao.send(sender=MovimentoFluxo, movimento=movimento)
        
        return movimento
    
    @staticmethod
    def validar_movimentacao(
        atendimento: "Atendimento",
        etapa_destino: "EtapaFluxo",
        atendente: Optional["Atendente"] = None
    ) -> Tuple[bool, List[str]]:
        """
        Valida se um atendimento pode ser movido para uma etapa.
        
        Returns:
            Tuple[bool, List[str]]: (pode_mover, lista_de_erros)
        """
        erros = []
        
        # Verificar se atendimento está em fluxo válido
        if not atendimento.departamento:
            erros.append("Atendimento não está associado a um departamento")
        
        # Verificar se etapa pertence ao mesmo fluxo do atendimento
        if atendimento.etapa_atual and atendimento.etapa_atual.fluxo != etapa_destino.fluxo:
            erros.append("Etapa de destino pertence a fluxo diferente do atendimento")
        
        # Verificar se etapa está ativa
        if not etapa_destino.ativo:
            erros.append("Etapa de destino está inativa")
        
        # Verificar permissões do atendente
        if atendente:
            # Verificar se atendente pertence ao mesmo departamento
            if atendente.departamento != atendimento.departamento:
                erros.append("Atendente não pertence ao mesmo departamento do atendimento")
            
            # Verificar se atendente pode mover para esta etapa
            if etapa_destino.tipo_etapa == TipoEtapa.FILA:
                # Apenas gestores podem mover para fila
                if not atendente.eh_gestor:
                    erros.append("Apenas gestores podem mover atendimentos para fila")
        
        # Verificar campos obrigatórios
        if etapa_destino.campos_obrigatorios:
            for campo in etapa_destino.campos_obrigatorios:
                if not hasattr(atendimento, campo) or not getattr(atendimento, campo):
                    erros.append(f"Campo obrigatório ausente: {campo}")
        
        # Verificar regras específicas da etapa
        if etapa_destino.regras_transicao:
            # Implementar validações específicas baseadas nas regras
            pass
        
        return len(erros) == 0, erros
    
    @staticmethod
    def atribuir_atendimento(
        atendimento: "Atendimento",
        atendente: "Atendente",
        motivo: Optional[str] = None
    ) -> "MovimentoFluxo":
        """
        Atribui um atendimento a um atendente específico.
        
        Args:
            atendimento: Atendimento a ser atribuído
            atendente: Atendente que receberá a atribuição
            motivo: Motivo da atribuição
            
        Returns:
            MovimentoFluxo da atribuição
        """
        # Se atendimento não tem etapa atual, buscar primeira etapa de trabalho
        if not atendimento.etapa_atual:
            fluxo = atendimento.departamento.fluxo_atendimento
            etapa_trabalho = fluxo.get_etapas_por_tipo(TipoEtapa.TRABALHO).first()
            
            if not etapa_trabalho:
                raise ValueError("Fluxo não possui etapas de trabalho configuradas")
            
            return FluxoAtendimentoService.mover_atendimento(
                atendimento=atendimento,
                etapa_destino=etapa_trabalho,
                atendente=atendente,
                motivo=motivo or f"Atribuído manualmente para {atendente.nome}",
                automatico=False
            )
        else:
            # Já está em uma etapa, apenas atualizar o atendente
            movimento = MovimentoFluxo.criar_movimento(
                atendimento=atendimento,
                etapa_destino=atendimento.etapa_atual,
                atendente_destino=atendente,
                motivo=motivo or f"Reatribuído para {atendente.nome}",
                automatico=False
            )
            
            return movimento
```

### 2.2. Serviço do Kanban

```python
from django.db.models import Q, Count
from django.core.serializers.json import DjangoJSONEncoder
import json

class KanbanService:
    """Serviço para alimentar o frontend do painel Kanban."""
    
    @staticmethod
    def get_dados_kanban(
        departamento: "Departamento",
        atendente: Optional["Atendente"] = None,
        filtros: Optional[dict] = None
    ) -> dict:
        """
        Retorna dados estruturados para o painel Kanban.
        
        Args:
            departamento: Departamento para filtrar
            atendente: Atendente específico (opcional)
            filtros: Filtros adicionais (opcional)
            
        Returns:
            dict com dados estruturados do kanban
        """
        fluxo = departamento.fluxo_atendimento
        if not fluxo:
            return {"error": "Departamento não possui fluxo configurado"}
        
        # Obter todas as etapas do fluxo em ordem
        etapas = fluxo.etapas.filter(ativo=True).order_by("ordem")
        
        # Construir dados do kanban
        dados_kanban = {
            "fluxo": {
                "id": fluxo.id,
                "nome": fluxo.nome,
                "departamento": departamento.nome
            },
            "etapas": [],
            "resumo": {
                "total_atendimentos": 0,
                "por_etapa": {},
                "por_atendente": {},
                "prioridades": {}
            }
        }
        
        total_atendimentos = 0
        
        for etapa in etapas:
            # Obter atendimentos nesta etapa
            atendimentos_etapa = KanbanService.get_atendimentos_por_etapa(
                etapa=etapa,
                atendente=atendente,
                filtros=filtros
            )
            
            # Serializar atendimentos
            atendimentos_serializados = []
            for atendimento in atendimentos_etapa:
                dados_atendimento = {
                    "id": atendimento.id,
                    "contato": {
                        "nome": atendimento.contato.nome,
                        "telefone": atendimento.contato.telefone
                    },
                    "assunto": atendimento.assunto,
                    "prioridade": atendimento.prioridade,
                    "data_inicio": atendimento.data_inicio.isoformat(),
                    "data_ultima_mensagem": (
                        atendimento.data_ultima_mensagem.isoformat()
                        if atendimento.data_ultima_mensagem else None
                    ),
                    "atendente": (
                        {
                            "id": atendimento.atendente_humano.id,
                            "nome": atendimento.atendente_humano.nome
                        }
                        if atendimento.atendente_humano else None
                    ),
                    "tags": atendimento.tags,
                    "tempo_etapa": KanbanService.calcular_tempo_etapa(atendimento),
                    "tempo_total": KanbanService.calcular_tempo_total(atendimento)
                }
                atendimentos_serializados.append(dados_atendimento)
            
            # Adicionar etapa aos dados do kanban
            dados_etapa = {
                "id": etapa.id,
                "nome": etapa.nome,
                "descricao": etapa.descricao,
                "cor": etapa.cor,
                "tipo": etapa.tipo_etapa,
                "permite_atribuicao": etapa.permite_atribuicao,
                "atendimentos": atendimentos_serializados,
                "total": len(atendimentos_serializados)
            }
            
            dados_kanban["etapas"].append(dados_etapa)
            
            # Atualizar resumo
            total_atendimentos += len(atendimentos_serializados)
            dados_kanban["resumo"]["por_etapa"][etapa.id] = len(atendimentos_serializados)
            
            # Contar por atendente
            for atendimento in atendimentos_etapa:
                if atendimento.atendente_humano:
                    atendente_id = atendimento.atendente_humano.id
                    if atendente_id not in dados_kanban["resumo"]["por_atendente"]:
                        dados_kanban["resumo"]["por_atendente"][atendente_id] = 0
                    dados_kanban["resumo"]["por_atendente"][atendente_id] += 1
                
                # Contar prioridades
                prioridade = atendimento.prioridade
                if prioridade not in dados_kanban["resumo"]["prioridades"]:
                    dados_kanban["resumo"]["prioridades"][prioridade] = 0
                dados_kanban["resumo"]["prioridades"][prioridade] += 1
        
        dados_kanban["resumo"]["total_atendimentos"] = total_atendimentos
        
        return dados_kanban
    
    @staticmethod
    def get_atendimentos_por_etapa(
        etapa: "EtapaFluxo",
        atendente: Optional["Atendente"] = None,
        filtros: Optional[dict] = None
    ):
        """
        Retorna atendimentos em uma etapa específica.
        
        Args:
            etapa: Etapa do fluxo
            atendente: Atendente específico (opcional)
            filtros: Filtros adicionais (opcional)
            
        Returns:
            QuerySet de atendimentos
        """
        queryset = etapa.atendimentos.select_related(
            'contato',
            'atendente_humano',
            'departamento'
        ).order_by('-data_ultima_mensagem', '-data_inicio')
        
        # Aplicar filtro por atendente
        if atendente:
            # Se a etapa permite atribuição, mostrar apenas do atendente
            if etapa.permite_atribuicao:
                queryset = queryset.filter(atendente_humano=atendente)
            # Se é fila, mostrar todos que atendente pode pegar
            elif etapa.tipo_etapa == TipoEtapa.FILA:
                # Mostrar todos na fila (atendente pode assumir)
                pass
            # Outros tipos, mostrar apenas se for responsável
            else:
                queryset = queryset.filter(atendente_humano=atendente)
        
        # Aplicar filtros adicionais
        if filtros:
            # Filtro por prioridade
            if 'prioridade' in filtros:
                queryset = queryset.filter(prioridade=filtros['prioridade'])
            
            # Filtro por tags
            if 'tags' in filtros:
                for tag in filtros['tags']:
                    queryset = queryset.filter(tags__contains=[tag])
            
            # Filtro por data
            if 'data_inicio' in filtros:
                queryset = queryset.filter(
                    data_inicio__date=filtros['data_inicio']
                )
            
            # Busca por texto
            if 'busca' in filtros:
                termo = filtros['busca']
                queryset = queryset.filter(
                    Q(assunto__icontains=termo) |
                    Q(contato__nome__icontains=termo) |
                    Q(contato__telefone__icontains=termo)
                )
        
        return queryset
    
    @staticmethod
    def calcular_tempo_etapa(atendimento: "Atendimento") -> dict:
        """
        Calcula quanto tempo o atendimento está na etapa atual.
        
        Returns:
            dict com tempo em diferentes formatos
        """
        if not atendimento.etapa_atual:
            return {"horas": 0, "dias": 0, "formatado": "-"}
        
        # Buscar movimento mais recente
        movimento_recente = atendimento.movimentos_fluxo.filter(
            etapa_destino=atendimento.etapa_atual
        ).first()
        
        if not movimento_recente:
            return {"horas": 0, "dias": 0, "formatado": "-"}
        
        agora = timezone.now()
        delta = agora - movimento_recente.data_movimento
        
        horas = delta.total_seconds() / 3600
        dias = horas / 24
        
        # Formatação amigável
        if dias >= 1:
            formatado = f"{int(dias)}d {int(horas % 24)}h"
        elif horas >= 1:
            formatado = f"{int(horas)}h {int((horas % 1) * 60)}m"
        else:
            formatado = f"{int(delta.total_seconds() / 60)}m"
        
        return {
            "horas": round(horas, 2),
            "dias": round(dias, 2),
            "formatado": formatado,
            "total_segundos": delta.total_seconds()
        }
    
    @staticmethod
    def calcular_tempo_total(atendimento: "Atendimento") -> dict:
        """
        Calcula o tempo total desde o início do atendimento.
        
        Returns:
            dict com tempo em diferentes formatos
        """
        agora = timezone.now()
        delta = agora - atendimento.data_inicio
        
        horas = delta.total_seconds() / 3600
        dias = horas / 24
        
        # Formatação amigável
        if dias >= 1:
            formatado = f"{int(dias)}d {int(horas % 24)}h"
        elif horas >= 1:
            formatado = f"{int(horas)}h {int((horas % 1) * 60)}m"
        else:
            formatado = f"{int(delta.total_seconds() / 60)}m"
        
        return {
            "horas": round(horas, 2),
            "dias": round(dias, 2),
            "formatado": formatado,
            "total_segundos": delta.total_seconds()
        }
```

## 3. Exemplos de API

### 3.1. Views do Django

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class KanbanView(APIView):
    """API para fornecer dados do painel Kanban."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, departamento_id):
        """Retorna dados estruturados para o Kanban."""
        try:
            departamento = Departamento.objects.get(id=departamento_id)
            
            # Verificar se usuário tem permissão
            if not request.user.has_perm('operacional.view_departamento', departamento):
                return Response(
                    {"error": "Sem permissão para acessar este departamento"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obter atendente logado
            atendente = getattr(request.user, 'atendente', None)
            
            # Obter filtros da querystring
            filtros = {
                'prioridade': request.GET.get('prioridade'),
                'busca': request.GET.get('busca'),
                'tags': request.GET.getlist('tags'),
            }
            # Remover valores nulos/vazios
            filtros = {k: v for k, v in filtros.items() if v}
            
            dados = KanbanService.get_dados_kanban(
                departamento=departamento,
                atendente=atendente,
                filtros=filtros
            )
            
            return Response(dados)
            
        except Departamento.DoesNotExist:
            return Response(
                {"error": "Departamento não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MoverAtendimentoView(APIView):
    """API para mover atendimentos entre etapas."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, atendimento_id):
        """Move um atendimento para uma nova etapa."""
        try:
            atendimento = Atendimento.objects.get(id=atendimento_id)
            
            # Obter dados da requisição
            etapa_destino_id = request.data.get('etapa_destino_id')
            motivo = request.data.get('motivo', '')
            
            if not etapa_destino_id:
                return Response(
                    {"error": "etapa_destino_id é obrigatório"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            etapa_destino = EtapaFluxo.objects.get(id=etapa_destino_id)
            
            # Obter atendente logado
            atendente = getattr(request.user, 'atendente', None)
            
            # Mover atendimento
            movimento = FluxoAtendimentoService.mover_atendimento(
                atendimento=atendimento,
                etapa_destino=etapa_destino,
                atendente=atendente,
                motivo=motivo,
                automatico=False
            )
            
            return Response({
                "success": True,
                "movimento": {
                    "id": movimento.id,
                    "etapa_origem": movimento.etapa_origem.nome if movimento.etapa_origem else None,
                    "etapa_destino": movimento.etapa_destino.nome,
                    "data_movimento": movimento.data_movimento.isoformat()
                }
            })
            
        except Atendimento.DoesNotExist:
            return Response(
                {"error": "Atendimento não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except EtapaFluxo.DoesNotExist:
            return Response(
                {"error": "Etapa não encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AtribuirAtendimentoView(APIView):
    """API para atribuir atendimentos a atendentes."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, atendimento_id):
        """Atribui um atendimento a um atendente."""
        try:
            atendimento = Atendimento.objects.get(id=atendimento_id)
            
            # Obter atendente que está fazendo a atribuição
            atendente_origem = getattr(request.user, 'atendente', None)
            
            # Obter atendente de destino
            atendente_destino_id = request.data.get('atendente_destino_id')
            motivo = request.data.get('motivo', '')
            
            if not atendente_destino_id:
                return Response(
                    {"error": "atendente_destino_id é obrigatório"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            atendente_destino = Atendente.objects.get(id=atendente_destino_id)
            
            # Atribuir atendimento
            movimento = FluxoAtendimentoService.atribuir_atendimento(
                atendimento=atendimento,
                atendente=atendente_destino,
                motivo=motivo
            )
            
            return Response({
                "success": True,
                "movimento": {
                    "id": movimento.id,
                    "atendente_destino": {
                        "id": atendente_destino.id,
                        "nome": atendente_destino.nome
                    },
                    "data_movimento": movimento.data_movimento.isoformat()
                }
            })
            
        except Atendimento.DoesNotExist:
            return Response(
                {"error": "Atendimento não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Atendente.DoesNotExist:
            return Response(
                {"error": "Atendente não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

## 4. Exemplo de Migration

```python
# Generated migration file: 0002_add_fluxos_personalizados.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ui_atendimentos', '0001_initial'),
        ('ui_operacional', '0001_initial'),
    ]

    operations = [
        # Criar novos modelos
        migrations.CreateModel(
            name='FluxoAtendimento',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(help_text='Nome descritivo do fluxo', max_length=100)),
                ('descricao', models.TextField(blank=True, help_text='Descrição detalhada do fluxo de trabalho', null=True)),
                ('ativo', models.BooleanField(default=True, help_text='Indica se o fluxo está ativo')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, help_text='Data de criação do fluxo')),
                ('data_atualizacao', models.DateTimeField(auto_now=True, help_text='Data da última atualização do fluxo')),
                ('departamento', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fluxo_atendimento', to='ui_operacional.departamento', help_text='Departamento ao qual este fluxo pertence')),
            ],
            options={
                'verbose_name': 'Fluxo de Atendimento',
                'verbose_name_plural': 'Fluxos de Atendimento',
                'db_table': 'oraculo_fluxo_atendimento',
                'ordering': ['departamento__nome'],
            },
        ),
        
        migrations.CreateModel(
            name='EtapaFluxo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nome', models.CharField(help_text='Nome da etapa (ex: \'Solicitação de Orçamento\')', max_length=50)),
                ('descricao', models.CharField(blank=True, help_text='Descrição opcional da etapa', max_length=200, null=True)),
                ('ordem', models.PositiveIntegerField(help_text='Ordem da etapa no fluxo (menor número primeiro)')),
                ('cor', models.CharField(default='#6B7280', help_text='Cor hexadecimal para identificação visual (ex: #FF5733)', max_length=7)),
                ('tipo_etapa', models.CharField(choices=[('fila', 'Fila de Entrada'), ('trabalho', 'Em Trabalho'), ('espera', 'Aguardando Resposta'), ('finalizacao', 'Finalização')], default='trabalho', help_text='Tipo da etapa para regras de negócio', max_length=20)),
                ('permite_atribuicao', models.BooleanField(default=True, help_text='Indica se atendentes podem ser atribuídos nesta etapa')),
                ('automatico', models.BooleanField(default=False, help_text='Indica se o movimento para esta etapa é automático')),
                ('regras_transicao', models.JSONField(blank=True, default=dict, help_text='Regras específicas para transição para esta etapa')),
                ('campos_obrigatorios', models.JSONField(blank=True, default=list, help_text='Lista de campos obrigatórios para entrar nesta etapa')),
                ('ativo', models.BooleanField(default=True, help_text='Indica se a etapa está ativa no fluxo')),
                ('data_criacao', models.DateTimeField(auto_now_add=True, help_text='Data de criação da etapa')),
                ('fluxo', models.ForeignKey(help_text='Fluxo ao qual esta etapa pertence', on_delete=django.db.models.deletion.CASCADE, related_name='etapas', to='ui_operacional.fluxoatendimento')),
            ],
            options={
                'verbose_name': 'Etapa do Fluxo',
                'verbose_name_plural': 'Etapas do Fluxo',
                'db_table': 'oraculo_etapa_fluxo',
                'ordering': ['fluxo', 'ordem'],
                'indexes': [
                    models.Index(fields=['fluxo', 'ordem'], name='oraculo_e_flu_fluxo_id_ord_idx'),
                    models.Index(fields=['tipo_etapa'], name='oraculo_e_tip_tipo_etap_idx'),
                    models.Index(fields=['ativo'], name='oraculo_e_ati_idx'),
                ],
            },
        ),
        
        migrations.CreateModel(
            name='MovimentoFluxo',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('motivo', models.TextField(blank=True, help_text='Motivo da movimentação (opcional)', null=True)),
                ('dados_complementares', models.JSONField(blank=True, default=dict, help_text='Dados complementares sobre a movimentação')),
                ('automatico', models.BooleanField(default=False, help_text='Indica se o movimento foi automático')),
                ('data_movimento', models.DateTimeField(auto_now_add=True, help_text='Data e hora da movimentação')),
                ('atendimento', models.ForeignKey(help_text='Atendimento que foi movido', on_delete=django.db.models.deletion.CASCADE, related_name='movimentos_fluxo', to='ui_atendimentos.atendimento')),
                ('atendente_destino', models.ForeignKey(blank=True, help_text='Atendente que foi atribuído ao atendimento (se aplicável)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos_destino', to='ui_operacional.atendente')),
                ('atendente_origem', models.ForeignKey(blank=True, help_text='Atendente que realizou o movimento (se aplicável)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos_origem', to='ui_operacional.atendente')),
                ('etapa_destino', models.ForeignKey(help_text='Etapa para a qual o atendimento foi movido', on_delete=django.db.models.deletion.CASCADE, related_name='movimentos_entrada', to='ui_operacional.etapafluxo')),
                ('etapa_origem', models.ForeignKey(blank=True, help_text='Etapa de origem (None para novos atendimentos)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos_saida', to='ui_operacional.etapafluxo')),
            ],
            options={
                'verbose_name': 'Movimento do Fluxo',
                'verbose_name_plural': 'Movimentos do Fluxo',
                'db_table': 'oraculo_movimento_fluxo',
                'ordering': ['-data_movimento'],
                'indexes': [
                    models.Index(fields=['atendimento', '-data_movimento'], name='oraculo_m_aten_data_idx'),
                    models.Index(fields=['etapa_destino', '-data_movimento'], name='oraculo_m_etap_data_idx'),
                    models.Index(fields=['data_movimento'], name='oraculo_m_data_idx'),
                ],
            },
        ),
        
        # Adicionar campo etapa_atual ao Atendimento
        migrations.AddField(
            model_name='atendimento',
            name='etapa_atual',
            field=models.ForeignKey(blank=True, help_text='Etapa atual do atendimento no fluxo personalizado', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='atendimentos', to='ui_operacional.etapafluxo'),
        ),
        
        # Adicionar índices ao Atendimento
        migrations.AddIndex(
            model_name='atendimento',
            index=models.Index(fields=['etapa_atual', 'atendente_humano'], name='oraculo_a_etap_aten_idx'),
        ),
        migrations.AddIndex(
            model_name='atendimento',
            index=models.Index(fields=['departamento', 'etapa_atual'], name='oraculo_a_depa_etap_idx'),
        ),
        
        # Criar constraint única para EtapaFluxo
        migrations.AlterUniqueTogether(
            name='etapafluxo',
            unique_together={('fluxo', 'ordem')},
        ),
    ]
```

Este documento fornece exemplos completos e práticos para implementar o sistema de fluxos personalizados, desde a criação dos modelos até a implementação dos serviços e APIs necessários.