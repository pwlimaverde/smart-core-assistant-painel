# Planejamento: Fluxo de Atribuição Inteligente e Handover

Este documento descreve as regras de negócio e o fluxo técnico para automatizar a transferência de atendimentos para a instância pessoal do atendente (quando aplicável) e o envio de mensagem de saudação automática.

## 1. Objetivo de Negócio

Permitir que, ao assumir um atendimento no painel (Kanban), o atendente receba a conversa "pronta" em seu dispositivo WhatsApp (físico ou web) sem precisar adicionar o contato do cliente manualmente. Isso é realizado através do envio ativo de uma mensagem ("Active Push") a partir da instância do atendente para o cliente.

## 2. Estratégia de Início de Conversa (Automação)

O objetivo principal desta funcionalidade é **eliminar a fricção operacional** no início do atendimento humano.

*   **Contexto**: O atendente possui acesso completo ao histórico da conversa através do **Painel Kanban**. Portanto, não é necessário migrar o histórico de mensagens para o WhatsApp pessoal do atendente.
*   **Foco da Automação**: A automação serve exclusivamente para **iniciar a interação** no dispositivo do atendente (abrir a janela de chat) sem que ele precise salvar o contato ou digitar a primeira mensagem.
*   **Mecanismo**: Ao enviar a mensagem de saudação ("Olá, meu nome é..."), o WhatsApp automaticamente posiciona essa conversa no topo da lista do atendente, pronta para continuidade.

## 3. Fluxo da Solução Proposta

### 3.1. Gatilho (Ação do Usuário)
O processo inicia quando:
1.  O atendente arrasta um card da coluna "Fila" para "Em Atendimento" no Kanban.
2.  OU o atendente clica no botão "Atribuir a Mim".
3.  OU um gestor atribui o atendimento a um atendente específico.

Tecnicamente, isso dispara uma alteração no campo `Atendimento.atendente_humano`.

### 3.2. Lógica de Decisão (Handover Service)

Ao detectar a atribuição, o sistema executa a seguinte lógica (`AtendimentoHandoverService`):

1.  **Verificação de Instância**:
    *   O sistema verifica se o `Atendente` atribuído possui uma `AppInstance` vinculada (campo `owner` em `AppInstance`).
    *   **Caso 1: Atendente com Instância Própria (Ex: Número Corporativo)**
        *   A instância de envio (`sender`) passa a ser a do Atendente.
        *   O contexto do atendimento é atualizado com a nova `api_key`.
    *   **Caso 2: Atendente sem Instância (Usa Número Central)**
        *   A instância de envio permanece a do Departamento/Triagem.

2.  **Construção da Mensagem**:
    *   O sistema gera uma mensagem de saudação personalizada.
    *   *Template Padrão*: "Olá, meu nome é {primeiro_nome}, darei continuidade ao seu atendimento."
    *   *Variação*: Se for o mesmo número (Caso 2), a mensagem serve apenas para "humanizar" a conversa.

3.  **Execução do Envio (Assíncrono)**:
    *   O sistema agenda uma tarefa (`django_q`) para enviar a mensagem.
    *   Isso garante que a interface do Kanban não trave aguardando a API do WhatsApp.

### 3.3. Resultado Esperado

1.  **No WhatsApp do Cliente**: Recebe uma nova mensagem (possivelmente de um novo número) dizendo "Olá...".
2.  **No WhatsApp do Atendente**: O chat com o cliente aparece no topo da lista de conversas (devido ao envio da mensagem).
3.  **No Painel**: O status muda para "Em Atendimento" e a mensagem de saudação é registrada no histórico.

## 4. Regras de Negócio

1.  **Precedência de Instância**: A instância pessoal do atendente sempre tem prioridade sobre a instância do departamento ao enviar mensagens manuais ou de saudação.
2.  **Tratamento de Erro**: Se a instância do atendente estiver desconectada (Evolution API offline):
    *   O sistema deve tentar enviar pela instância do Departamento (fallback).
    *   Uma notificação de alerta deve ser gerada no painel para o atendente.
3.  **Evitar Spam**: Se o atendente já estava atribuído e apenas mudou de etapa (ex: "Em Atendimento" -> "Aguardando"), a mensagem de saudação NÃO deve ser enviada novamente. O gatilho é a **entrada** no estado de posse (de `None` para `Atendente`).

## 5. Especificação Técnica

### 5.1. Novos Componentes

*   **`AtendimentoHandoverService`**: Classe responsável por orquestrar a troca de contexto e envio.
    *   Método: `process_handover(atendimento: Atendimento, atendente: Atendente) -> bool`
*   **Signal Handler**:
    *   Ouvir `pre_save` ou `post_save` de `Atendimento`.
    *   Detectar `if old_instance.atendente_humano is None and new_instance.atendente_humano is not None`.

### 5.2. Exemplo de Implementação (Pseudocódigo)

```python
# services/handover_service.py

def process_handover(atendimento, atendente):
    # 1. Determinar Instância
    instancia_alvo = atendente.app_instance
    if not instancia_alvo or not instancia_alvo.active:
        instancia_alvo = atendimento.departamento.get_instancia_padrao()

    # 2. Atualizar Contexto do Atendimento
    atendimento.atualizar_contexto("api_key_atual", instancia_alvo.api_key)

    # 3. Enviar Mensagem
    mensagem_texto = f"Olá, meu nome é {atendente.nome_curto}, darei continuidade ao seu atendimento."

    send_whatsapp_message(
        api_key=instancia_alvo.api_key,
        phone=atendimento.contato.telefone,
        message=mensagem_texto
    )

    # 4. Registrar no Banco
    Mensagem.objects.create(
        atendimento=atendimento,
        remetente="atendente_humano",
        conteudo=mensagem_texto,
        # ...
    )
```

## 6. Próximos Passos para Implementação

1.  Criar o `AtendimentoHandoverService`.
2.  Implementar o Signal em `src/smart_core_assistant_painel/app/ui/atendimentos/signals.py` (criar se não existir).
3.  Configurar task assíncrona no Django Q.
4.  Testar com instâncias reais para validar a abertura do chat no dispositivo do atendente.
