# Admin do Modelo Empresa

O modelo `Empresa` foi adicionado ao Django Admin com uma interface rica e funcional.

## Recursos do Admin

### Interface Principal
- **Lista**: Mostra nome fantasia, razão social, CNPJ, localização, ramo de atividade, total de contatos e status
- **Filtros**: Por status ativo, UF, cidade, ramo de atividade e datas
- **Busca**: Nome fantasia, razão social, CNPJ, telefone, cidade e ramo de atividade
- **Ordenação**: Por nome fantasia (padrão)

### Formulário de Edição

#### Seções Organizadas
1. **Informações Básicas**: Nome fantasia, razão social, CNPJ e status ativo
2. **Contatos**: Telefone, site e ramo de atividade
3. **Endereço**: Campos organizados logicamente (CEP/UF, Logradouro, Número/Complemento, etc.)
4. **Relacionamentos**: Interface melhorada para vincular contatos (filter_horizontal)
5. **Observações**: Campo de texto livre (colapsável)
6. **Metadados**: Campo JSON para dados personalizados (colapsável)
7. **Informações do Sistema**: Datas e endereço completo formatado (colapsável, readonly)

### Campos Especiais

#### Campos Somente Leitura
- `data_cadastro`: Data de criação automática
- `ultima_atualizacao`: Data de última modificação automática
- `get_endereco_completo_display`: Endereço formatado completo
- `total_contatos`: Número de contatos vinculados

#### Interface Otimizada
- `filter_horizontal`: Interface drag-and-drop para relacionamento com contatos
- `prefetch_related`: Consultas otimizadas para melhor performance

### Actions (Ações em Lote)

#### Ações de Status
- **Marcar como ativa**: Ativa empresas selecionadas
- **Marcar como inativa**: Inativa empresas selecionadas

#### Exportação
- **Exportar para CSV**: Gera arquivo CSV com dados completos das empresas selecionadas
  - Inclui todos os campos principais
  - Endereço completo formatado
  - Contagem de contatos relacionados
  - Formatação brasileira de datas

### Métodos Display Personalizados

```python
@admin.display(description='Total de Contatos')
def total_contatos(self, obj: Empresa) -> "Any":
    """Conta contatos vinculados à empresa"""
    return obj.contatos.count()

@admin.display(description='Endereço Completo')
def get_endereco_completo_display(self, obj: Empresa) -> str:
    """Mostra endereço formatado no admin"""
    return obj.get_endereco_completo() or "-"
```

## Admin do Contato Atualizado

O admin do `Contato` também foi aprimorado para mostrar relacionamentos com empresas:

### Novas Funcionalidades
- **Coluna**: `total_empresas` mostra quantas empresas estão vinculadas ao contato
- **Filtro**: Adicionado filtro por status ativo
- **Performance**: Consultas otimizadas com `prefetch_related('empresas')`

## Como Usar

### 1. Acessar o Admin
```
http://localhost:8000/admin/oraculo/empresa/
```

### 2. Criar Nova Empresa
1. Clique em "Adicionar Empresa"
2. Preencha pelo menos o "Nome Fantasia" (obrigatório)
3. Outros campos são opcionais
4. Use a seção "Relacionamentos" para vincular contatos existentes
5. Dados como CNPJ e CEP são formatados automaticamente ao salvar

### 3. Vincular Contatos
1. Na edição da empresa, vá para "Relacionamentos"
2. Use a interface de seleção múltipla para vincular contatos
3. Ou vá ao admin do contato e veja as empresas relacionadas

### 4. Exportar Dados
1. Selecione as empresas desejadas na lista
2. Escolha a ação "Exportar dados das empresas selecionadas (CSV)"
3. O arquivo será baixado automaticamente

### 5. Buscar e Filtrar
- **Busca rápida**: Digite na barra de busca (nome, CNPJ, cidade, etc.)
- **Filtros laterais**: Use para filtrar por localização, status ou datas
- **Ordenação**: Clique nos cabeçalhos das colunas

## Validações Automáticas

O admin herda todas as validações do modelo:
- **CNPJ**: Validação e formatação automática
- **CEP**: Validação e formatação automática
- **Campos obrigatórios**: Nome fantasia é obrigatório
- **Formatação**: UF em maiúscula, telefones formatados

## Exemplos de Uso

### Busca Avançada
```
# No campo de busca do admin:
"Microsoft"           # Busca por nome
"12.345.678/0001-99" # Busca por CNPJ
"São Paulo"          # Busca por cidade
"tecnologia"         # Busca por ramo de atividade
```

### Filtros Combinados
- Filtrar por UF="SP" + Cidade="São Paulo" + Ativo=Sim
- Filtrar por Ramo de Atividade="Tecnologia" + Data de Cadastro="Últimos 7 dias"

### Gerenciamento em Lote
1. Selecione múltiplas empresas
2. Use "Marcar como inativa" para desativar várias de uma vez
3. Use "Exportar dados" para gerar relatório das selecionadas

## Considerações Técnicas

### Performance
- Consultas otimizadas com `select_related()` e `prefetch_related()`
- Paginação configurada (25 itens por página)
- Índices automáticos nos campos de busca

### Segurança
- Validações do modelo são aplicadas no admin
- Campos sensíveis podem ser marcados como readonly
- Actions têm mensagens de confirmação

### Extensibilidade
- Fácil adição de novos campos no modelo (migração automática)
- Metadados JSON permitem dados personalizados sem migração
- Actions personalizadas podem ser facilmente adicionadas

## Próximas Melhorias

### Possíveis Adições Futuras
- Inline para mostrar atendimentos relacionados via contatos
- Gráficos de distribuição geográfica
- Importação de dados via CSV
- Auditoria de mudanças
- Duplicação inteligente de empresas
