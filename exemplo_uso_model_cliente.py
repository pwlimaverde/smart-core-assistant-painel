"""
Exemplo de uso do modelo Cliente.

Este arquivo demonstra como utilizar o novo modelo Cliente
para gerenciar informações dos clientes e seus relacionamentos
com contatos.
"""

from typing import Any, Dict


# Exemplo de como usar o modelo Cliente após aplicar as migrations
def exemplo_criacao_cliente():
    """
    Exemplo de criação de um cliente com dados completos.

    Este exemplo mostra como criar um cliente com todas as
    informações disponíveis no modelo.
    """
    from oraculo.models import Cliente

    # Criando um cliente pessoa jurídica com dados completos
    cliente = Cliente.objects.create(
        nome_fantasia="Microsoft Brasil",
        razao_social="Microsoft Informática Ltda",
        tipo="juridica",
        cnpj="04.712.500/0001-07",  # CNPJ será formatado automaticamente
        telefone="(11) 3123-4567",
        site="https://www.microsoft.com/pt-br",
        ramo_atividade="Tecnologia da Informação",
        observacoes="Filial brasileira da Microsoft Corporation",

        # Dados de endereço
        cep="04567-000",  # CEP será formatado automaticamente
        logradouro="Avenida Paulista",
        numero="1234",
        complemento="Torre A - 15º andar",
        bairro="Bela Vista",
        cidade="São Paulo",
        uf="sp",  # UF será convertida para maiúscula automaticamente
        pais="Brasil",

        # Metadados personalizados
        metadados={
            "setor_responsavel": "Vendas Empresariais",
            "horario_funcionamento": "08:00-18:00",
            "codigo_cliente_interno": "MS-BR-001"
        }
    )

    print(f"Cliente criado: {cliente}")

    # Exemplo de criação de cliente pessoa física
    cliente_pf = Cliente.objects.create(
        nome_fantasia="João Silva",
        tipo="fisica",
        cpf="123.456.789-00",  # CPF será formatado automaticamente
        telefone="(11) 98765-4321",
        observacoes="Cliente pessoa física",

        # Dados de endereço
        cep="01234-567",
        logradouro="Rua das Flores",
        numero="123",
        bairro="Jardim das Rosas",
        cidade="São Paulo",
        uf="sp",
        pais="Brasil",

        # Metadados personalizados
        metadados={
            "data_nascimento": "1985-06-15",
            "profissao": "Engenheiro de Software"
        }
    )

    print(f"Cliente PF criado: {cliente_pf}")

    # Mostra os dados formatados
    print(f"Endereço completo: {cliente.get_endereco_completo()}")

    return cliente


def exemplo_vinculacao_contatos():
    """
    Exemplo de vinculação de contatos ao cliente.
    """
    from oraculo.models import Cliente, Contato

    # Busca um cliente existente
    cliente = Cliente.objects.get(nome_fantasia="Microsoft Brasil")

    # Cria ou busca contatos
    contato1, created = Contato.objects.get_or_create(
        telefone="+5511987654321",
        defaults={'nome_contato': "João Silva - Vendas Microsoft"}
    )

    contato2, created = Contato.objects.get_or_create(
        telefone="+5511123456789",
        defaults={'nome_contato': "Maria Santos - Suporte Microsoft"}
    )

    # Vincula contatos ao cliente
    cliente.adicionar_contato(contato1)
    cliente.adicionar_contato(contato2)

    # Lista contatos do cliente
    contatos_ativos = cliente.get_contatos_ativos()
    print(f"Contatos ativos do cliente {cliente.nome_fantasia}:")
    for contato in contatos_ativos:
        print(f"- {contato.nome_contato} ({contato.telefone})")


def exemplo_busca_clientes():
    """
    Exemplo de buscas e consultas no modelo Cliente.
    """
    from oraculo.models import Cliente

    # Busca clientes ativos
    clientes_ativos = Cliente.objects.filter(ativo=True)

    # Busca por ramo de atividade
    clientes_tecnologia = Cliente.objects.filter(
        ramo_atividade__icontains="tecnologia"
    )

    # Busca por cidade
    clientes_sp = Cliente.objects.filter(cidade="São Paulo")

    # Busca por tipo de pessoa
    clientes_pj = Cliente.objects.filter(tipo="juridica")
    clientes_pf = Cliente.objects.filter(tipo="fisica")

    # Busca com contatos relacionados
    clientes_com_contatos = Cliente.objects.prefetch_related('contatos')

    print("Exemplos de buscas:")
    print(f"- Clientes ativos: {clientes_ativos.count()}")
    print(f"- Clientes de tecnologia: {clientes_tecnologia.count()}")
    print(f"- Clientes em SP: {clientes_sp.count()}")
    print(f"- Clientes PJ: {clientes_pj.count()}")
    print(f"- Clientes PF: {clientes_pf.count()}")

    for cliente in clientes_com_contatos[:5]:  # Primeiros 5
        print(f"- {cliente.nome_fantasia} tem {cliente.contatos.count()} contatos")


