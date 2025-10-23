# Análise Estrutural dos Models Atuais

**Data:** Janeiro 2025  
**Objetivo:** Revisar estrutura dos models Django existentes antes da criação do app de integração Notion  
**Princípio:** Desacoplamento total - models principais NÃO devem ter referências ao Notion

---

## 1. Análise dos Models por App

### 1.1. App: `clientes`

#### Modelo: `Contato`

**Status:** ✅ **Estrutura adequada - Nenhum ajuste necessário**

```python
class Contato(models.Model):
    id: AutoField (PK)
    telefone: CharField(20, unique, validators, help_text) ✓
    nome_contato: CharField(100, null/blank) ✓
    email: EmailField(254, null/blank) ✓
    nome_perfil_whatsapp: CharField(100, null/blank) ✓
    data_cadastro: DateTimeField(auto_now_add) ✓
    ultima_interacao: DateTimeField(auto_now) ✓
    ativo: BooleanField(default=True) ✓
    metadados: JSONField(dict, default={}) ✓
```

**Análise:**
- ✅ Validação de telefone adequada
- ✅ Normalização automática para +55 (Brasil)
- ✅ Campos essenciais presentes
- ✅ Metadados flexível para expansão futura
- ✅ Timestamps automáticos
- ✅ db_table customizada (`oraculo_contato`)

**Relacionamentos:**
- → `Cliente` (ManyToMany reverso)
- → `Atendimento` (OneToMany reverso)

**Observações:**
- Campo `telefone` é chave natural para sincronização
- `metadados` pode armazenar informações temporárias da sincronização se necessário

---

#### Modelo: `Cliente`

**Status:** ✅ **Estrutura adequada - Nenhum ajuste necessário**

```python
class Cliente(models.Model):
    id: AutoField (PK)
    nome_fantasia: CharField(200, obrigatório) ✓
    razao_social: CharField(200, null/blank) ✓
    tipo: CharField(20, choices=['fisica','juridica']) ✓
    cnpj: CharField(18, validators, null/blank) ✓
    cpf: CharField(14, validators, null/blank) ✓
    telefone: CharField(20, validators, null/blank) ✓
    site: URLField(null/blank) ✓
    ramo_atividade: CharField(200, null/blank) ✓
    observacoes: TextField(null/blank) ✓
    # Endereço completo
    cep: CharField(10, validators, null/blank) ✓
    logradouro: CharField(200, null/blank) ✓
    numero: CharField(10, null/blank) ✓
    complemento: CharField(100, null/blank) ✓
    bairro: CharField(100, null/blank) ✓
    cidade: CharField(100, null/blank) ✓
    uf: CharField(2, null/blank) ✓
    pais: CharField(50, default='Brasil') ✓
    contatos: ManyToManyField(Contato) ✓
    data_cadastro: DateTimeField(auto_now_add) ✓
    ultima_atualizacao: DateTimeField(auto_now) ✓
    ativo: BooleanField(default=True) ✓
    metadados: JSONField(dict, default={}) ✓
```

**Análise:**
- ✅ Validações robustas (CNPJ, CPF, CEP, telefone)
- ✅ Formatação automática ao salvar
- ✅ Método `get_endereco_completo()` útil para Notion
- ✅ Métodos helper para gerenciar contatos
- ✅ Estrutura de endereço completa
- ✅ Campo `nome_fantasia` obrigatório (bom para Notion title)

**Relacionamentos:**
- ↔ `Contato` (ManyToMany)
- → `Atendimento` (via Contato)

**Observações:**
- Relação M:N com Contato será mapeada no Notion via relation
- `metadados` flexível para dados adicionais

---

### 1.2. App: `operacional`

#### Modelo: `Departamento`

**Status:** ⚠️ **Pequeno ajuste recomendado**

