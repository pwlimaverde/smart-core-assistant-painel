# Documentação Auxiliar — Chat estilo WhatsApp: mídia/IA estruturada + correção de visualização

> Gerado em: 2026-05-24
> Plano canônico: `.context/plans/chat-whatsapp-midia-ia.md`
> Plano completo: `.context/plans/chat-whatsapp-midia-ia/plano_completo_chat-whatsapp-midia-ia.md`

Versões fixadas (de `pyproject.toml`):
`django==5.2.7`, `langchain==1.0.2`, `langchain-core==1.0.0`, `langchain-openai==1.0.1`,
`langchain-google-genai>=2.1.0`, `pydantic==2.12.3`, `httpx==0.28.1`.

---

## Libs Python

### langchain / langchain-core (1.0.x) — `with_structured_output` + mensagens multimodais
Library ID context7: `/websites/langchain_oss`

- **`with_structured_output(PydanticModel)`** retorna a **instância Pydantic** diretamente.
  Sem breaking change de uso entre 0.3.x → 1.0 para esse método.
  ```python
  from pydantic import BaseModel

  class AnswerWithJustification(BaseModel):
      answer: str
      justification: str

  structured = model.with_structured_output(AnswerWithJustification)
  result = structured.invoke("...")   # -> instância (result.answer, result.justification)
  ```
- **Mensagens multimodais (content blocks)** — no 1.0 há o formato **nativo LangChain** e os formatos **nativos do provedor** (ambos aceitos):
  ```python
  # Imagem — formato nativo LangChain
  {"type": "image", "base64": b64, "mime_type": "image/jpeg"}
  # Imagem — formato provedor (OpenAI/Gemini), data-URI  ← usado hoje no projeto
  {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
  # Documento PDF inline
  {"type": "document_url", "document_url": {"url": f"data:application/pdf;base64,{b64}"}}
  ```
  Construção: `HumanMessage(content=[{"type":"text","text":...}, <bloco de mídia>])`.
- **Imports**: `from langchain_core.messages import HumanMessage` continua válido no 1.0;
  o alias novo é `from langchain.messages import HumanMessage`.
- **Combinar multimodal + structured output** no mesmo `invoke` é suportado (a doc oficial
  mostra extração de JSON estruturado a partir de PDF inline numa única chamada).

### langchain-google-genai (>=2.1.0) — ChatGoogleGenerativeAI (gemini-2.5-flash)
Library ID context7: `/langchain-ai/langchain-google`

- **Structured output** com Pydantic retorna instância:
  ```python
  from pydantic import BaseModel, Field
  from langchain_google_genai import ChatGoogleGenerativeAI

  class Recipe(BaseModel):
      name: str = Field(description="Recipe name")
      ingredients: list[str] = Field(description="List of ingredients")

  model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
  structured = model.with_structured_output(Recipe)
  recipe = structured.invoke("Give me a simple pasta recipe.")  # recipe.name, recipe.ingredients
  ```
  (Variante alternativa p/ Gemini: `with_structured_output(schema=Model.model_json_schema(), method="json_schema")` → retorna **dict**. Preferir a classe Pydantic.)
- **Multimodal (imagem)** confirmado com `image_url` + data-URI base64 (igual ao código atual):
  ```python
  vision_msg = HumanMessage(content=[
      {"type": "text", "text": "Describe this landscape."},
      {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
  ])
  model.invoke([vision_msg])
  ```
- `ChatGoogleGenerativeAI` lista oficialmente suporte a: streaming, async, tool calling,
  **structured output**, **multimodal (imagens, vídeo, áudio, PDFs)** e context caching.
- **Conclusão p/ o plano**: imagem/vídeo/documento → **1 chamada** (multimodal + structured).
  Áudio → manter **2 passos** (transcrição no datasource de áudio dedicado; resumo via 2ª
  chamada leve de texto com structured output), por robustez.

### pydantic (2.12.3)
- `BaseModel` com `Field(description=...)` é a forma recomendada — a `description` é embutida
  no schema enviado ao LLM, melhorando a aderência da saída estruturada.

### django (5.2.7)
- `TextField(blank=True, default="")` + migration padrão (`makemigrations` → `migrate`).
  Sem particularidades; isolamento multi-tenant via `TenantDatabaseRouter` (sem FK de tenant).

---

## Frontend / Serviços de UI

### Alpine.js — `x-for`, `x-if`, `x-text`
Fonte: https://alpinejs.dev/directives/for

- **Regra confirmada (oficial)**: *"`x-for` MUST be declared on a `<template>` element. That
  `<template>` element MUST contain only one root element."* Múltiplos elementos irmãos na raiz
  do `<template x-for>` **"will not work"** (loop não renderiza).
- **`<template x-if>` aninhado** dentro do root único do `x-for` **é permitido** — solução para
  o bug: envolver separadores de data/"novas mensagens" + balão num único `<div>` wrapper.
- **Quebras de linha**: `x-text` **não** converte `\n` em quebra visual. Recomendado usar CSS
  `white-space: pre-wrap` no elemento de texto (preserva `\n` sem risco de injeção), em vez de
  `x-html` com `<br>` (que exige sanitização).

---

## Notas Gerais
- Nenhuma dependência nova é necessária — `with_structured_output` já vem em
  `langchain-google-genai`/`langchain-openai` instalados.
- Manter Result Pattern (`SuccessReturn`/`ErrorReturn`) nos usecases/datasources de IA.
- Credenciais de visão/transcrição via `SERVICEHUB`/config por tenant — **nada** novo em `.env`.
- O download de mídia da Evolution Go (base64) já está implementado e funcional no
  `attendance_orchestrator._fetch_media_base64_from_evolution` — o plano não altera essa
  integração externa, apenas o consumo do base64 pela IA.
