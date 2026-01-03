# Relatório Completo: Precificação e Análise Competitiva - Smart Core Assistant

## 1. Visão Geral do Smart Core Assistant

O **Smart Core Assistant** é uma plataforma inovadora de atendimento centralizado via WhatsApp que combina IA avançada (RAG com pgvector nativo), handover inteligente IA-humano e gerenciamento visual via integração bidirecional com Trello (Kanban).

### Diferenciais Principais
*   **Base de conhecimento dinâmica:** Upload de PDFs/DOCX com chunking automático.
*   **Sincronização real-time Trello:** Conversas viram cards, movimentações atualizam status.
*   **Multi-número e Multi-departamento:** Suporte via Evolution API e dashboards gerenciais.
*   **Orquestrador central:** Contexto de conversa persistente e validação de contatos.

> **Fluxo Principal:** Cliente → IA analisa/RAG → Ticket Trello → Handover humano (se necessário) → Finalização sincronizada.

---

## 2. Análise de Mercado e Concorrentes

### 2.1 Concorrentes por Segmento de Preço e Funcionalidades

As plataformas brasileiras de chatbot WhatsApp com IA e gerenciamento de atendimentos existentes geralmente não oferecem *Trello sync nativo* somado a um *RAG profundo*.

| Plataforma | Plano Inicial (R$/mês) | Conversas Incluídas | Usuários | IA/RAG | Gerenciamento Visual | Diferencial vs Smart Core |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Blip** | ~R$1.200 | 800-2.000 | 10 | Avançada | Painel próprio | Enterprise-heavy, sem Trello |
| **Zenvia** | R$1.800 | ~2.000 | 30 | Avançada | Omnichannel interno | Setup complexo, foco voz |
| **RD Station** | R$798 | 1.000 | 2 | Fluxos básicos | CRM lists | Orientado a Marketing |
| **Huggy** | ~R$500+ | Variável | Ilimitado | Chatbots | Interface interna | Omnichannel genérico |
| **Chatpro** | ~R$300+ | Por uso | Multi | ChatGPT básico | Multi-depto | Sem Kanban visual |
| **Letalk** | ~R$400 | 1.000 | Multi | IA simples | Inbox central | Pré-atendimento básico |
| **Manychat** | ~R$50+ | Paga/conversa | Ilimitado | Automação | Fluxogramas | Marketing, sem handover |

> *Nota:* Preços incluem assinatura + custo Meta WhatsApp (~R$0,20-0,55/conversa iniciada).

### 2.2 Posicionamento Competitivo

*   **Sem concorrente direto:** Nenhuma combina RAG nativo (pgvector), Trello bidirecional e handover com contexto completo.
*   **Vantagem na Simplicidade:** "Gerencie como no Trello" vs painéis proprietários que exigem treinamento.
*   **Mercado-Alvo:** PMEs brasileiras (e-commerce, serviços) que usam WhatsApp + Trello, buscando escalar sem a complexidade de soluções como Blip/Zenvia.

---

## 3. Estratégia de Precificação Recomendada

**Modelo:** Assinatura mensal + conversas extras + setup único.
*Competitivo abaixo de Blip/Zenvia, valor premium vs básicos.*

### 3.1 Tiers de Planos

| Plano | Preço (R$/mês) | Números WhatsApp | Conversas/mês | Usuários | Funcionalidades Exclusivas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Básico** | **R$ 497** | 1 | 1.000 | 5 | RAG essencial, Trello sync básico, 1 depto |
| **Pro** | **R$ 997** | 3 | 3.000 | 15 | Multi-depto, handover avançado, dashboards |
| **Enterprise** | **R$ 1.997** | Ilimitado | Sob consulta | Ilimitado | Suporte dedicado, integrações custom (Firebase) |

### 3.2 Detalhes Adicionais
*   **Conversas extras:** R$ 0,25 cada (alinhado Meta)
*   **Setup único:** R$ 1.000 (Básico) a R$ 2.000 (Enterprise)
*   **Desconto anual:** 20% off
*   **Trial:** 14 dias grátis (Limitação de 500 conversas)

### 3.3 Justificativa por Tier
*   **Básico (R$ 497):** *Entry-level* acessível vs RD Station (R$ 798), destaca o Trello visual.
*   **Pro (R$ 997):** *Sweet spot* vs Zenvia inicial, entregando valor em RAG + multi-departamento.
*   **Enterprise (R$ 1.997):** Posicionado abaixo do Blip Plus, focado no nicho Trello/RAG para escala.

---

## 4. Funcionalidades Únicas vs Concorrentes

Comparativo de funcionalidades exclusivas do Smart Core Assistant:

*   ✅ **RAG Nativo** (pgvector, upload docs)
*   ✅ **Trello Sync Bidirecional** (cards automáticos, movimentação real-time)
*   ✅ **Handover IA-Humano** com resumo de contexto
*   ✅ **Multi-número/departamento nativo** (Evolution API)
*   ✅ **Dashboards + Auditoria completa**
*   ✅ **Firebase Remote Config dinâmico**

*Fonte: Documentos internos e análise de mercado.*

---

## 5. Recomendações de Go-to-Market

1.  **Trial Estratégico:** 14 dias com setup guiado (via webinar ou vídeo demonstrativo).
2.  **Landing Page:** Destaque para "Trello + IA WhatsApp" com vídeo de demonstração.
3.  **Preço Psicológico:** R$ 497 (evitar R$ 500), criar urgência com "vagas limitadas".
4.  **Upsell:** Oferecer migração gratuita de planilhas/chats manuais.
5.  **Métricas de Sucesso:**
    *   30% conversão trial → pago
    *   Churn <10% nos primeiros 3 meses

---

**Contato para Customizações:** smartcoreassistant@gmail.com

> *Relatório gerado em 09/12/2025. Dados de mercado baseados em fontes públicas de 2025.*