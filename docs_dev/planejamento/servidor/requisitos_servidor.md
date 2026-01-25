# Análise de Requisitos de Servidor: Smart Core Assistant Painel

Este documento detalha os requisitos de hardware e software para a implantação do sistema **Smart Core Assistant Painel** em dois cenários distintos: um servidor robusto para processamento de IA local e um servidor otimizado para uso de APIs externas.

---

## 1. Visão Geral da Arquitetura

O sistema é composto pelos seguintes serviços principais que consomem recursos:
*   **Aplicação Principal:** Django 5.x (Python 3.13+)
*   **Banco de Dados:** PostgreSQL 16+ com extensão `pgvector` (Armazenamento Relacional + Vetorial)
*   **Cache e Filas:** Redis 6.2+
*   **Workers Assíncronos:** Django-Q2 Cluster (Processamento de tarefas em background)
*   **Integrações:** Evolution API (Gateway WhatsApp - Node.js)

---

## 2. Cenário A: Servidor Robusto (IA Local)
**Objetivo:** Executar Grandes Modelos de Linguagem (LLMs) localmente (ex: Llama-3-70b-Quantized, Mixtral 8x7b, ou similar "gpt-0ss20gb" ~20GB+ VRAM) para máxima privacidade e zero custo por token.

### 🖥️ Hardware Recomendado

| Componente | Especificação Recomendada | Justificativa |
| :--- | :--- | :--- |
| **GPU (Placa de Vídeo)** | **NVIDIA RTX 3090 / 4090 (24GB VRAM)** ou A6000/A100 | **Crítico.** Para rodar um modelo de ~20GB com performance aceitável, é necessário carregar os pesos inteiramente na VRAM. 24GB é o mínimo para modelos de médio/grande porte quantizados. |
| **Processador (CPU)** | **16 Cores / 32 Threads** (ex: AMD Ryzen 9 7950X ou Intel Core i9-14900K) | O pré-processamento de dados, ingestão de documentos (RAG) e o banco de dados vetorial demandam alto paralelismo. |
| **Memória RAM** | **64GB DDR5** | Necessário para o SO, Banco de Dados, Cache e para "transbordar" o modelo da GPU se necessário (offloading), embora isso reduza a performance. |
| **Armazenamento** | **2TB NVMe SSD (Gen 4/5)** | Modelos de IA são grandes (20GB-100GB). O banco vetorial também cresce rápido. A velocidade de leitura (I/O) impacta diretamente no tempo de carregamento do modelo. |
| **Rede** | 1 Gbps (Link Dedicado) | Importante se houver alto tráfego de mídia (imagens/áudios) no WhatsApp. |

### 🛠️ Stack de Software Adicional
*   **Drivers:** NVIDIA Drivers (versão mais recente)
*   **Runtime:** NVIDIA Container Toolkit (para Docker acessar a GPU)
*   **Inference Engine:** Ollama ou vLLM (otimizados para produção)

---

## 3. Cenário B: Servidor Simples (IA via API)
**Objetivo:** Hospedar o sistema com custo-benefício, delegando a inteligência para APIs externas (OpenAI, Groq, Anthropic). Ideal para escalar sem gerenciar hardware complexo.

### 🖥️ Hardware Recomendado

| Componente | Especificação Recomendada | Justificativa |
| :--- | :--- | :--- |
| **GPU (Placa de Vídeo)** | **N/A (Não necessária)** | Todo o processamento pesado de IA é feito via API externa. |
| **Processador (CPU)** | **4 a 8 vCPUs** (ex: AWS t3.xlarge ou DigitalOcean CPU-Optimized) | Suficiente para lidar com as requisições HTTP do Django, workers do Celery/Django-Q e o banco de dados. |
| **Memória RAM** | **16GB a 32GB** | O PostgreSQL e o Redis consomem memória baseada no volume de dados. 16GB é o ponto de partida seguro; 32GB oferece folga para cache. |
| **Armazenamento** | **256GB a 512GB SSD** | Suficiente para o sistema operacional, logs, banco de dados e arquivos de mídia do WhatsApp. |
| **Rede** | 100 Mbps+ | Estável para garantir baixa latência na comunicação com as APIs da OpenAI/Groq. |

