# PydanticModelFactory - Entidades Fixas para Cadastro

## Resumo das Melhorias Implementadas

Este documento descreve as melhorias realizadas na classe `PydanticModelFactory` para incluir **entidades fixas** destinadas ao cadastro estruturado no banco de dados.

## Principais Alterações

### 1. Nova Seção de Entidades Fixas

Foi adicionado o método `_generate_fixed_entities_section()` que inclui três categorias principais de dados para cadastro:

#### 🏢 **CONTATO** 
Dados da pessoa que participou da conversa:
- `nome_contato`: Nome completo do contato
- `cargo_contato`: Cargo profissional
- `departamento_contato`: Departamento/setor
- `email_contato`: E-mail de contato
- `rg_contato`: Número do RG
- `observacoes_contato`: Informações adicionais

#### 🏪 **CLIENTE**
Dados da empresa ou pessoa física cliente:
- `tipo_cliente`: pessoa física/jurídica
- `nome_fantasia_cliente`: Nome comercial
- `razao_social_cliente`: Razão social legal
- `cnpj_cliente`/`cpf_cliente`: Documentos
- `telefone_cliente`: Telefone corporativo
- `site_cliente`: Website
- `ramo_atividade_cliente`: Setor de atuação
- Dados de endereço completo (CEP, logradouro, número, etc.)
- `observacoes_cliente`: Informações adicionais

#### 📞 **ATENDIMENTO**
Dados sobre a qualidade do atendimento:
- `tags_atendimento`: Tags categorizadoras
- `avaliacao_atendimento`: Nota de 1 a 5
- `feedback_atendimento`: Comentários qualitativos

### 2. Documentação Aprimorada

#### Estrutura da Documentação:
1. **INTENTS** - Intenções do usuário (dinâmico)
2. **ENTIDADES DINÂMICAS** - Informações específicas da conversa (dinâmico)  
3. **ENTIDADES FIXAS** - Dados para cadastro no banco (fixo)
4. **EXEMPLOS** - Casos práticos melhorados

#### Princípios Atualizados:
- **Conservador** para entidades dinâmicas
- **Mais liberal** para entidades fixas (dados de cadastro)
- Priorização da extração de dados estruturados para o banco

### 3. Exemplos Melhorados

Os exemplos agora demonstram:
- Extração simultânea de entidades dinâmicas e fixas
- Distinção entre pessoa física e jurídica
- Captura de dados completos de contato e cliente
- Avaliação e feedback de atendimento

## Como Usar

```python
from pydantic_model_factory import PydanticModelFactory

# JSONs dinâmicos (configuráveis)
intent_json = "..." # Seus intent_types
entity_json = "..." # Seus entity_types

# Criar o modelo (entidades fixas são incluídas automaticamente)
PydanticModel = PydanticModelFactory.create_pydantic_model(
    intent_json, 
    entity_json
)

# A documentação completa é gerada automaticamente
print(PydanticModel.__doc__)

# Usar o modelo normalmente
instance = PydanticModel(
    intent=[{"type": "saudacao", "value": "Olá"}],
    entities=[
        {"type": "nome_contato", "value": "João Silva"},
        {"type": "nome_fantasia_cliente", "value": "Microsoft"}
    ]
)
```

## Benefícios

### ✅ **Para a LLM:**
- Instruções claras sobre dados de cadastro prioritários
- Exemplos práticos com dados estruturados
- Diferenciação entre extração conservadora vs liberal

### ✅ **Para o Sistema:**
- Captura estruturada de dados de contatos e clientes
- Padronização de campos de cadastro
- Facilita integração com banco de dados

### ✅ **Para Desenvolvimento:**
- Manutenção das configurações dinâmicas existentes
- Adição transparente das entidades fixas
- Backward compatibility mantida

## Teste

Execute `test_documentation_generation.py` para ver a documentação completa gerada dinamicamente:

```bash
python test_documentation_generation.py
```

O teste demonstra:
- Geração completa da documentação
- Criação de instâncias do modelo
- Métodos de consulta por tipo de entidade

## Conclusão

A implementação mantém a flexibilidade original da factory enquanto adiciona capacidades estruturadas de cadastro, oferecendo o melhor dos dois mundos: configuração dinâmica para regras de negócio específicas e estrutura fixa para dados essenciais do sistema.
