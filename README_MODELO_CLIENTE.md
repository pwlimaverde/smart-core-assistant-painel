# Modelo Cliente

O modelo `Cliente` foi criado para armazenar informações completas dos clientes no sistema, incluindo dados cadastrais, endereço e relacionamento many-to-many com contatos. O modelo suporta tanto pessoas físicas quanto jurídicas.

## Características Principais

### Campos Obrigatórios
- **nome_fantasia**: Nome comum do cliente (único campo obrigatório)

### Dados do Cliente
- **razao_social**: Nome legal/oficial do cliente (principalmente para PJ)
- **tipo**: Tipo de pessoa - "fisica" ou "juridica" (opcional)
- **cnpj**: CNPJ com validação automática (formato: XX.XXX.XXX/XXXX-XX) - para PJ
- **cpf**: CPF com validação automática (formato: XXX.XXX.XXX-XX) - para PF
- **telefone**: Telefone fixo ou corporativo com validação
- **site**: URL do website do cliente
- **ramo_atividade**: Área de atuação
- **observacoes**: Informações adicionais

### Dados de Endereço
- **cep**: CEP com validação e formatação automática
- **logradouro**: Rua, avenida ou logradouro
- **numero**: Número do endereço
- **complemento**: Complemento (sala, andar, etc.)
- **bairro**: Bairro
- **cidade**: Cidade
- **uf**: Estado (formatado automaticamente para maiúscula)
- **pais**: País (padrão: "Brasil")

### Relacionamentos e Controle
- **contatos**: Relacionamento Many-to-Many com o modelo `Contato`
- **data_cadastro**: Data de criação automática
- **ultima_atualizacao**: Data de última modificação automática  
- **ativo**: Status de atividade do cliente
- **metadados**: Campo JSON para informações personalizadas

## Validações Automáticas

O modelo inclui validações automáticas para:
- **CNPJ**: Formato correto com 14 dígitos (pessoa jurídica)
- **CPF**: Formato correto com 11 dígitos (pessoa física)
- **CEP**: Formato correto com 8 dígitos  
- **Telefone**: Formato brasileiro (10-15 dígitos)

## Formatação Automática

Ao salvar, os dados são formatados automaticamente:
- **CNPJ**: `12345678000199` → `12.345.678/0001-99`
- **CPF**: `12345678900` → `123.456.789-00`
- **CEP**: `12345678` → `12345-678`  
- **UF**: `sp` → `SP`
- **Telefone**: Formatação de telefone fixo quando aplicável

## Métodos Úteis

### Endereço
```python
cliente.get_endereco_completo()  # Retorna endereço formatado completo
```

### Gerenciamento de Contatos
```python
cliente.adicionar_contato(contato)    # Vincula contato ao cliente
cliente.remover_contato(contato)      # Remove vinculação
cliente.get_contatos_ativos()         # Retorna contatos ativos vinculados
```

### Metadados
```python
cliente.atualizar_metadados(chave, valor)  # Atualiza metadados
cliente.get_metadados(chave, padrao)       # Recupera metadados
```

## Como Usar

### 1. Aplicar a Migração

Primeiro, aplique a migração criada:

```bash
cd src/smart_core_assistant_painel/app/ui
python manage.py migrate
```

### 2. Exemplo de Uso Básico - Pessoa Jurídica

```python
from oraculo.models import Cliente, Contato

# Criar cliente pessoa jurídica
cliente_pj = Cliente.objects.create(
    nome_fantasia="Microsoft Brasil",
    razao_social="Microsoft Informática Ltda",
    tipo="juridica",
    cnpj="04712500000107",  # Será formatado automaticamente
    site="https://www.microsoft.com/pt-br",
    ramo_atividade="Tecnologia da Informação",
    
    # Endereço
    cep="04567000",  # Será formatado automaticamente
    logradouro="Avenida Paulista", 
    numero="1234",
    cidade="São Paulo",
    uf="sp"  # Será convertido para "SP"
)

print(f"Cliente PJ: {cliente_pj}")
print(f"CNPJ formatado: {cliente_pj.cnpj}")
print(f"Endereço: {cliente_pj.get_endereco_completo()}")
```

### 2.1. Exemplo de Uso Básico - Pessoa Física

```python
# Criar cliente pessoa física
cliente_pf = Cliente.objects.create(
    nome_fantasia="João Silva",
    tipo="fisica",
    cpf="12345678900",  # Será formatado automaticamente
    
    # Endereço
    cep="01234567",  # Será formatado automaticamente
    logradouro="Rua das Flores",
    numero="123",
    cidade="São Paulo",
    uf="sp"  # Será convertido para "SP"
)

print(f"Cliente PF: {cliente_pf}")
print(f"CPF formatado: {cliente_pf.cpf}")
print(f"Endereço: {cliente_pf.get_endereco_completo()}")
```

