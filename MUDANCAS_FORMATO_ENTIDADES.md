# Novo Formato de Entidades Extraídas

## Resumo das Alterações

O formato das entidades extraídas foi simplificado para ser mais direto e intuitivo:

### Formato Anterior (Removido)
```python
entidades_extraidas = [
    {"tipo": "pessoa", "valor": "João Silva"},
    {"tipo": "email", "valor": "joao@email.com"},
    {"tipo": "telefone", "valor": "+5511999999999"}
]
```

### Formato Atual (Único Suportado)
```python
entidades_extraidas = [
    {"pessoa": "João Silva"},
    {"email": "joao@email.com"},
    {"telefone": "+5511999999999"}
]
```

## Arquivos Modificados

### 1. `models.py`
- **Método `extrair_entidades_formatadas`**: Simplificado para processar apenas o formato `{"tipo": "valor"}`
- **Método `carregar_historico_mensagens`**: Atualizado para processar entidades no novo formato
- **Campo `entidades_extraidas`**: Documentação atualizada para refletir o formato único

### 2. `exemplo_entidades_padronizadas.py`
- Exemplos atualizados para mostrar apenas o novo formato
- Remoção de todas as referências ao formato antigo
- Testes de validação simplificados

### 3. `exemplo_novo_formato_entidades.py`
- Arquivo com exemplos específicos do formato único
- Demonstrações de uso com LLMs
- Guias de implementação

## Principais Mudanças no Código

### Método `extrair_entidades_formatadas`
```python
def extrair_entidades_formatadas(self):
    """
    Comportamento simplificado:
    1. Processa apenas formato: {"pessoa": "João Silva"}
    2. Pega todos os valores de cada dicionário
    3. Retorna set com valores únicos
    """
    # Formato único: {"pessoa": "João Silva"} - pega todos os valores
    for chave, valor in entidade_dict.items():
        if valor and str(valor).strip():
            entidades.add(str(valor))
```

### Método `carregar_historico_mensagens`
```python
# Processamento simplificado para formato único
for entidade_dict in mensagem.entidades_extraidas:
    if isinstance(entidade_dict, dict):
        # Formato único: {"pessoa": "João Silva"}
        for chave, valor in entidade_dict.items():
            if valor and str(valor).strip():
                entidades_extraidas.add(str(valor))
```

## Benefícios da Mudança

1. **Simplicidade**: O formato `{"pessoa": "João Silva"}` é direto e intuitivo
2. **Menos código**: Reduz complexidade de processamento
3. **Clareza**: Sem ambiguidade sobre qual formato usar
4. **Consistência**: Um único padrão em todo o sistema
5. **Performance**: Processamento mais rápido sem verificações de compatibilidade

## Como Usar

### Formato Único (Obrigatório)
```python
entidades = [
    {"pessoa": "João Silva"},
    {"email": "joao@email.com"},
    {"telefone": "+5511999999999"},
    {"produto": "Smartphone"},
    {"urgencia": "alta"}
]
```

### Exemplos Práticos
```python
# Criar mensagem com entidades
mensagem = Mensagem.objects.create(
    atendimento=atendimento,
    conteudo="Olá, sou João Silva...",
    entidades_extraidas=[
        {"nome": "João Silva"},
        {"email": "joao@email.com"}
    ]
)

# Extrair entidades
entidades = mensagem.extrair_entidades_formatadas()
# Retorna: {'João Silva', 'joao@email.com'}
```

## Testes

Execute os exemplos:
```bash
python exemplo_novo_formato_entidades.py
python exemplo_entidades_padronizadas.py
```

## Observações Importantes

- **BREAKING CHANGE**: O formato antigo não é mais suportado
- **Migração necessária**: Código existente deve ser atualizado
- A extração de entidades retorna sempre os valores (não os tipos)
- Logs de warning são gerados para formatos incorretos
- Todos os valores de um dicionário são extraídos como entidades