```python
class Departamento(models.Model):
    id: AutoField (PK)
    nome: CharField(100, unique) ✓
    slug: SlugField(120, unique, auto-gerado) ✓
    descricao: TextField(null/blank) ✓
    ativo: BooleanField(default=True) ✓
    configuracoes: JSONField(dict, default={}) ✓
    data_criacao: DateTimeField(auto_now_add) ✓
    metadados: JSONField(dict, default={}) ✓
```

**Análise:**
- ✅ Estrutura simples e eficaz
- ✅ Slug auto-gerado útil para URLs
- ⚠️ Índice composto `[ativo, nome]` pode ser otimizado
- ✅ Separação clara: configurações vs metadados

**Relacionamentos:**
- → `AtendenteHumano` (OneToMany)
- → `WhatsAppInstance` (OneToMany)
- → `Atendimento` (OneToMany)

**Recomendação:**
- ✅ Estrutura adequada, nenhum ajuste crítico necessário
- 💡 Considerar adicionar campo `ordem` para ordenação customizada (opcional)

---

#### Modelo: `AtendenteHumano`

**Status:** ✅ **Estrutura adequada - Ajuste menor sugerido**

```python
class AtendenteHumano(models.Model):
    id: AutoField (PK)
    telefone: CharField(20, unique, null/blank, validators) ✓
    nome: CharField(100) ✓
    cargo: CharField(100) ✓
    departamento: ForeignKey(Departamento, null, SET_NULL) ✓
    email: EmailField(null/blank) ✓
    usuario: OneToOneField(User, null, SET_NULL) ✓
    usuario_sistema: CharField(50, null/blank) ✓
    ativo: BooleanField(default=True) ✓
    disponivel: BooleanField(default=True) ✓
    max_atendimentos_simultaneos: PositiveIntegerField(default=5) ✓
    data_ultima_atribuicao: DateTimeField(null/blank) ✓
    horario_trabalho: JSONField(dict, default={}) ✓
    especialidades: JSONField(list, default=[]) ✓
    metadados: JSONField(dict, default={}) ✓
    data_cadastro: DateTimeField(auto_now_add) ✓
    ultima_atividade: DateTimeField(auto_now) ✓
```

**Análise:**
- ✅ Estrutura completa para gestão de atendentes
- ✅ Métodos helper úteis: `get_atendimentos_ativos()`, `is_available()`, `current_load()`
- ✅ Normalização de telefone com +55
- ✅ Índices estratégicos para queries de disponibilidade
- ✅ Integração opcional com User do Django

**Relacionamentos:**
- → `Departamento` (ManyToOne)
- → `WhatsAppInstance` (OneToOne reverso)
- → `Atendimento` (OneToMany)

**Observações:**
- Campo `data_ultima_atribuicao` crucial para round-robin
- `especialidades` útil para filtros no Notion

---

#### Modelo: `WhatsAppInstance`

**Status:** ✅ **Não sincronizar - Segurança**

```python
class WhatsAppInstance(models.Model):
    id: AutoField (PK)
    departamento: ForeignKey(Departamento, CASCADE, null/blank) ✓
    phone_number: CharField(20, unique, validators, null/blank) ✓
    instance_id: CharField(100, unique, null/blank) ✓
    api_key: CharField(100, unique, validators) ⚠️ SENSÍVEL
    provider: CharField(30, choices, default='evolution') ✓
    owner: OneToOneField(AtendenteHumano, null, SET_NULL) ✓
    ativo: BooleanField(default=True) ✓
    metadados: JSONField(dict, default={}) ✓
    data_criacao: DateTimeField(auto_now_add) ✓
    ultima_validacao: DateTimeField(null/blank) ✓
```

**Análise:**
- ⚠️ **CONTÉM CREDENCIAIS SENSÍVEIS** (`api_key`)
- ✅ **DECISÃO: NÃO SINCRONIZAR COM NOTION**
- ✅ Métodos úteis: `validar_api_key()`, `selecionar_proximo_atendente()`

**Relacionamentos:**
- → `Departamento` (ManyToOne)
- → `AtendenteHumano` (OneToOne)

