"""
Exemplo de uso da PydanticModelFactory com os JSONs fornecidos pelo usuário
"""

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model, )

# JSONs exatos fornecidos pelo usuário
entity_types_json = {
    "entity_types": {
        "identificacao_pessoal": {
            "cliente": "nome ou identificação do cliente",
            "contato": "informações de contato geral",
            "email": "endereço de email",
            "telefone": "número de telefone"
        },
        "produtos_servicos": {
            "tipo_produto": "categoria ou tipo de produto",
            "produto": "nome específico do produto",
            "servico": "tipo de serviço solicitado",
            "marca": "marca ou fabricante"
        },
        "quantidades_medidas": {
            "quantidade": "número ou volume de itens",
            "preco": "valor monetário ou orçamento",
            "desconto": "percentual ou valor de desconto"
        },
        "tempo_localizacao": {
            "prazo": "período ou data limite",
            "data": "data específica",
            "horario": "horário específico",
            "local": "endereço ou localização",
            "cidade": "nome da cidade"
        },
        "caracteristicas_tecnicas": {
            "cor": "cor do produto",
            "tamanho": "dimensões ou tamanho",
            "material": "tipo de material",
            "modelo": "modelo específico"
        },
        "identificadores_sistema": {
            "numero_protocolo": "número de protocolo de atendimento",
            "id_pedido": "identificador do pedido",
            "codigo_cliente": "código de identificação do cliente",
            "numero_ticket": "número do ticket de suporte",
            "codigo_produto": "código do produto"
        },
        "documentos_identificacao": {
            "cpf": "CPF do cliente",
            "cnpj": "CNPJ da empresa",
            "rg": "RG do cliente",
            "numero_conta": "número da conta",
            "codigo_transacao": "código da transação"
        },
        "dados_financeiros": {
            "forma_pagamento": "meio de pagamento",
            "numero_parcelas": "quantidade de parcelas",
            "vencimento": "data de vencimento",
            "valor_total": "valor total da transação",
            "juros": "taxa de juros"
        },
        "status_estados": {
            "status_pedido": "situação atual do pedido",
            "situacao_cliente": "status do cliente",
            "nivel_prioridade": "nível de prioridade do atendimento",
            "tipo_cliente": "categoria do cliente",
            "canal_origem": "canal de origem do contato"
        },
        "entrega_logistica": {
            "cep": "código postal",
            "endereco": "endereço completo",
            "transportadora": "empresa de transporte",
            "codigo_rastreamento": "código de rastreamento"
        },
        "suporte_tecnico": {
            "versao_sistema": "versão do sistema",
            "codigo_erro": "código de erro",
            "categoria_problema": "categoria do problema",
            "departamento": "departamento responsável"
        }
    }
}

intent_types_json = {
    "intent_types": {
        "comunicacao_basica": {
            "saudacao": "cumprimentos e apresentações",
            "despedida": "finalizações de conversa",
            "agradecimento": "expressões de gratidão"
        },
        "busca_informacao": {
            "pergunta": "solicitações de informação",
            "esclarecimento": "pedidos de clarificação",
            "consulta": "verificações de status ou disponibilidade"
        },
        "acoes_comerciais": {
            "solicitacao_servico": "pedidos de serviços ou produtos",
            "cotacao": "solicitações de orçamento ou preço",
            "pedido": "ordens de compra ou contratação",
            "cancelamento": "solicitações de cancelamento"
        },
        "feedback_suporte": {
            "reclamacao": "queixas ou problemas",
            "elogio": "comentários positivos ou satisfação",
            "sugestao": "propostas de melhoria",
            "relato_problema": "descrição de dificuldades técnicas"
        },
        "confirmacoes_validacoes": {
            "confirmacao": "confirmações de ações ou informações",
            "negacao": "recusas ou negativas",
            "aceitacao": "concordâncias ou aprovações"
        },
        "informacoes_fornecidas": {
            "apresentacao": "identificação pessoal ou empresarial",
            "informacao": "dados ou detalhes fornecidos",
            "instrucao": "orientações ou direcionamentos"
        },
        "urgencia_priorizacao": {
            "urgente": "solicitações com alta prioridade",
            "agendamento": "marcação de compromissos ou reuniões",
            "acompanhamento": "verificação de andamento de processos"
        },
        "controle_atendimento": {
            "transferir_humano": "solicitações para falar com atendente",
            "escalar_supervisor": "pedidos para falar com supervisor",
            "pausar_atendimento": "pausar o atendimento temporariamente",
            "finalizar_atendimento": "encerrar o atendimento"
        },
        "autenticacao_seguranca": {
            "login": "tentativas de acesso ao sistema",
            "validar_identidade": "verificações de identidade",
            "reset_senha": "solicitações de redefinição de senha",
            "recuperar_acesso": "recuperação de acesso ao sistema"
        },
        "gerenciamento_dados": {
            "atualizar_dados": "atualização de informações",
            "excluir_dados": "exclusão de informações",
            "consultar_historico": "consulta ao histórico",
            "exportar_dados": "exportação de dados"
        }
    }
}


def demonstrar_uso() -> None:
    """
    Demonstra o uso da factory com os JSONs do usuário
    """
    print("=== Demonstração da PydanticModelFactory ===\n")

    # Criar o modelo dinâmico
    PydanticModel = create_dynamic_pydantic_model(
        intent_types_json=intent_types_json,
        entity_types_json=entity_types_json
    )

    print("✅ Modelo PydanticModel criado dinamicamente!")
    print(f"Nome da classe: {PydanticModel.__name__}")

    # Mostrar um trecho da documentação gerada
    if PydanticModel.__doc__:
        doc_lines = PydanticModel.__doc__.split('\n')
        print("\n📚 Documentação gerada (primeiras 20 linhas):")
        for i, line in enumerate(doc_lines[:20]):
            print(f"  {line}")

        print("  [... documentação continua ...]")

    # Exemplo de uso prático
    print("\n🔧 Exemplo de uso:")
    exemplo_mensagem = PydanticModel(
        intent=[
            {"type": "saudacao", "value": "Olá, tudo bem?"},
            {"type": "cotacao", "value": "gostaria de uma cotação"},
            {"type": "pergunta", "value": "vocês produzem cones para crepe?"}
        ],
        entities=[
            {"type": "cliente", "value": "Paulo"},
            {"type": "produto", "value": "cones para crepe"},
            {"type": "servico", "value": "cotação"}
        ]
    )

    print(f"Instância criada com sucesso: {type(exemplo_mensagem).__name__}")

    print("✨ Demonstração concluída! A factory funciona perfeitamente.")
    print("🎯 Agora você pode usar os JSONs de configuração para gerar")
    print("   dinamicamente a classe PydanticModel com tipos e documentação")
    print("   personalizados para cada contexto de uso.")


if __name__ == "__main__":
    demonstrar_uso()
