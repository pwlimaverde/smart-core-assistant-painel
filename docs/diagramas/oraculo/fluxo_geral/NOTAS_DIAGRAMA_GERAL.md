# 📋 Notas Explicativas - Fluxo de Recebimento de Mensagem WhatsApp

## 🎯 Visão Geral do Sistema
**Versão**: 5.0 - Implementação Real Documentada
**Data**: 18 de julho de 2025

Este fluxo representa o processo **real implementado** de recebimento, processamento e direcionamento de mensagens WhatsApp no sistema de atendimento. O diagrama foi ajustado para refletir exatamente o que está implementado no código, incluindo funcionalidades em desenvolvimento e TODOs planejados.

### ✨ **Características Implementadas**:
1. **Processamento Completo de Webhook**: Validação POST, parsing JSON, tratamento de erros
2. **Extração Inteligente de Dados**: Suporte a todos os tipos de mensagem WhatsApp
3. **Direcionamento por Contexto**: Verificação se bot pode responder baseado em histórico
4. **Conversão de Contexto Multimídia**: Preparação para análise de conteúdo não textual
5. **Gestão de Atendimentos**: Criação e recuperação de atendimentos ativos
6. **Logging Completo**: Auditoria de todas as operações para debugging

### ⚠️ **Funcionalidades Planejadas (TODO)**:
1. **Resposta Automática do Bot**: Código preparado mas não implementado
2. **Classificação de Intent**: Análise de intenção das mensagens
3. **Transferência Automática**: Sistema de triagem por especialidade
4. **Validação de API Key**: Segurança robusta do webhook
5. **Análise de Conteúdo Multimídia**: OCR, transcrição, análise de imagem

### 🔄 **Diferenças da Versão Anterior**:
- **Removido**: Fluxos complexos de resposta automática não implementados
- **Adicionado**: Seção TODO clara para funcionalidades planejadas
- **Simplificado**: Foco no que realmente está funcionando
- **Detalhado**: Subgrafos explicando processos internos implementados

---

## 🚀 1. INÍCIO DO FLUXO - Webhook de Recebimento

### 📱 1.1 **Função: webhook_whatsapp (View Django)**
**Processo**: Ponto de entrada robusto para webhook do WhatsApp
- **Validações Implementadas**:
  - Método HTTP deve ser POST
  - Body da requisição não pode estar vazio
  - JSON deve ser válido e estruturado
  - Logs de auditoria completos
- **Tratamento de Erros**:
  - 405: Método não permitido
  - 400: JSON inválido ou corpo vazio
  - 500: Erro interno do servidor
- **Resposta**:
  ```json
  {
    "status": "success",
    "mensagem_id": 12345,
    "direcionamento": "bot|humano"
  }
  ```

**Implementação Real**: 
```python
def webhook_whatsapp(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    data = json.loads(request.body)
    mensagem_id = nova_mensagem(data)
    # ... processamento completo
```

### 🔍 1.2 **Função: nova_mensagem**
**Processo**: Extração inteligente de dados do payload WhatsApp
- **Extrações por Tipo**:
  - **TEXTO_FORMATADO**: Extrai `text` diretamente
  - **IMAGEM**: Extrai `caption`, `mimetype`, `url`, `fileLength`
  - **VIDEO**: Extrai `caption`, `mimetype`, `url`, `seconds`, `fileLength`
  - **AUDIO**: Extrai `mimetype`, `url`, `seconds`, `ptt` (mensagem de voz)
  - **DOCUMENTO**: Extrai `fileName`, `mimetype`, `url`, `fileLength`
  - **OUTROS**: STICKER, LOCALIZACAO, CONTATO, LISTA, BOTOES, ENQUETE, REACAO
- **Metadados**: Estrutura específica por tipo para processamento posterior
- **Retorno**: ID da mensagem criada (inteiro)

**Lógica Implementada**:
```python
# Obter primeira chave do message (tipo de mensagem)
message_keys = data.get('data').get('message').keys()
tipo_chave = list(message_keys)[0]

# Converter para enum interno
tipo_mensagem = TipoMensagem.obter_por_chave_json(tipo_chave)
```

### ⚙️ 1.3 **Função: processar_mensagem_whatsapp**
**Processo**: Criação da mensagem no banco de dados
- **Determinação do Remetente**:
  ```python
  atendente = AtendenteHumano.objects.filter(telefone=numero_telefone).first()
  remetente = TipoRemetente.ATENDENTE_HUMANO if atendente else TipoRemetente.CLIENTE
  ```
- **Gestão de Atendimentos**:
  - Busca atendimento ativo primeiro
  - Cria novo se não existe
  - Atualiza timestamp do cliente
- **Retorno**: ID da mensagem criada

### 💾 1.4 **Recuperar Objeto Mensagem**
**Processo**: Acesso completo aos dados da mensagem
- **Implementação**: `Mensagem.objects.get(id=mensagem_id)`
- **Objetivo**: Acessar relacionamento `mensagem.atendimento` para verificações
- **Importância**: Base para todas as verificações subsequentes