**Justificativa Exclusão:**
- Segurança: API keys não devem ser expostas
- Separação de responsabilidades: configuração técnica vs. gestão
- Desnecessário para equipe de atendimento

---

### 1.3. App: `atendimentos`

#### Modelo: `Atendimento`

**Status:** ⚠️ **Ajuste de nomenclatura recomendado**

```python
class Atendimento(models.Model):
    id: AutoField (PK)
    contato: ForeignKey(Contato, CASCADE) ✓
    departamento: ForeignKey(Departamento, null, SET_NULL) ✓
    status: CharField(20, choices=StatusAtendimento) ✓
    data_inicio: DateTimeField(auto_now_add) ⚠️
    data_fim: DateTimeField(null/blank) ⚠️
    data_ultima_mensagem: DateTimeField(null/blank) ✓
    assunto: CharField(200, null/blank) ✓
    prioridade: CharField(10, choices, default='normal') ✓
    atendente_humano: ForeignKey(AtendenteHumano, null, SET_NULL) ✓
    contexto_conversa: JSONField(dict, default={}) ✓
    historico_status: JSONField(list, default=[]) ✓
    tags: JSONField(list, default=[]) ✓
    avaliacao: IntegerField(1-5, null/blank) ✓
    feedback: TextField(null/blank) ✓
```

**Análise:**
- ✅ Estrutura sólida e completa
- ⚠️ **INCONSISTÊNCIA DE NOMENCLATURA:**
  - Campo atual: `data_inicio` 
  - Plano Notion: `data_abertura`
  - **Decisão:** Manter `data_inicio` (não quebra nada)
- ⚠️ **INCONSISTÊNCIA:**
  - Campo atual: `data_fim`
  - Plano Notion: `data_finalizacao`
  - **Decisão:** Manter `data_fim` (mais conciso)
- ✅ Enums bem definidos (`StatusAtendimento`)
- ✅ Métodos úteis para gestão

**Enums:**
```python
StatusAtendimento:
  - FILA = "fila"
  - EM_ATENDIMENTO = "em_atendimento"
  - AGUARDANDO_RETORNO = "aguardando_retorno"
  - RESOLVIDO = "resolvido"
  - CANCELADO = "cancelado"
```

**⚠️ DIVERGÊNCIA COM PLANO:**
- **Plano propõe:** `aguardando_inicial`, `em_andamento`, `aguardando_contato`, `aguardando_atendente`, `transferido`
- **Atual tem:** `fila`, `em_atendimento`, `aguardando_retorno`, `resolvido`, `cancelado`

**DECISÃO CRÍTICA:**
- ✅ **Manter enums atuais** (já em uso)
- ✅ Mapear no `notion_sync` app para nomenclatura Notion
- ✅ Atualizar plano para refletir enums reais

**Relacionamentos:**
- → `Contato` (ManyToOne)
- → `Departamento` (ManyToOne, optional)
- → `AtendenteHumano` (ManyToOne, optional)
- → `Mensagem` (OneToMany)

**Campos Faltantes (Notion propôs):**
- ❌ `data_primeira_resposta` - NÃO EXISTE
- ❌ `canal` - NÃO EXISTE (mas pode ser inferido)
- ❌ `cliente` - RELAÇÃO INDIRETA via Contato

**Recomendações:**
1. **ADICIONAR campos opcionais:**
   ```python
   data_primeira_resposta: DateTimeField(null/blank)
   canal: CharField(choices=['whatsapp','email','telefone','web'], default='whatsapp')
   ```
2. **Property para cliente:**
   ```python
   @property
   def cliente(self):
       return self.contato.clientes.first()  # Assumindo 1 cliente principal
   ```

---

#### Modelo: `Mensagem`

**Status:** ✅ **Estrutura adequada**

