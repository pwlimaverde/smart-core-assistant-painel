# 📋 Implementação: Processamento Automático de Entidades do Cliente

## 🎯 Objetivo
Implementar processamento automático das entidades extraídas (`entity_types`) para atualizar dados do cliente no modelo Django de forma inteligente e eficiente.

## ✅ Funcionalidades Implementadas

### 1. **Função Principal: `_processar_entidades_cliente()`**
**Localização:** `views.py` (linha ~517)

**Responsabilidades:**
- Analisa `entity_types` extraídas pela IA
- Atualiza automaticamente o campo `nome` do cliente quando encontra entidade "cliente"
- Salva outras entidades relevantes nos `metadados` do cliente
- Evita duplicatas e sobrescrições desnecessárias

**Entidades Suportadas para Metadados:**
```python
entidades_metadados = {
    'contato', 'email', 'telefone', 'cpf', 'cnpj', 'endereco', 
    'cidade', 'estado', 'cep', 'rg', 'data_nascimento', 'profissao'
}
```

### 2. **Função de Solicitação: `_solicitar_dados_cliente_se_necessario()`**
**Localização:** `views.py` (linha ~606)

**Responsabilidades:**
- Verifica se cliente não tem nome cadastrado
- Evita spam verificando mensagens recentes do bot
- Gera automaticamente mensagem de solicitação de dados
- Cria mensagem do bot no atendimento

**Status:** Implementada mas **desabilitada por padrão** (linha comentada)

### 3. **Função Auxiliar: `_gerar_mensagem_solicitacao_dados()`**
**Localização:** `views.py` (linha ~680)

**Responsabilidades:**
- Gera mensagem personalizada baseada nos dados faltantes
- Verifica quais informações já existem
- Retorna texto amigável para solicitar dados

## 🔄 Fluxo de Execução

```mermaid
graph TD
    A[Nova Mensagem] --> B[Análise de Entidades IA]
    B --> C[_processar_entidades_cliente]
    C --> D{Entidade "cliente"?}
    D -->|Sim| E[Atualizar campo nome]
    D -->|Não| F{Outras entidades?}
    F -->|Sim| G[Salvar em metadados]
    E --> H[Salvar no banco]
    G --> H
    H --> I{Solicitação ativada?}
    I -->|Sim| J[_solicitar_dados_cliente_se_necessario]
    I -->|Não| K[Fim]
    J --> K
```

## 📊 Exemplos de Uso

### Exemplo 1: Nome do Cliente Detectado
```python
entity_types = [
    {"cliente": "João Silva"},
    {"email": "joao@email.com"},
    {"telefone": "(11) 99999-9999"}
]
```
**Resultado:**
- `cliente.nome = "João Silva"`
- `cliente.metadados = {"email": "joao@email.com", "telefone": "(11) 99999-9999"}`

### Exemplo 2: Apenas Dados Complementares
```python
entity_types = [
    {"cpf": "123.456.789-00"},
    {"endereco": "Rua das Flores, 123"}
]
```
**Resultado:**
- `cliente.nome` permanece inalterado
- `cliente.metadados` atualizado com CPF e endereço

## 🚀 Como Ativar

### 1. Processamento de Entidades (Já Ativo)
O processamento é chamado automaticamente em `_analisar_conteudo_mensagem()`:
```python
_processar_entidades_cliente(mensagem, resultado_analise.entity_types)
```

### 2. Solicitação Automática de Dados (Opcional)
Para ativar, descomente a linha em `_analisar_conteudo_mensagem()`:
```python
# _solicitar_dados_cliente_se_necessario(mensagem)  # ← Descomente esta linha
```

## ⚙️ Configurações

### Validações de Nome
- Mínimo 2 caracteres
- Só atualiza se estiver vazio ou novo nome for mais completo
- Remove espaços em branco

### Prevenção de Spam
- Verifica últimas 5 mensagens do bot
- Não solicita dados se já foi pedido recentemente
- Palavras-chave de detecção: `['nome', 'como posso chamá', 'qual seu nome', 'poderia me informar', 'dados', 'informações']`

### Performance
- Usa `update_fields` para economia no banco
- Logs informativos para debugging
- Tratamento de erros robusto (não interrompe fluxo)

## 🛡️ Segurança e Robustez

1. **Graceful Degradation:** Erros não interrompem o fluxo principal
2. **Validação de Dados:** Verificações antes de salvar
3. **Logs Detalhados:** Facilita debugging e monitoramento
4. **Prevenção de Duplicatas:** Só atualiza quando necessário

## 📝 Logs Gerados

```log
INFO: Nome do cliente atualizado para: João Silva
INFO: Metadado email atualizado para cliente: joao@email.com
INFO: Cliente +5511999999999 atualizado com sucesso
INFO: Cliente +5511999999999 ainda sem nome - considerar solicitar dados
INFO: Solicitação de dados enviada para cliente +5511999999999
```

## 🔮 Extensões Futuras

1. **Validação Avançada:** CPF, CNPJ, email format
2. **Normalização:** Telefone, CEP, formato de nomes
3. **Integrações:** APIs de validação de dados
4. **Analytics:** Métricas de completude de dados
5. **Interface Admin:** Visualização de dados coletados

## 📖 Arquivos Criados/Modificados

- ✅ `views.py` - Funções principais implementadas
- ✅ `exemplo_processamento_entidades_cliente.py` - Documentação e exemplos
- ✅ Import `timezone` adicionado
- ✅ Type hints configurados

**Status:** ✅ **IMPLEMENTADO E PRONTO PARA USO**