### 3. Vinculação com Contatos

```python
# Criar/buscar contato
contato, created = Contato.objects.get_or_create(
    telefone="+5511987654321",
    defaults={'nome_contato': "João Silva"}
)

# Vincular ao cliente  
cliente_pj.adicionar_contato(contato)

# Listar contatos do cliente
for contato in cliente_pj.get_contatos_ativos():
    print(f"Contato: {contato.nome_contato} - {contato.telefone}")
```

### 4. Usando Metadados

```python
# Armazenar informações personalizadas
cliente_pj.atualizar_metadados("codigo_interno", "CLI-001")
cliente_pj.atualizar_metadados("setor_contato", "Vendas")
cliente_pj.atualizar_metadados("observacoes_comerciais", [
    "Cliente preferencial",
    "Desconto especial aprovado"
])

# Recuperar metadados
codigo = cliente_pj.get_metadados("codigo_interno")
setor = cliente_pj.get_metadados("setor_contato", "Não informado")
```

## Integração com Dados de Conversa

O modelo foi desenhado para trabalhar com os dados extraídos de conversas no formato JSON especificado:

```python
def processar_dados_cliente(dados_conversa):
    """
    Processa dados extraídos de uma conversa e cria/atualiza cliente.
    """
    dados_cliente = dados_conversa.get("dados_cliente", {})
    endereco_cliente = dados_conversa.get("endereco_cliente", {})
    
    cliente = Cliente()
    
    # Mapear dados básicos
    cliente.nome_fantasia = dados_cliente.get("nome_fantasia", "")
    cliente.razao_social = dados_cliente.get("razao_social")
    cliente.tipo = dados_cliente.get("tipo")  # "fisica" ou "juridica"
    cliente.cnpj = dados_cliente.get("cnpj")
    cliente.cpf = dados_cliente.get("cpf")
    cliente.telefone = dados_cliente.get("telefone")
    cliente.site = dados_cliente.get("site")
    cliente.ramo_atividade = dados_cliente.get("ramo_atividade")
    cliente.observacoes = dados_cliente.get("observacoes")
    
    # Mapear endereço
    cliente.cep = endereco_cliente.get("cep")
    cliente.logradouro = endereco_cliente.get("logradouro")
    cliente.numero = endereco_cliente.get("numero")
    cliente.complemento = endereco_cliente.get("complemento")
    cliente.bairro = endereco_cliente.get("bairro")
    cliente.cidade = endereco_cliente.get("cidade")
    cliente.uf = endereco_cliente.get("uf")
    cliente.pais = endereco_cliente.get("pais")
    
    cliente.save()  # Validações e formatações automáticas
    return cliente
```

## Buscas Comuns

```python
# Clientes ativos
clientes_ativos = Cliente.objects.filter(ativo=True)

# Por tipo de pessoa
clientes_pj = Cliente.objects.filter(tipo="juridica")
clientes_pf = Cliente.objects.filter(tipo="fisica")

# Por ramo de atividade
clientes_tech = Cliente.objects.filter(ramo_atividade__icontains="tecnologia")

# Por cidade
clientes_sp = Cliente.objects.filter(cidade="São Paulo")

# Com contatos relacionados (otimizada)
clientes_com_contatos = Cliente.objects.prefetch_related('contatos')

# Por CNPJ (pessoa jurídica)
cliente = Cliente.objects.filter(cnpj="12.345.678/0001-99").first()

# Por CPF (pessoa física)
cliente = Cliente.objects.filter(cpf="123.456.789-00").first()
```

## Admin do Django

O modelo está configurado com `verbose_name` e `verbose_name_plural` para exibição correta no Django Admin. Os campos possuem `help_text` descritivos para facilitar o uso.

## Considerações Técnicas

- **Performance**: Use `prefetch_related('contatos')` ao buscar clientes com seus contatos
- **Validações**: Todas as validações são executadas no `save()` e `clean()`
- **Formatação**: Dados são formatados automaticamente no `save()`
- **Flexibilidade**: Campo `metadados` permite extensão sem alteração do modelo
- **Relacionamento**: Many-to-Many permite que um contato seja cliente de múltiplos tipos
- **Suporte PF/PJ**: Campo `tipo` permite distinguir pessoas físicas de jurídicas

## Arquivos Relacionados

- **Modelo**: `src/smart_core_assistant_painel/app/ui/oraculo/models.py`
- **Migração**: `src/smart_core_assistant_painel/app/ui/oraculo/migrations/0013_empresa.py` (ou mais recente)
- **Exemplo de uso**: `exemplo_uso_model_cliente.py`
- **Exemplo de Uso**: `exemplo_uso_model_empresa.py`