```python
class Mensagem(models.Model):
    id: AutoField (PK)
    atendimento: ForeignKey(Atendimento, CASCADE) ✓
    tipo: CharField(choices=TipoMensagem, default=TEXTO_FORMATADO) ✓
    conteudo: TextField() ✓
    remetente: CharField(choices=TipoRemetente, default='contato') ✓
    timestamp: DateTimeField(auto_now_add) ✓
    message_id_whatsapp: CharField(null/blank) ✓
    metadados: JSONField(dict, default={}) ✓
    respondida: BooleanField(default=False) ✓
    resposta_bot: TextField(null/blank) ✓
    intent_detectado: JSONField(list, default=[]) ✓
    entidades_extraidas: JSONField(list, default=[]) ✓
    confianca_resposta: FloatField(null/blank) ✓
```

**Análise:**
- ✅ Estrutura rica e completa
- ✅ Suporta múltiplos tipos de mensagem (WhatsApp types)
- ✅ Metadados para informações de mídia
- ✅ Campos de IA (intent, entidades, confiança)

**Enums:**
```python
TipoMensagem: 13 tipos (texto, imagem, vídeo, áudio, etc.)
TipoRemetente: contato, bot, atendente_humano
```

**Relacionamentos:**
- → `Atendimento` (ManyToOne)

**Observações:**
- Campo `timestamp` será mapeado para `data_envio` no Notion
- `message_id_whatsapp` útil para rastreamento

---

## 2. Ajustes Necessários nos Models Existentes

### 2.1. CRÍTICO - Model `Atendimento`

**Adicionar campos para compatibilidade com plano Notion:**

```python
# src/smart_core_assistant_painel/app/ui/atendimentos/models.py

class Atendimento(models.Model):
    # ... campos existentes ...
    
    # NOVOS CAMPOS:
    data_primeira_resposta: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data e hora da primeira resposta ao contato"
    )
    
    canal: models.CharField[str] = models.CharField(
        max_length=20,
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('email', 'E-mail'),
            ('telefone', 'Telefone'),
            ('web', 'Website'),
        ],
        default='whatsapp',
        help_text="Canal de origem do atendimento"
    )
    
    # ADICIONAR Property para cliente:
    @property
    def cliente(self) -> Optional["Cliente"]:
        """Retorna o cliente principal vinculado ao contato."""
        return self.contato.clientes.first() if self.contato.clientes.exists() else None
```

### 2.2. Atualização de Enums

**Manter enums atuais, mas documentar mapeamento:**

```python
# Mapeamento para Notion (será usado no app notion_sync)
STATUS_NOTION_MAPPING = {
    'fila': '🕐 Aguardando Inicial',
    'em_atendimento': '⚡ Em Andamento',
    'aguardando_retorno': '⏸️ Aguardando Contato',
    'resolvido': '✅ Resolvido',
    'cancelado': '❌ Cancelado'
}
```

---

## 3. Validação de Relacionamentos

### 3.1. Grafo de Relacionamentos

```
Contato (N) ←──────→ (M) Cliente
   ↓ (1:N)
Atendimento
   ↓ (1:N)              ↓ (N:1)              ↓ (N:1)
Mensagem        Departamento (1)      AtendenteHumano (1)
                       ↓ (1:N)               ↓ (1:1)
                AtendenteHumano      WhatsAppInstance
                       ↓ (1:N)
                 WhatsAppInstance
```

**Validações:**
- ✅ Não há referências circulares
- ✅ Cascade deletes configurados corretamente
- ✅ SET_NULL em relações opcionais
- ✅ Índices em ForeignKeys

---

## 4. Índices e Performance

### 4.1. Índices Existentes

**Contato:**
- ✅ `telefone` (unique) - implicit index
- ✅ `-ultima_interacao` (ordering)

**Cliente:**
- ✅ `nome_fantasia` (ordering)

**Departamento:**
- ✅ `slug` (explicit index)
- ✅ `[ativo, nome]` (composite index)

**AtendenteHumano:**
- ✅ `[departamento, disponivel]`
- ✅ `[disponivel, max_atendimentos_simultaneos]`
- ✅ `[data_ultima_atribuicao]`