---

## 🎯 2. CONVERSÃO DE CONTEXTO MULTIMÍDIA

### ❓ 2.1 **Verificação de Tipo Não Textual**
**Processo**: Identificação de mensagens que precisam conversão
- **Condição**: `mensagem.tipo != TipoMensagem.TEXTO_FORMATADO`
- **Tipos que passam**: IMAGEM, VIDEO, AUDIO, DOCUMENTO, STICKER, etc.

### 🤖 2.2 **Função: _converter_contexto** 
**Status**: **PLACEHOLDER ATUAL - TODO**
- **Implementação Atual**: Sempre retorna `'contexto'`
- **Objetivo Futuro**: Converter metadados em texto descritivo
- **Exemplos Planejados**:
  - `"Imagem JPEG de 2.1MB (1920x1080)"`
  - `"Áudio MP3 de 45 segundos"`
  - `"Documento PDF: 'Relatório_Mensal.pdf' (856KB)"`

**Código Atual**:
```python
def _converter_contexto(metadata) -> str:
    # TODO: Implementar lógica específica
    return 'contexto'
```

### 💾 2.3 **Atualização do Conteúdo**
**Processo**: Substituição do conteúdo original pelo convertido
- **Verificação**: Só atualiza se conteúdo mudou
- **Otimização**: Usa `update_fields=['conteudo']`
- **Log**: Registra conversão realizada

---

## 🔧 3. VERIFICAÇÃO DE DIRECIONAMENTO

### 🔧 3.1 **Função: _pode_bot_responder_atendimento**
**Processo**: **ÚNICA VERIFICAÇÃO** centralizada de direcionamento
- **Implementação Real**:
  ```python
  def _pode_bot_responder_atendimento(atendimento):
      mensagens_atendente = atendimento.mensagens.filter(
          remetente=TipoRemetente.ATENDENTE_HUMANO
      ).exists() or atendimento.atendente_humano is not None
      
      return not mensagens_atendente
  ```
- **Lógica**: Bot NÃO responde se:
  - Há mensagens de atendente humano no histórico
  - OU atendimento tem atendente responsável
- **Comportamento Conservador**: Em caso de erro, assume `False` (direcionamento humano)

---

## ❓ 4. DECISÃO DE DIRECIONAMENTO

### ❓ 4.1 **Bot pode responder?**
**Resultado**: Baseado na verificação anterior
- **True**: Mensagem vai para fluxo do bot (5.1)
- **False**: Mensagem vai para fluxo humano (6.1)

---

## ⚠️ 5. FLUXO BOT - TODO NÃO IMPLEMENTADO

### ⚠️ 5.1 **Resposta Automática do Bot**
**Status**: **PREPARADO MAS NÃO IMPLEMENTADO**
- **Código Comentado**: Pronto para implementação
- **Estrutura Planejada**:
  ```python
  # TODO: Implementar geração de resposta automática
  # resposta = FeaturesCompose.gerar_resposta_automatica(mensagem)
  # if resposta:
  #     mensagem.resposta_bot = resposta
  #     mensagem.respondida = True
  #     mensagem.save()
  ```
- **Dependências**: Módulo AI Engine não integrado ainda

---

## 👤 6. FLUXO HUMANO - IMPLEMENTADO

### 👤 6.1 **Direcionamento Humano**
**Processo**: Lógica atual para atendimento humano
- **Log**: Registra direcionamento e contexto
- **Verificação**: Se tem atendente responsável

### ❓ 6.2 **Tem Atendente Responsável?**
**Verificação**: `atendimento.atendente_humano is not None`
- **Sim**: Direciona para responsável (6.3)
- **Não**: Direciona para triagem (6.4)

### 🎯 6.3 **Direcionar para Responsável**
**Processo**: Conexão direta com atendente definido
- **Log**: `f"Mensagem {mensagem_id} direcionada para atendente: {atendente.nome}"`
- **Contexto**: Mantém histórico da conversa
- **Eficiência**: Sem necessidade de triagem

### 📋 6.4 **Direcionar para Triagem**
**Processo**: Aguarda designação de atendente
- **Log**: `f"Mensagem {mensagem_id} direcionada para triagem de atendente humano"`
- **Status**: Mensagem fica disponível para atendentes livres
- **Futuro**: Integração com sistema de busca de atendente disponível

---

## ✅ 7. RESPOSTA FINAL DO WEBHOOK

### ✅ 7. **Resposta de Sucesso**
**Formato**: JSON estruturado
```json
{
  "status": "success",
  "mensagem_id": 12345,
  "direcionamento": "bot" | "humano"
}
```
- **Status HTTP**: 200
- **Log**: Registro completo do processamento
- **Metadados**: ID da mensagem e direcionamento para auditoria

