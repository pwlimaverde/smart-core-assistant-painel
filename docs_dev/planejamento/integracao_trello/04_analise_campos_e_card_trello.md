# Análise de Campos e Representação no Card do Trello

Este documento detalha o mapeamento dos campos dos modelos Django para os elementos visuais nos cartões do Trello. A tabela abaixo serve como um guia para a sincronização de dados entre o sistema de atendimentos e o Trello.

## Tabela de Mapeamento: Django ↔ Trello Card

| Modelo e Campo Django | Elemento no Card do Trello | Direção Sync | Notas |
| :--- | :--- | :--- | :--- |
| **Atendimento.id** | Título do Card | `->` | O título será formatado como: `[#ID] - Nome do Contato` (Ex: `[#123] - João Silva`). |
| **Atendimento.assunto** | Título do Card (Sufixo) | `->` | Adicionado ao título se existir: `[#123] - João Silva - Orçamento Site` |
| **Contato.nome_contato** | Título do Card | `->` | Usado para compor o título do card. |
| **Cliente.nome_fantasia** | Campo Personalizado: "Cliente" | `->` | Nome da empresa ou cliente principal associado ao atendimento. |
| **Atendimento.prioridade** | Etiqueta (Label) | `<->` | Mapeamento de prioridade para cores de etiqueta (Ex: "Urgente" -> Vermelho). A mudança da etiqueta no Trello pode (opcionalmente) atualizar a prioridade no Django. |
| **Atendimento.data_inicio** | Campo Personalizado: "Início" | `->` | Data e hora de criação do atendimento. |
| **Atendimento.data_ultima_mensagem** | Campo Personalizado: "Últ. Mensagem" | `->` | Atualizado a cada nova mensagem para indicar a atividade recente. |
| **Atendente.nome** | Membro do Card | `<->` | O `Atendente` responsável é atribuído como membro do card. A atribuição de um membro no Trello sincroniza o `atendente_humano` no Django. |
| **EtapaFluxo.nome** | Lista do Trello | `<->` | O nome da `EtapaFluxo` corresponde ao nome da Lista no quadro. Mover o card entre listas atualiza a `etapa_atual` do `Atendimento`. |
| **Atendimento (Resumo)** | Descrição do Card | `->` | A descrição conterá um resumo gerado com informações chave. |
| **Contato.telefone** | Descrição do Card | `->` | Incluído na descrição para fácil acesso. |
| **Contato.email** | Descrição do Card | `->` | Incluído na descrição, se disponível. |
| **Atendimento.canal** | Descrição do Card | `->` | Canal de origem (ex: "WhatsApp", "Web"). |
| **Atendimento.id (Link)** | Descrição do Card | `->` | Um link direto para a tela do atendimento no painel Smart Core Assistant. (Ex: `https://painel.meusistema.com/atendimentos/123/`) |
| **Mensagem (últimas 3)** | Comentários do Card | `->` | As últimas mensagens trocadas no atendimento serão adicionadas como comentários no card para dar contexto. |

---

## Exemplo Visual de um Card no Trello

A seguir, uma representação de como um card ficaria no Trello com base no mapeamento acima.

**Título do Card:** `[#451] - Maria Souza - Dúvida sobre Fatura`

**Membros:** `(Avatar de Carlos Andrade)`

**Etiquetas:** <span style="color:orange;">●</span> Normal

**Descrição:**
```
**Atendimento #451**

**Cliente:** Empresa XYZ
**Contato:** Maria Souza
**Telefone:** 5511987654321
**Email:** maria.souza@email.com
**Canal:** WhatsApp

**Link Interno:** [Acessar Atendimento no Painel](https://painel.meusistema.com/atendimentos/451/)

---
*Última atualização: 15/08/2024 11:30*
```

**Campos Personalizados:**
- **Início:** `14/08/2024 09:15`
- **Últ. Mensagem:** `15/08/2024 11:28`
- **Cliente:** `Empresa XYZ`

**Comentários:**

> **Carlos Andrade** (15/08/2024 11:28):
> Olá, Maria! Já estou verificando sua fatura. Um momento, por favor.

> **Maria Souza** (15/08/2024 11:27):
> Bom dia, recebi minha fatura e o valor parece incorreto. Podem me ajudar?

---