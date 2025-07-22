# Modelo Empresa

O modelo `Empresa` foi criado para armazenar informações completas das empresas no sistema, incluindo dados cadastrais, endereço e relacionamento many-to-many com contatos.

## Características Principais

### Campos Obrigatórios
- **nome_fantasia**: Nome comum da empresa (único campo obrigatório)

### Dados da Empresa
- **razao_social**: Nome legal/oficial da empresa
- **cnpj**: CNPJ com validação automática (formato: XX.XXX.XXX/XXXX-XX)
- **telefone**: Telefone fixo ou corporativo com validação
- **site**: URL do website da empresa
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
- **ativo**: Status de atividade da empresa
- **metadados**: Campo JSON para informações personalizadas

## Validações Automáticas

O modelo inclui validações automáticas para:
- **CNPJ**: Formato correto com 14 dígitos
- **CEP**: Formato correto com 8 dígitos  
- **Telefone**: Formato brasileiro (10-15 dígitos)

## Formatação Automática

Ao salvar, os dados são formatados automaticamente:
- **CNPJ**: `12345678000199` → `12.345.678/0001-99`
- **CEP**: `12345678` → `12345-678`  
- **UF**: `sp` → `SP`
- **Telefone**: Formatação de telefone fixo quando aplicável

## Métodos Úteis

### Endereço
```python
empresa.get_endereco_completo()  # Retorna endereço formatado completo
```

### Gerenciamento de Contatos
```python
empresa.adicionar_contato(contato)    # Vincula contato à empresa
empresa.remover_contato(contato)      # Remove vinculação
empresa.get_contatos_ativos()         # Retorna contatos ativos vinculados
```

### Metadados
```python
empresa.atualizar_metadados(chave, valor)  # Atualiza metadados
empresa.get_metadados(chave, padrao)       # Recupera metadados
```

## Como Usar

### 1. Aplicar a Migração

Primeiro, aplique a migração criada:

```bash
cd src/smart_core_assistant_painel/app/ui
python manage.py migrate
```

### 2. Exemplo de Uso Básico

```python
from oraculo.models import Empresa, Contato

# Criar empresa
empresa = Empresa.objects.create(
    nome_fantasia="Microsoft Brasil",
    razao_social="Microsoft Informática Ltda",
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

print(f"Empresa: {empresa}")
print(f"CNPJ formatado: {empresa.cnpj}")
print(f"Endereço: {empresa.get_endereco_completo()}")
```

### 3. Vinculação com Contatos

```python
# Criar/buscar contato
contato, created = Contato.objects.get_or_create(
    telefone="+5511987654321",
    defaults={'nome': "João Silva"}
)

# Vincular à empresa  
empresa.adicionar_contato(contato)

# Listar contatos da empresa
for contato in empresa.get_contatos_ativos():
    print(f"Contato: {contato.nome_contato} - {contato.telefone}")
```

### 4. Usando Metadados

```python
# Armazenar informações personalizadas
empresa.atualizar_metadados("codigo_interno", "EMP-001")
empresa.atualizar_metadados("setor_contato", "Vendas")
empresa.atualizar_metadados("observacoes_comerciais", [
    "Cliente preferencial",
    "Desconto especial aprovado"
])

# Recuperar metadados
codigo = empresa.get_metadados("codigo_interno")
setor = empresa.get_metadados("setor_contato", "Não informado")
```

## Integração com Dados de Conversa

O modelo foi desenhado para trabalhar com os dados extraídos de conversas no formato JSON especificado:

```python
def processar_dados_empresa(dados_conversa):
    """
    Processa dados extraídos de uma conversa e cria/atualiza empresa.
    """
    dados_empresa = dados_conversa.get("dados_empresa", {})
    endereco_empresa = dados_conversa.get("endereco_empresa", {})
    
    empresa = Empresa()
    
    # Mapear dados básicos
    empresa.nome_fantasia = dados_empresa.get("nome_fantasia", "")
    empresa.razao_social = dados_empresa.get("razao_social")
    empresa.cnpj = dados_empresa.get("cnpj")
    empresa.telefone = dados_empresa.get("telefone")
    empresa.site = dados_empresa.get("site")
    empresa.ramo_atividade = dados_empresa.get("ramo_atividade")
    empresa.observacoes = dados_empresa.get("observacoes")
    
    # Mapear endereço
    empresa.cep = endereco_empresa.get("cep")
    empresa.logradouro = endereco_empresa.get("logradouro")
    empresa.numero = endereco_empresa.get("numero")
    empresa.complemento = endereco_empresa.get("complemento")
    empresa.bairro = endereco_empresa.get("bairro")
    empresa.cidade = endereco_empresa.get("cidade")
    empresa.uf = endereco_empresa.get("uf")
    empresa.pais = endereco_empresa.get("pais")
    
    empresa.save()  # Validações e formatações automáticas
    return empresa
```

## Buscas Comuns

```python
# Empresas ativas
empresas_ativas = Empresa.objects.filter(ativo=True)

# Por ramo de atividade
empresas_tech = Empresa.objects.filter(ramo_atividade__icontains="tecnologia")

# Por cidade
empresas_sp = Empresa.objects.filter(cidade="São Paulo")

# Com contatos relacionados (otimizada)
empresas_com_contatos = Empresa.objects.prefetch_related('contatos')

# Por CNPJ
empresa = Empresa.objects.filter(cnpj="12.345.678/0001-99").first()
```

## Admin do Django

O modelo está configurado com `verbose_name` e `verbose_name_plural` para exibição correta no Django Admin. Os campos possuem `help_text` descritivos para facilitar o uso.

## Considerações Técnicas

- **Performance**: Use `prefetch_related('contatos')` ao buscar empresas com seus contatos
- **Validações**: Todas as validações são executadas no `save()` e `clean()`
- **Formatação**: Dados são formatados automaticamente no `save()`
- **Flexibilidade**: Campo `metadados` permite extensão sem alteração do modelo
- **Relacionamento**: Many-to-Many permite que um contato trabalhe em múltiplas empresas

## Arquivos Relacionados

- **Modelo**: `src/smart_core_assistant_painel/app/ui/oraculo/models.py`
- **Migração**: `src/smart_core_assistant_painel/app/ui/oraculo/migrations/0013_empresa.py`
- **Exemplo de Uso**: `exemplo_uso_model_empresa.py`