### ❌ 7.1 **Resposta de Erro**
**Tratamento**: Diferentes tipos de erro
- **400**: JSON inválido, corpo vazio
- **405**: Método não permitido
- **500**: Erro interno do servidor
- **Log**: Erro detalhado com stack trace

---

## 🔍 DETALHAMENTO DOS PROCESSOS INTERNOS

### 📞 buscar_atendimento_ativo
**Implementação**:
1. **Normalizar telefone**: Adiciona +55, remove caracteres especiais
2. **Buscar Cliente**: `Cliente.objects.filter(telefone=telefone_formatado)`
3. **Buscar Atendimento**: Status em `[AGUARDANDO_INICIAL, EM_ANDAMENTO, AGUARDANDO_CLIENTE, AGUARDANDO_ATENDENTE]`

### 🆕 inicializar_atendimento_whatsapp
**Implementação**:
1. **get_or_create Cliente**: Cria se não existe, atualiza metadados se existe
2. **Verificar Atendimento Ativo**: Evita duplicação
3. **Criar Novo Atendimento**: Status `AGUARDANDO_INICIAL`, contexto WhatsApp
4. **Histórico**: Registra criação com motivo "Atendimento iniciado via WhatsApp"

### 📱 Tipos de Mensagem Suportados
**Implementados**:
- **TEXTO_FORMATADO**: Processamento direto do texto
- **IMAGEM**: Caption + metadados (mimetype, url, fileLength)
- **VIDEO**: Caption + metadados (seconds, mimetype, url)
- **AUDIO**: Metadados completos (ptt para mensagem de voz)
- **DOCUMENTO**: Nome do arquivo + metadados
- **STICKER, LOCALIZACAO, CONTATO, LISTA, BOTOES, ENQUETE, REACAO**: Suporte básico

---

## 🚧 FUNCIONALIDADES PLANEJADAS (TODO)

### 🤖 Resposta Automática Bot
- Integração com AI Engine
- Cálculo de confiança da resposta
- Envio automático para cliente
- Fallback para humano em baixa confiança

### 🔍 Classificação de Intent
- Análise de intenção: PERGUNTA, SATISFACAO, TRANSFERENCIA
- Machine Learning para categorização
- Direcionamento inteligente baseado em intent

### 🔄 Transferência Automática
- Busca por especialidade/departamento
- Balanceamento de carga entre atendentes
- Sistema de espera e retry

### 🔐 Validação API Key
- Autenticação robusta do webhook
- HMAC-SHA256 ou banco de dados
- Rate limiting e blacklist

### 🎯 Análise Conteúdo Multimídia
- OCR para extração de texto em imagens
- Transcrição automática de áudios
- Análise de documentos PDF/DOC
- Descrição automática de vídeos

---

## 📊 MÉTRICAS E MONITORAMENTO

### Logs Implementados
- Auditoria de entrada do webhook
- Processamento de cada tipo de mensagem
- Direcionamento e decisões tomadas
- Erros com stack trace completo

### KPIs Disponíveis
- Taxa de sucesso do webhook
- Distribuição por tipo de mensagem
- Direcionamento bot vs humano
- Tempo de processamento por etapa

### Debugging
- IDs únicos para rastreamento
- Logs estruturados para análise
- Metadados preservados para análise posterior

---

## 🔄 ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Validação e Segurança
- [ ] Implementar validação robusta de API Key
- [ ] Adicionar rate limiting no webhook
- [ ] Implementar HMAC-SHA256 para assinatura

### Fase 2: Resposta Automática
- [ ] Integrar módulo AI Engine
- [ ] Implementar geração de resposta automática
- [ ] Adicionar cálculo de confiança
- [ ] Criar fallback para baixa confiança

### Fase 3: Classificação Inteligente
- [ ] Implementar análise de intent
- [ ] Adicionar categorização automática
- [ ] Criar regras de direcionamento por intent

### Fase 4: Análise Multimídia
- [ ] Implementar OCR para imagens
- [ ] Adicionar transcrição de áudio
- [ ] Criar análise de documentos
- [ ] Implementar descrição de vídeos

### Fase 5: Transferência Inteligente
- [ ] Sistema de busca por especialidade
- [ ] Balanceamento automático de carga
- [ ] Escalação automática por timeout
- [ ] Transferência entre setores

---

## 📝 CONCLUSÃO

Este documento reflete o **estado atual real** da implementação do webhook WhatsApp. O diagrama e as notas foram ajustados para mostrar:

1. **O que está funcionando**: Processamento básico, extração de dados, direcionamento
2. **O que está preparado**: Estrutura para resposta automática, placeholders implementados
3. **O que está planejado**: TODOs claramente marcados e documentados

A documentação serve como base para:
- **Debugging**: Entender exatamente o que acontece em cada etapa
- **Desenvolvimento**: Saber onde implementar novas funcionalidades
- **Manutenção**: Localizar rapidamente problemas no fluxo
- **Planejamento**: Roadmap claro de próximas implementações
