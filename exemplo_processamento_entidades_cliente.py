"""
Exemplo de uso do processamento de entidades do cliente

Este arquivo demonstra como o sistema processa automaticamente
as entidades extraídas para atualizar dados do cliente.
"""

# Exemplo 1: Entidades extraídas com nome do cliente
entity_types_exemplo_1 = [
    {"cliente": "João Silva"},
    {"email": "joao.silva@email.com"},
    {"telefone": "(11) 99999-9999"}
]

# Resultado esperado:
# - cliente.nome = "João Silva"
# - cliente.metadados = {
#     "email": "joao.silva@email.com",
#     "telefone": "(11) 99999-9999"
# }

# Exemplo 2: Apenas dados complementares
entity_types_exemplo_2 = [
    {"cpf": "123.456.789-00"},
    {"endereco": "Rua das Flores, 123"},
    {"cidade": "São Paulo"}
]

# Resultado esperado:
# - cliente.nome permanece inalterado
# - cliente.metadados é atualizado com:
#   {
#     "cpf": "123.456.789-00",
#     "endereco": "Rua das Flores, 123",
#     "cidade": "São Paulo"
#   }

# Exemplo 3: Cliente sem nome ainda
entity_types_exemplo_3 = [
    {"produto": "Notebook Dell"},
    {"preco": "R$ 2.500,00"}
]

# Resultado esperado:
# - Nenhuma atualização do cliente
# - Se ativada, solicitação automática de dados será enviada

print("Exemplos de processamento de entidades configurados!")
print("As funções _processar_entidades_cliente e _solicitar_dados_cliente_se_necessario")
print("estão implementadas em views.py e serão chamadas automaticamente durante")
print("o processamento de mensagens no webhook do WhatsApp.")

print("\nEntidades suportadas para metadados do cliente:")
entidades_suportadas = [
    'contato', 'email', 'telefone', 'cpf', 'cnpj', 'endereco',
    'cidade', 'estado', 'cep', 'rg', 'data_nascimento', 'profissao'
]

for entidade in entidades_suportadas:
    print(f"- {entidade}")

print("\nPara ativar a solicitação automática de dados do cliente,")
print("descomente a linha em _analisar_conteudo_mensagem() no views.py:")
print("# _solicitar_dados_cliente_se_necessario(mensagem)")
