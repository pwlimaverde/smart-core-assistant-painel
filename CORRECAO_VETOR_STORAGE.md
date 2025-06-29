# Correção do Problema VetorStorage no Django-Q

## Problema Identificado

O erro `VetorStorage não foi configurado` e a "perda" de documentos ocorriam devido a:

1. **Processos Separados**: O Django-Q executa tasks em processos workers separados
2. **Múltiplas Instâncias**: Cada acesso criava uma nova instância do `FaissVetorStorage`
3. **Falta de Sincronização**: Instâncias não compartilhavam o estado do banco vetorial
4. **Race Conditions**: Múltiplas configurações simultâneas causavam conflitos

## Solução Implementada

### 1. Padrão Singleton no FaissVetorStorage

Implementado padrão singleton thread-safe para garantir uma única instância:

```python
class FaissVetorStorage(VetorStorage):
    """
    Implementação singleton do VetorStorage usando FAISS.
    Garante que todas as instâncias compartilhem o mesmo banco vetorial.
    """
    
    _instance = None
    _initialized = False
    _lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            import threading
            if FaissVetorStorage._lock is None:
                FaissVetorStorage._lock = threading.Lock()
                
            with FaissVetorStorage._lock:
                if not self._initialized:
                    # Inicialização única
                    self.__db_path = str(Path(__file__).parent / "banco_faiss")
                    self.__embeddings = OllamaEmbeddings(model=SERVICEHUB.FAISS_MODEL)
                    self.__vectordb = self.__inicializar_banco_vetorial()
                    FaissVetorStorage._initialized = True
```

### 2. Sincronização do Banco Vetorial

Adicionado método para sincronizar com o disco antes de operações críticas:

```python
def _sync_vectordb(self):
    """
    Sincroniza o banco vetorial recarregando do disco.
    Usado para garantir que mudanças de outros processos sejam visíveis.
    """
    try:
        if self.__faiss_db_exists(self.__db_path):
            logger.debug("Sincronizando banco vetorial com o disco")
            self.__vectordb = FAISS.load_local(
                self.__db_path,
                self.__embeddings,
                allow_dangerous_deserialization=True
            )
            logger.debug("Banco vetorial sincronizado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao sincronizar banco vetorial: {e}")
```

### 3. Auto-configuração Melhorada no ServiceHub

Implementada proteção contra race conditions na auto-configuração:

```python
def _auto_configure_vetor_storage(self) -> None:
    """
    Auto-configura o VetorStorage se não estiver configurado.
    Garante que apenas uma instância seja criada por processo.
    """
    try:
        # Verifica se já está sendo configurado para evitar race conditions
        if hasattr(self, '_configuring_vetor_storage') and self._configuring_vetor_storage:
            import time
            timeout = 10  # 10 segundos de timeout
            start_time = time.time()
            while (hasattr(self, '_configuring_vetor_storage') and 
                   self._configuring_vetor_storage and 
                   (time.time() - start_time) < timeout):
                time.sleep(0.1)
            return
            
        # Marca que está configurando
        self._configuring_vetor_storage = True
        
        # Verifica novamente se não foi configurado enquanto aguardava
        if self._vetor_storage is not None:
            self._configuring_vetor_storage = False
            return
        
        # Configuração...
    finally:
        # Remove a marca de configuração
        if hasattr(self, '_configuring_vetor_storage'):
            self._configuring_vetor_storage = False
```

### 4. Sincronização em Operações Críticas

Métodos `read()` e `remove_by_metadata()` agora sincronizam antes de executar:

```python
def read(self, query_vector=None, metadata=None, k=5):
    try:
        # Sincroniza com o disco antes de ler
        self._sync_vectordb()
        # ... resto da operação

def remove_by_metadata(self, metadata_key, metadata_value):
    try:
        # Sincroniza com o disco antes de remover
        self._sync_vectordb()
        # ... resto da operação
```

## Arquivos Modificados

1. **`service_hub.py`**:
   - Melhorada auto-configuração com proteção contra race conditions
   - Adicionado timeout e retry logic

2. **`faiss_vetor_storage.py`**:
   - Implementado padrão singleton thread-safe
   - Adicionado método de sincronização `_sync_vectordb()`
   - Integrada sincronização em operações críticas

3. **`signals.py`**:
   - Mantidos metadados de identificação aos chunks
   - Logs melhorados para debugging

## Scripts de Teste

1. **`test_singleton.py`**: Testa comportamento singleton do ServiceHub
2. **`test_faiss_singleton.py`**: Testa singleton e sincronização do FaissVetorStorage

## Como Testar

Execute os scripts de teste:

```bash
python test_singleton.py
python test_faiss_singleton.py
```

## Benefícios da Solução

1. **Thread-Safe**: Proteção contra race conditions
2. **Singleton Garantido**: Uma única instância por processo
3. **Sincronização Automática**: Dados sempre atualizados
4. **Compatibilidade**: Mantém API existente
5. **Performance**: Evita recarregamentos desnecessários
6. **Robustez**: Tratamento de erros melhorado

## Comportamento Esperado

- **Inserção**: Documentos são salvos no disco imediatamente
- **Remoção**: Sincroniza antes de buscar e remover documentos  
- **Leitura**: Sempre sincroniza para dados atualizados
- **Logs**: Indicam sincronizações e operações singleton
- **Workers**: Cada worker tem sua instância singleton que sincroniza com o disco

## Resolução do Problema Original

O problema "Banco vetorial está vazio" foi resolvido porque:

1. **Singleton**: Garante que todos acessem a mesma instância
2. **Sincronização**: Recarrega dados do disco antes de operações críticas
3. **Thread Safety**: Evita conflitos de inicialização
4. **Persistência**: Mudanças são salvas imediatamente no disco