**Atendimento:**
- ✅ `[status, departamento]`
- ✅ `[departamento, data_ultima_mensagem]`
- ✅ `[atendente_humano, status]`

**Mensagem:**
- ✅ `timestamp` (ordering)

**Recomendação:**
- ✅ **Índices adequados para queries de sincronização**
- 💡 Considerar índice em `Atendimento.data_primeira_resposta` após adicionar

---

## 5. Campos JSONField

### 5.1. Uso de JSONField

| Model | Campo | Tipo | Uso |
|-------|-------|------|-----|
| Contato | `metadados` | dict | ✅ Flexível |
| Cliente | `metadados` | dict | ✅ Flexível |
| Departamento | `configuracoes` | dict | ✅ Config técnica |
| Departamento | `metadados` | dict | ✅ Dados adicionais |
| AtendenteHumano | `horario_trabalho` | dict | ✅ Estruturado |
| AtendenteHumano | `especialidades` | list | ✅ Tags |
| AtendenteHumano | `metadados` | dict | ✅ Flexível |
| Atendimento | `contexto_conversa` | dict | ✅ Estado IA |
| Atendimento | `historico_status` | list[dict] | ✅ Audit trail |
| Atendimento | `tags` | list[str] | ✅ Categorização |
| Mensagem | `metadados` | dict | ✅ Dados mídia |
| Mensagem | `intent_detectado` | list[dict] | ✅ NLU |
| Mensagem | `entidades_extraidas` | list[dict] | ✅ NER |

**Análise:**
- ✅ Uso apropriado de JSONField
- ✅ Permite extensibilidade sem migrations
- ✅ Útil para armazenar metadados de sincronização temporários

---

## 6. Checklist de Ajustes

### ✅ Aprovados (Não necessitam alteração)
- [x] Modelo `Contato` - estrutura perfeita
- [x] Modelo `Cliente` - estrutura completa
- [x] Modelo `Departamento` - adequado
- [x] Modelo `AtendenteHumano` - bem estruturado
- [x] Modelo `Mensagem` - rico e completo
- [x] Modelo `WhatsAppInstance` - excluído da sincronização

### ✅ Ajustes Realizados
- [x] **Atendimento:** ✅ Campo `data_primeira_resposta` adicionado
- [x] **Atendimento:** ✅ Campo `canal` adicionado (choices: whatsapp, email, telefone, web)
- [x] **Atendimento:** ✅ Property `cliente` implementada
- [x] **Atendimento:** ✅ Mapeamento de status documentado

### 📝 Documentação
- [x] ✅ Constantes de mapeamento criadas (STATUS_NOTION_MAPPING)
- [x] ✅ Campos Django vs Notion documentados
- [x] ✅ Plano Notion atualizado com enums reais

---

## 7. Conclusão

### Status Geral: ✅ **MODELOS PRONTOS PARA INTEGRAÇÃO**

**Pontos Fortes:**
- ✅ Estrutura bem normalizada
- ✅ Validações robustas
- ✅ Relacionamentos claros
- ✅ Flexibilidade via JSONField
- ✅ Timestamps automáticos
- ✅ Métodos helper úteis

**Ajustes Realizados com Sucesso:**
1. ✅ 2 campos adicionados em `Atendimento` (data_primeira_resposta, canal)
2. ✅ Property `cliente` implementada em `Atendimento`
3. ✅ Documentação atualizada com enums e mapeamentos reais

**Status Atual:**
✅ **MODELS PRONTOS - AJUSTES CONCLUÍDOS** - Todos os ajustes necessários foram implementados. Models principais estão estruturalmente sólidos e prontos para integração via app dedicado `notion_sync`.

---

**Próximo Passo:** Revisar arquitetura do app `notion_sync` considerando:
- Foco em Kanban para gestão de Atendimentos
- Model intermediário com apenas campos necessários para sincronização
- Comunicação via interfaces abstratas (substituibilidade futura)
- Atendimentos devem incluir visualização de mensagens