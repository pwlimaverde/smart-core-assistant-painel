# Sugestões de Estruturação de Apps Django

## Estrutura Atual
O app `oraculo` atualmente contém todas as funcionalidades em um único local, incluindo:
- Gestão de atendentes humanos
- Gestão de contatos e clientes
- Fluxo de atendimentos
- Sistema de treinamento da IA
- Configurações de departamentos
- Webhooks e integrações

## Proposta de Divisão em Apps

Para melhor organização e separação de responsabilidades, sugiro a seguinte estrutura:

### 1. **operacional** (Interno)
**Responsabilidade**: Gestão de recursos humanos e infraestrutura interna
**Modelos**: 
- `AtendenteHumano`
- `Departamento`

**Funcionalidades**:
- Gestão de atendentes e suas capacidades
- Administração de departamentos e instâncias
- Controle de disponibilidade e capacidade
- Configurações operacionais

### 2. **clientes** (Externo)
**Responsabilidade**: Gestão de clientes e contatos (público externo)
**Modelos**:
- `Cliente`
- `Contato`

**Funcionalidades**:
- Cadastro e gestão de clientes
- Administração de contatos
- Relacionamento entre clientes e contatos
- Dados cadastrais externos

### 3. **atendimentos**
**Responsabilidade**: Fluxo completo de atendimentos e conversas
**Modelos**:
- `Atendimento`
- `Mensagem`

**Funcionalidades**:
- Controle de fluxo de atendimentos
- Histórico de conversas
- Integração entre operacional e clientes
- Métricas e relatórios

### 4. **treinamento**
**Responsabilidade**: Sistema de treinamento e conhecimento da IA
**Modelos**:
- `Treinamento`
- `Documento`

**Funcionalidades**:
- Gestão de base de conhecimento
- Processamento e vetorização de conteúdo
- Interface administrativa para treinamento

### 5. **webhooks**
**Responsabilidade**: Integrações e recebimento de eventos externos
**Funcionalidades**:
- Webhook do WhatsApp
- Processamento inicial de mensagens
- Validação e roteamento de eventos

### 6. **core**
**Responsabilidade**: Componentes compartilhados e utilitários
**Funcionalidades**:
- Validações comuns
- Utilitários reutilizáveis
- Configurações base
- Signals e handlers globais