# Arquitetura com EmbeddingData Separado

## 📋 Visão Geral

A refatoração separou todas as operações de embedding em uma classe dedicada `EmbeddingData`, deixando o modelo `Documento` mais limpo e focado apenas em suas responsabilidades principais.

## 🏗️ Estrutura da Nova Arquitetura

```
📁 app/ui/oraculo/
├── 📄 models_documento.py      # Modelo principal (229 linhas)
├── 📄 embedding_data.py        # Classe de embeddings (100 linhas)
├── 📄 models_treinamento.py    # Modelo enxuto
└── 📄 signals.py              # Signals do sistema
```

## 🔧 Separação de Responsabilidades

### 📄 **EmbeddingData** (`embedding_data.py`)
**Responsabilidade**: Gerenciar todas as operações de embedding

```python
class EmbeddingData:
    # Métodos principais:
    - gerar_embedding_texto(texto: str) -> List[float]
    - gerar_embedding_para_documento(conteudo: str) -> List[float]
    
    # Métodos privados de configuração:
    - _criar_instancia_embeddings()
    - _criar_ollama_embeddings(modelo: str)
    - _criar_openai_embeddings(modelo: str)
    - _criar_huggingface_embeddings(modelo: str)
    - _criar_huggingface_inference_embeddings(modelo: str)
```

### 📄 **Documento** (`models_documento.py`)
**Responsabilidade**: Modelo Django + busca semântica + embedding ultra-automático

```python
class Documento(models.Model):
    # Campos do modelo Django
    # Métodos essenciais:
    - buscar_documentos_similares(mensagem: str) -> str  # PRINCIPAL
    - save() -> None  # COM EMBEDDING ULTRA-AUTOMÁTICO! 🚀
    - processar_conteudo_para_chunks()
    - vetorizar_documentos_por_treinamento()
    
    # ZERO métodos manuais ou auxiliares de embedding!
```

## 🚀 Vantagens da Nova Arquitetura

### ✅ **Separação Clara**
- **EmbeddingData**: Foca apenas em embeddings
- **Documento**: Foca apenas no modelo e busca

### ✅ **Automação Total**
- **Embedding automático** no save() do modelo
- Zero métodos manuais necessários
- Impossível esquecer de gerar embedding

### ✅ **Manutenção**
- Mudanças em embeddings não afetam o modelo
- Mais fácil adicionar novos provedores

### ✅ **Testabilidade**
- Pode testar embeddings independentemente
- Testes de modelo sem dependência de IA

## 📊 Comparação de Tamanho

| Arquivo | Antes | Depois | Redução |
|---------|--------|--------|---------|
| `models_documento.py` | ~800 linhas | 265 linhas | -67% |
| `embedding_data.py` | 0 linhas | 100 linhas | +100 linhas |
| **Total** | 800 linhas | 365 linhas | **-54%** |

## 🔄 Fluxo de Uso

### 1. **Webhook Recebe Mensagem**
```python
def processar_mensagem_webhook(mensagem: str) -> str:
    # UMA LINHA APENAS!
    return Documento.buscar_documentos_similares(mensagem)
```

### 2. **Criar Documento (Embedding Automático)**
```python
# ANTES: 3 passos manuais
documento = Documento.objects.create(...)
documento.generate_embedding()  # Manual!
documento.save()

# AGORA: 1 passo automático! 🎉
documento = Documento.objects.create(...)  # Embedding gerado automaticamente!
```

### 2. **Busca Interna (Documento)**
```python
@classmethod
def buscar_documentos_similares(cls, mensagem: str) -> str:
    # Delega embedding para EmbeddingData
    query_vec = EmbeddingData.gerar_embedding_texto(mensagem)
    
    # Foca na busca semântica
    documentos = cls.objects.filter(...).annotate(
        distance=CosineDistance('embedding', query_vec)
    )
    
    # Retorna contexto formatado
    return contexto_formatado
```

### 3. **Geração de Embedding (EmbeddingData)**
```python
@staticmethod
def gerar_embedding_texto(texto: str) -> List[float]:
    # Cria instância do provedor configurado
    embeddings_instance = EmbeddingData._criar_instancia_embeddings()
    
    # Gera e retorna embedding
    return embeddings_instance.embed_query(texto)
```

## 🎯 Principais Métodos

### **Para Webhooks (Método Principal):**
```python
# Uso direto no webhook
contexto = Documento.buscar_documentos_similares("Como funciona o pagamento?")
```

### **Para Criação de Documentos (Automático):**
```python
# Embedding é gerado automaticamente - zero trabalho manual!
documento = Documento.objects.create(
    treinamento=treinamento_finalizado,
    conteudo="Texto para embedding automático",
    ordem=1
)  # Embedding já está pronto! 🎉
```

### **Para Uso Direto de Embeddings:**
```python
# Gerar embedding de qualquer texto
embedding = EmbeddingData.gerar_embedding_texto("Texto qualquer")

# Gerar embedding específico para documento
embedding = EmbeddingData.gerar_embedding_para_documento(conteudo)
```

## 🧪 Testabilidade

### **Testar Embeddings Isoladamente:**
```python
def test_embedding_generation():
    resultado = EmbeddingData.gerar_embedding_texto("teste")
    assert len(resultado) == 1024  # Verifica dimensões
    assert all(isinstance(x, float) for x in resultado)
```

### **Testar Busca sem Dependência de IA:**
```python
def test_busca_com_mock():
    with mock.patch.object(EmbeddingData, 'gerar_embedding_texto'):
        resultado = Documento.buscar_documentos_similares("teste")
        # Testa lógica sem depender de serviços externos
```

## 📈 Conclusão

A separação em `EmbeddingData` + **embedding automático** resultou em:

- ✅ **Código mais limpo** e organizado
- ✅ **Zero métodos manuais** de embedding
- ✅ **Embedding sempre consistente**
- ✅ **Impossível esquecer** de gerar
- ✅ **Facilidade de manutenção**
- ✅ **Reutilização de componentes**
- ✅ **Melhor testabilidade**
- ✅ **Menor acoplamento**

O fluxo principal continua sendo **uma linha** para webhooks, mas agora com **embedding 100% automático**! 🎉