def exemplo_atualizacao_metadados():
    """
    Exemplo de uso dos metadados para armazenar informações personalizadas.
    """
    from oraculo.models import Cliente

    # Busca um cliente
    cliente = Cliente.objects.first()

    if cliente:
        # Atualiza metadados
        cliente.atualizar_metadados("ultima_negociacao", "2025-07-22")
        cliente.atualizar_metadados("valor_contrato", 50000.00)
        cliente.atualizar_metadados("observacoes_comerciais", [
            "Cliente interessado em licenças Office",
            "Necessita apresentação presencial",
            "Decisor final: Diretor de TI"
        ])

        # Recupera metadados
        ultima_negociacao = cliente.get_metadados("ultima_negociacao")
        valor_contrato = cliente.get_metadados("valor_contrato", 0)

        print(
            f"Última negociação com {
                cliente.nome_fantasia}: {ultima_negociacao}")
        print(f"Valor do contrato: R$ {valor_contrato:,.2f}")


def exemplo_dados_extraidos_conversa():
    """
    Exemplo de como os dados seriam extraídos de uma conversa
    e armazenados no modelo Cliente.

    Este exemplo simula como os dados JSON fornecidos pelo usuário
    seriam processados e salvos no banco de dados.
    """

    # Exemplo de dados extraídos de uma conversa - Pessoa Jurídica
    dados_conversa_pj = {
        "dados_cliente": {
            "nome_fantasia": "Microsoft",
            "razao_social": "Microsoft Corporation",
            "tipo": "juridica",
            "cnpj": "12.345.678/0001-99",
            "telefone": "(11) 3123-4567",
            "site": "https://www.microsoft.com",
            "ramo_atividade": "Tecnologia da Informação",
            "observacoes": "filial no Rio de Janeiro"
        },
        "endereco_cliente": {
            "cep": "04567-000",
            "logradouro": "Av. Paulista",
            "numero": "1234",
            "complemento": "Torre A",
            "bairro": "Bela Vista",
            "cidade": "São Paulo",
            "uf": "SP",
            "pais": "Brasil"
        }
    }

    # Exemplo de dados extraídos - Pessoa Física
    dados_conversa_pf = {
        "dados_cliente": {
            "nome_fantasia": "João Silva",
            "tipo": "fisica",
            "cpf": "123.456.789-00",
            "telefone": "(11) 98765-4321",
            "observacoes": "Cliente desde 2020"
        },
        "endereco_cliente": {
            "cep": "01234-567",
            "logradouro": "Rua das Flores",
            "numero": "123",
            "bairro": "Jardim das Rosas",
            "cidade": "São Paulo",
            "uf": "SP",
            "pais": "Brasil"
        }
    }

    # Função para processar os dados e criar/atualizar cliente
    def processar_dados_cliente(dados: Dict[str, Any]) -> 'Cliente':
        from oraculo.models import Cliente

        dados_cliente = dados.get("dados_cliente", {})
        endereco_cliente = dados.get("endereco_cliente", {})

        # Tenta encontrar cliente existente pelo CNPJ, CPF ou nome
        cliente = None
        if dados_cliente.get("cnpj"):
            cnpj_formatado = dados_cliente["cnpj"]
            cliente = Cliente.objects.filter(cnpj=cnpj_formatado).first()
        elif dados_cliente.get("cpf"):
            cpf_formatado = dados_cliente["cpf"]
            cliente = Cliente.objects.filter(cpf=cpf_formatado).first()

        if not cliente and dados_cliente.get("nome_fantasia"):
            cliente = Cliente.objects.filter(
                nome_fantasia=dados_cliente["nome_fantasia"]
            ).first()

        # Cria novo cliente se não encontrar
        if not cliente:
            cliente = Cliente()

        # Atualiza dados básicos
        if dados_cliente.get("nome_fantasia"):
            cliente.nome_fantasia = dados_cliente["nome_fantasia"]
        if dados_cliente.get("razao_social"):
            cliente.razao_social = dados_cliente["razao_social"]
        if dados_cliente.get("tipo"):
            cliente.tipo = dados_cliente["tipo"]
        if dados_cliente.get("cnpj"):
            cliente.cnpj = dados_cliente["cnpj"]
        if dados_cliente.get("cpf"):
            cliente.cpf = dados_cliente["cpf"]
        if dados_cliente.get("telefone"):
            cliente.telefone = dados_cliente["telefone"]
        if dados_cliente.get("site"):
            cliente.site = dados_cliente["site"]
        if dados_cliente.get("ramo_atividade"):
            cliente.ramo_atividade = dados_cliente["ramo_atividade"]
        if dados_cliente.get("observacoes"):
            cliente.observacoes = dados_cliente["observacoes"]

        # Atualiza dados de endereço
        if endereco_cliente.get("cep"):
            cliente.cep = endereco_cliente["cep"]
        if endereco_cliente.get("logradouro"):
            cliente.logradouro = endereco_cliente["logradouro"]
        if endereco_cliente.get("numero"):
            cliente.numero = endereco_cliente["numero"]
        if endereco_cliente.get("complemento"):
            cliente.complemento = endereco_cliente["complemento"]
        if endereco_cliente.get("bairro"):
            cliente.bairro = endereco_cliente["bairro"]
        if endereco_cliente.get("cidade"):
            cliente.cidade = endereco_cliente["cidade"]
        if endereco_cliente.get("uf"):
            cliente.uf = endereco_cliente["uf"]
        if endereco_cliente.get("pais"):
            cliente.pais = endereco_cliente["pais"]

        # Salva com validações automáticas (formatação de CNPJ, CPF, CEP, etc.)
        cliente.save()

        return cliente

    # Processa os dados de exemplo
    cliente_pj_criado = processar_dados_cliente(dados_conversa_pj)
    cliente_pf_criado = processar_dados_cliente(dados_conversa_pf)

    print(f"Cliente PJ processado: {cliente_pj_criado}")
    print(f"CNPJ formatado: {cliente_pj_criado.cnpj}")
    print(f"CEP formatado: {cliente_pj_criado.cep}")
    print(f"Endereço completo: {cliente_pj_criado.get_endereco_completo()}")

    print(f"Cliente PF processado: {cliente_pf_criado}")
    print(f"CPF formatado: {cliente_pf_criado.cpf}")

    return cliente_pj_criado


