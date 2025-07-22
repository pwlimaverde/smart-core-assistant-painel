"""
Exemplo de uso do modelo Empresa.

Este arquivo demonstra como utilizar o novo modelo Empresa
para gerenciar informações das empresas e seus relacionamentos
com contatos.
"""

from typing import Any, Dict


# Exemplo de como usar o modelo Empresa após aplicar as migrations
def exemplo_criacao_empresa():
    """
    Exemplo de criação de uma empresa com dados completos.

    Este exemplo mostra como criar uma empresa com todas as
    informações disponíveis no modelo.
    """
    from oraculo.models import Empresa

    # Criando uma empresa com dados completos
    empresa = Empresa.objects.create(
        nome_fantasia="Microsoft Brasil",
        razao_social="Microsoft Informática Ltda",
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

    print(f"Empresa criada: {empresa}")
    print(f"Endereço completo: {empresa.get_endereco_completo()}")

    return empresa


def exemplo_vinculacao_contatos():
    """
    Exemplo de vinculação de contatos à empresa.
    """
    from oraculo.models import Contato, Empresa

    # Busca uma empresa existente
    empresa = Empresa.objects.get(nome_fantasia="Microsoft Brasil")

    # Cria ou busca contatos
    contato1, created = Contato.objects.get_or_create(
        telefone="+5511987654321",
        defaults={'nome': "João Silva - Vendas Microsoft"}
    )

    contato2, created = Contato.objects.get_or_create(
        telefone="+5511123456789",
        defaults={'nome': "Maria Santos - Suporte Microsoft"}
    )

    # Vincula contatos à empresa
    empresa.adicionar_contato(contato1)
    empresa.adicionar_contato(contato2)

    # Lista contatos da empresa
    contatos_ativos = empresa.get_contatos_ativos()
    print(f"Contatos ativos da {empresa.nome_fantasia}:")
    for contato in contatos_ativos:
        print(f"- {contato.nome_contato} ({contato.telefone})")


def exemplo_busca_empresas():
    """
    Exemplo de buscas e consultas no modelo Empresa.
    """
    from oraculo.models import Empresa

    # Busca empresas ativas
    empresas_ativas = Empresa.objects.filter(ativo=True)

    # Busca por ramo de atividade
    empresas_tecnologia = Empresa.objects.filter(
        ramo_atividade__icontains="tecnologia"
    )

    # Busca por cidade
    empresas_sp = Empresa.objects.filter(cidade="São Paulo")

    # Busca com contatos relacionados
    empresas_com_contatos = Empresa.objects.prefetch_related('contatos')

    print("Exemplos de buscas:")
    print(f"- Empresas ativas: {empresas_ativas.count()}")
    print(f"- Empresas de tecnologia: {empresas_tecnologia.count()}")
    print(f"- Empresas em SP: {empresas_sp.count()}")

    for empresa in empresas_com_contatos[:5]:  # Primeiras 5
        print(f"- {empresa.nome_fantasia} tem {empresa.contatos.count()} contatos")


def exemplo_atualizacao_metadados():
    """
    Exemplo de uso dos metadados para armazenar informações personalizadas.
    """
    from oraculo.models import Empresa

    # Busca uma empresa
    empresa = Empresa.objects.first()

    if empresa:
        # Atualiza metadados
        empresa.atualizar_metadados("ultima_negociacao", "2025-07-22")
        empresa.atualizar_metadados("valor_contrato", 50000.00)
        empresa.atualizar_metadados("observacoes_comerciais", [
            "Cliente interessado em licenças Office",
            "Necessita apresentação presencial",
            "Decisor final: Diretor de TI"
        ])

        # Recupera metadados
        ultima_negociacao = empresa.get_metadados("ultima_negociacao")
        valor_contrato = empresa.get_metadados("valor_contrato", 0)

        print(
            f"Última negociação com {
                empresa.nome_fantasia}: {ultima_negociacao}")
        print(f"Valor do contrato: R$ {valor_contrato:,.2f}")


def exemplo_dados_extraidos_conversa():
    """
    Exemplo de como os dados seriam extraídos de uma conversa
    e armazenados no modelo Empresa.

    Este exemplo simula como os dados JSON fornecidos pelo usuário
    seriam processados e salvos no banco de dados.
    """

    # Exemplo de dados extraídos de uma conversa (formato original solicitado)
    dados_conversa = {
        "dados_empresa": {
            "nome_fantasia": "Microsoft",
            "razao_social": "Microsoft Corporation",
            "cnpj": "12.345.678/0001-99",
            "telefone": "(11) 3123-4567",
            "site": "https://www.microsoft.com",
            "ramo_atividade": "Tecnologia da Informação",
            "observacoes": "filial no Rio de Janeiro"
        },
        "endereco_empresa": {
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

    # Função para processar os dados e criar/atualizar empresa
    def processar_dados_empresa(dados: Dict[str, Any]) -> 'Empresa':
        from oraculo.models import Empresa

        dados_empresa = dados.get("dados_empresa", {})
        endereco_empresa = dados.get("endereco_empresa", {})

        # Tenta encontrar empresa existente pelo CNPJ ou nome
        empresa = None
        if dados_empresa.get("cnpj"):
            cnpj_formatado = dados_empresa["cnpj"]
            empresa = Empresa.objects.filter(cnpj=cnpj_formatado).first()

        if not empresa and dados_empresa.get("nome_fantasia"):
            empresa = Empresa.objects.filter(
                nome_fantasia=dados_empresa["nome_fantasia"]
            ).first()

        # Cria nova empresa se não encontrar
        if not empresa:
            empresa = Empresa()

        # Atualiza dados básicos
        if dados_empresa.get("nome_fantasia"):
            empresa.nome_fantasia = dados_empresa["nome_fantasia"]
        if dados_empresa.get("razao_social"):
            empresa.razao_social = dados_empresa["razao_social"]
        if dados_empresa.get("cnpj"):
            empresa.cnpj = dados_empresa["cnpj"]
        if dados_empresa.get("telefone"):
            empresa.telefone = dados_empresa["telefone"]
        if dados_empresa.get("site"):
            empresa.site = dados_empresa["site"]
        if dados_empresa.get("ramo_atividade"):
            empresa.ramo_atividade = dados_empresa["ramo_atividade"]
        if dados_empresa.get("observacoes"):
            empresa.observacoes = dados_empresa["observacoes"]

        # Atualiza dados de endereço
        if endereco_empresa.get("cep"):
            empresa.cep = endereco_empresa["cep"]
        if endereco_empresa.get("logradouro"):
            empresa.logradouro = endereco_empresa["logradouro"]
        if endereco_empresa.get("numero"):
            empresa.numero = endereco_empresa["numero"]
        if endereco_empresa.get("complemento"):
            empresa.complemento = endereco_empresa["complemento"]
        if endereco_empresa.get("bairro"):
            empresa.bairro = endereco_empresa["bairro"]
        if endereco_empresa.get("cidade"):
            empresa.cidade = endereco_empresa["cidade"]
        if endereco_empresa.get("uf"):
            empresa.uf = endereco_empresa["uf"]
        if endereco_empresa.get("pais"):
            empresa.pais = endereco_empresa["pais"]

        # Salva com validações automáticas (formatação de CNPJ, CEP, etc.)
        empresa.save()

        return empresa

    # Processa os dados de exemplo
    empresa_criada = processar_dados_empresa(dados_conversa)

    print(f"Empresa processada: {empresa_criada}")
    print(f"CNPJ formatado: {empresa_criada.cnpj}")
    print(f"CEP formatado: {empresa_criada.cep}")
    print(f"Endereço completo: {empresa_criada.get_endereco_completo()}")

    return empresa_criada


def exemplo_integracao_com_atendimento():
    """
    Exemplo de como integrar o modelo Empresa com o fluxo de atendimento.
    """
    from oraculo.models import Atendimento

    # Simula situação onde durante um atendimento são coletados dados da
    # empresa
    def vincular_empresa_ao_atendimento(
            atendimento_id: int,
            dados_empresa: dict):
        """
        Vincula uma empresa ao contato de um atendimento.
        """
        atendimento = Atendimento.objects.get(id=atendimento_id)
        contato = atendimento.cliente

        # Processa dados da empresa
        empresa = processar_dados_empresa(dados_empresa)

        # Vincula empresa ao contato
        empresa.adicionar_contato(contato)

        # Atualiza contexto do atendimento
        atendimento.atualizar_contexto("empresa_vinculada", {
            "id": empresa.id,
            "nome_fantasia": empresa.nome_fantasia,
            "data_vinculacao": "2025-07-22T16:35:00Z"
        })

        print(
            f"Empresa {
                empresa.nome_fantasia} vinculada ao atendimento {
                atendimento.id}")

        return empresa


if __name__ == "__main__":
    """
    Para executar este exemplo, primeiro aplique a migração:

    cd src/smart_core_assistant_painel/app/ui
    python manage.py migrate

    Depois execute este arquivo:
    python manage.py shell < exemplo_uso_model_empresa.py
    """
    print("Exemplo de uso do modelo Empresa")
    print("=" * 50)

    # Descomente as funções abaixo conforme necessário
    # exemplo_criacao_empresa()
    # exemplo_vinculacao_contatos()
    # exemplo_busca_empresas()
    # exemplo_atualizacao_metadados()
    # exemplo_dados_extraidos_conversa()
