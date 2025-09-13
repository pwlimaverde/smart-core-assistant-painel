#!/usr/bin/env python3
"""
Script de simulação para demonstrar o uso do método to_embedding_text
do modelo QueryCompose com logs estruturados.

Este script simula diferentes cenários de uso do método to_embedding_text,
mostrando como o método funciona com diferentes combinações de dados.
"""

import os
import sys
from typing import List, Dict, Any

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import FeaturesCompose



# Configuração do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.ui.core.settings")

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import django
django.setup()

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smart_core_assistant_painel.app.ui.treinamento.models import QueryCompose

# Configuração do console rich
console = Console()

# Configuração do loguru
logger.remove()  # Remove o handler padrão
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


def create_sample_queries() -> List[QueryCompose]:
    """Cria queries de exemplo para demonstração."""
    logger.info("Criando queries de exemplo para demonstração")
    
    sample_data = [
        {
            "tag": "orcamento",
            "grupo": "vendas",
            "descricao": "Solicitação de orçamento para produtos ou serviços",
            "exemplo": "Preciso de um orçamento para 100 camisetas personalizadas",
            "comportamento": "Você deve solicitar detalhes específicos sobre o produto e fornecer informações de preço."
        },
        {
            "tag": "suporte_tecnico",
            "grupo": "atendimento",
            "descricao": "Problemas técnicos com produtos ou serviços",
            "exemplo": "Meu sistema não está funcionando corretamente",
            "comportamento": "Identifique o problema e forneça soluções passo a passo."
        },
        {
            "tag": "informacoes_produto",
            "grupo": "vendas",
            "descricao": "Consultas sobre características e especificações de produtos",
            "exemplo": "Quais são as especificações técnicas do produto X?",
            "comportamento": "Forneça informações detalhadas e precisas sobre o produto."
        },
        {
            "tag": "reclamacao",
            "grupo": "atendimento",
            "descricao": "Reclamações sobre produtos ou serviços",
            "exemplo": "",  # Exemplo vazio para testar
            "comportamento": "Ouça atentamente e busque soluções para resolver o problema."
        },
        {
            "tag": "",  # Tag vazia para testar
            "grupo": "teste",
            "descricao": "",  # Descrição vazia
            "exemplo": "",  # Exemplo vazio
            "comportamento": "Comportamento de teste"
        }
    ]
    
    queries = []
    for data in sample_data:
        query = QueryCompose(**data)
        queries.append(query)
        logger.debug(f"Query criada: tag='{data['tag']}', grupo='{data['grupo']}'")
    
    logger.info(f"Total de {len(queries)} queries criadas")
    return queries


def demonstrate_embedding_text(queries: List[QueryCompose]) -> None:
    """Demonstra o uso do método to_embedding_text."""
    logger.info("Iniciando demonstração do método to_embedding_text")
    
    # Criar tabela para exibir resultados
    table = Table(title="Demonstração do método to_embedding_text")
    table.add_column("Tag", style="cyan", no_wrap=True)
    table.add_column("Grupo", style="magenta")
    table.add_column("Texto para Embedding", style="green")
    table.add_column("Tamanho", style="yellow", justify="right")
    
    for i, query in enumerate(queries, 1):
        logger.info(f"Processando query {i}/{len(queries)}")
        
        # Log dos dados de entrada
        logger.debug(
            "Dados da query",
            extra={
                "tag": query.tag,
                "grupo": query.grupo,
                "descricao_length": len(query.descricao or ""),
                "exemplo_length": len(query.exemplo or "")
            }
        )
        
        # Gerar texto para embedding
        embedding_text = query.to_embedding_text()
        consulta = 'agradecimento: Agradeço a atenção'	
        embedding_vector: list[float] = FeaturesCompose.generate_embeddings(
            text=consulta
        )
        teste_comportamento = QueryCompose.buscar_comportamento_similar(embedding_vector)
        logger.warning(f"Teste comportamento: {teste_comportamento}")
        
        # Log do resultado
        logger.info(
            "Texto para embedding gerado",
            extra={
                "tag": query.tag or "[vazio]",
                "embedding_length": len(embedding_text),
                "has_content": bool(embedding_text.strip())
            }
        )
        
        # Adicionar à tabela
        tag_display = query.tag or "[vazio]"
        grupo_display = query.grupo or "[vazio]"
        text_display = embedding_text if embedding_text else "[sem conteúdo]"
        
        # Truncar texto longo para exibição
        if len(text_display) > 80:
            text_display = text_display[:77] + "..."
        
        table.add_row(
            tag_display,
            grupo_display,
            text_display,
            str(len(embedding_text))
        )
        
        # Log detalhado do conteúdo
        if embedding_text:
            logger.debug(f"Conteúdo completo do embedding:\n{embedding_text}")
        else:
            logger.warning("Query não gerou conteúdo para embedding")
    
    # Exibir tabela
    console.print(table)
    logger.info("Demonstração concluída")


def analyze_embedding_patterns(queries: List[QueryCompose]) -> None:
    """Analisa padrões nos textos gerados para embedding."""
    logger.info("Iniciando análise de padrões dos embeddings")
    
    stats = {
        "total_queries": len(queries),
        "with_content": 0,
        "empty_content": 0,
        "avg_length": 0,
        "max_length": 0,
        "min_length": float('inf')
    }
    
    lengths = []
    
    for query in queries:
        embedding_text = query.to_embedding_text()
        length = len(embedding_text)
        
        if embedding_text.strip():
            stats["with_content"] += 1
            lengths.append(length)
            stats["max_length"] = max(stats["max_length"], length)
            stats["min_length"] = min(stats["min_length"], length)
        else:
            stats["empty_content"] += 1
    
    if lengths:
        stats["avg_length"] = sum(lengths) / len(lengths)
    else:
        stats["min_length"] = 0
    
    # Log das estatísticas
    logger.info(
        "Estatísticas dos embeddings",
        extra=stats
    )
    
    # Exibir painel com estatísticas
    stats_text = Text()
    stats_text.append(f"Total de queries: {stats['total_queries']}\n", style="bold")
    stats_text.append(f"Com conteúdo: {stats['with_content']}\n", style="green")
    stats_text.append(f"Sem conteúdo: {stats['empty_content']}\n", style="red")
    stats_text.append(f"Tamanho médio: {stats['avg_length']:.1f} caracteres\n", style="blue")
    stats_text.append(f"Tamanho máximo: {stats['max_length']} caracteres\n", style="blue")
    stats_text.append(f"Tamanho mínimo: {stats['min_length']} caracteres", style="blue")
    
    console.print(Panel(stats_text, title="📊 Estatísticas dos Embeddings", border_style="blue"))


def main() -> None:
    """Função principal do script de simulação."""
    logger.info("Iniciando simulação do uso do método to_embedding_text")
    
    try:
        # Exibir cabeçalho
        console.print(Panel(
            "🤖 Simulação do método to_embedding_text\n"
            "Este script demonstra como o método funciona com diferentes cenários de dados.",
            title="Smart Core Assistant - Simulação de Embedding",
            border_style="green"
        ))
        
        # Criar queries de exemplo
        queries = create_sample_queries()
        
        # Demonstrar uso do método
        demonstrate_embedding_text(queries)
        
        # Analisar padrões
        analyze_embedding_patterns(queries)
        
        logger.success("Simulação concluída com sucesso")
        
    except Exception as e:
        logger.error(f"Erro durante a simulação: {e}")
        console.print(f"❌ Erro: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()