### 💰 Estimativa de Custo (Nuvem)
*   **VPS/Cloud:** ~$40 - $80 USD/mês (dependendo do provedor: Hetzner, DigitalOcean, AWS).
*   **Custo Variável:** Chaves de API (pago por uso).

---

## 4. Cenário C: Servidor Local (Híbrido)
**Objetivo:** Rodar o sistema dentro da empresa (On-Premise) usando hardware comum, mas conectando-se a APIs externas para a inteligência. Ideal para escritórios que já possuem um computador "sobrando" e querem economizar com nuvem.

### 🖥️ Hardware Recomendado

| Componente | Especificação Recomendada | Justificativa |
| :--- | :--- | :--- |
| **GPU (Placa de Vídeo)** | **N/A (Não necessária)** | Processamento de IA é externo. |
| **Processador (CPU)** | **Intel Core i5/i7 (8ª Geração+) ou Ryzen 5 (3000+)** | Qualquer desktop moderno de médio porte consegue rodar os containers do sistema tranquilamente. |
| **Memória RAM** | **16GB DDR4** | Mínimo recomendável para rodar Docker Desktop no Windows/Linux com conforto. |
| **Armazenamento** | **256GB SSD** | Essencial ser SSD para performance do banco de dados. HD mecânico deixará o sistema lento. |
| **Rede** | Conexão de Fibra Estável | O servidor precisa estar sempre online para receber Webhooks do WhatsApp e Trello. |

### ⚠️ Considerações Importantes
*   **Exposição na Internet:** Para receber Webhooks (WhatsApp/Trello), este computador precisará de um **IP Fixo** ou usar um túnel seguro como **Cloudflare Tunnel** ou **Ngrok** (versão paga para estabilidade).
*   **Energia:** Requer No-Break para evitar quedas.

---

## 5. Cenário D: Nuvem Mínima (Small Business)
**Objetivo:** O menor custo possível em nuvem para uma empresa pequena (ex: < 500 atendimentos/mês), mantendo a estabilidade profissional.

### 🖥️ Hardware Recomendado (VPS)

| Componente | Especificação Mínima | Justificativa |
| :--- | :--- | :--- |
| **CPU** | **2 vCPUs** | Menos que isso pode causar travamentos durante o deploy ou picos de uso. |
| **Memória RAM** | **4GB a 8GB** | 4GB é o limite estrito (requer configuração agressiva de SWAP). **8GB é o recomendado** para evitar "OOM Kills" (Out of Memory). |
| **Armazenamento** | **80GB NVMe** | Espaço suficiente para o sistema e alguns meses de logs/mídia. |

### 💰 Estimativa de Custo
*   **VPS (Hetzner/Contabo):** ~$10 - $15 USD/mês.
*   **VPS (AWS/Azure/Google):** ~$30 - $50 USD/mês (instâncias t3.medium ou similar).

---

## 6. Resumo Comparativo

| Característica | A. Robusto (Local IA) | B. Simples (Cloud API) | C. Local (Híbrido) | D. Nuvem Mínima |
| :--- | :--- | :--- | :--- | :--- |
| **Investimento Inicial** | Alto (Hardware) | Baixo | Zero (Hardware Existente) | Baixo |
| **Custo Mensal** | Energia | Hospedagem ($40+) | Energia + Tunnel | Hospedagem ($10+) |
| **Privacidade** | **Total** | Parcial | Parcial | Parcial |
| **Complexidade** | Alta | Média | Média (Rede) | Baixa |
| **Escalabilidade** | Limitada ao Hardware | Alta | Limitada ao Hardware | Baixa |

## 7. Recomendação Final

*   **Cenário A:** Para privacidade total e alto volume.
*   **Cenário B:** O padrão ouro para empresas estabelecidas. Equilíbrio perfeito.
*   **Cenário C:** Ótimo para testes ou empresas com orçamento zero para infra, mas requer cuidado com a rede (Tunneling).
*   **Cenário D:** Para startups ou pequenas operações que querem profissionalismo (Nuvem) gastando pouco.