def exemplo_integracao_com_atendimento():
    """
    Exemplo de como integrar o modelo Cliente com o fluxo de atendimento.
    """
    from oraculo.models import Atendimento

    # Simula situação onde durante um atendimento são coletados dados do
    # cliente
    def vincular_cliente_ao_atendimento(
            atendimento_id: int,
            dados_cliente: dict):
        """
        Vincula um cliente ao contato de um atendimento.
        """
        atendimento = Atendimento.objects.get(id=atendimento_id)
        contato = atendimento.contato

        # Processa dados do cliente (necessário referenciar a função local)
        def processar_dados_cliente_local(dados):
            # Reimplemente a lógica aqui ou importe da função principal
            pass  # Implementação simplificada para exemplo

        cliente = processar_dados_cliente_local(dados_cliente)

        # Vincula cliente ao contato
        cliente.adicionar_contato(contato)

        # Atualiza contexto do atendimento
        atendimento.atualizar_contexto("cliente_vinculado", {
            "id": cliente.id,
            "nome_fantasia": cliente.nome_fantasia,
            "tipo": cliente.tipo,
            "data_vinculacao": "2025-07-22T16:35:00Z"
        })

        print(
            f"Cliente {
                cliente.nome_fantasia} vinculado ao atendimento {
                atendimento.id}")

        return cliente


if __name__ == "__main__":
    """
    Para executar este exemplo, primeiro aplique a migração:

    cd src/smart_core_assistant_painel/app/ui
    python manage.py migrate

    Depois execute este arquivo:
    python manage.py shell < exemplo_uso_model_cliente.py
    """
    print("Exemplo de uso do modelo Cliente")
    print("=" * 50)

    # Descomente as funções abaixo conforme necessário
    # exemplo_criacao_cliente()
    # exemplo_vinculacao_contatos()
    # exemplo_busca_clientes()
    # exemplo_atualizacao_metadados()
    # exemplo_dados_extraidos_conversa()
