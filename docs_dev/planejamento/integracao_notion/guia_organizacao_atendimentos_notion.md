# Guia de Organização de Atendimentos no Notion

Este guia explica como utilizar o Notion para organizar sua central de atendimento, clientes e operação, usando a infraestrutura criada automaticamente pelo projeto.

## Objetivo
- Centralizar atendimentos em um formato simples e replicável para outras empresas.
- Usar bancos de dados do Notion (Clientes, Atendentes, Departamentos, Atendimentos, Mensagens) com relações.
- Permitir criação automática de atendimentos a partir de novas mensagens e migração dos dados existentes do Django.

## Estrutura de Bancos de Dados
- Clientes: Nome, Telefone, Email, Ativo, Última Interação, relação com Atendimentos.
- Departamentos: Nome, Código.
- Atendentes: Nome, Telefone, Email, Ativo, relação com Departamentos.
- Atendimentos: Assunto (título), Status, Prioridade, Contato, Departamento, Agente, Datas (início/fim/última), Avaliação, Tags, Origem.
- Mensagens: Resumo (título), Conteúdo (rich text), Tipo, Remetente, Recebida em, relação com Atendimento.

## Visões sugeridas (Notion)
- Atendimentos por Status: Group by `Status` para visualizar como Kanban (Fila, Em Atendimento, Aguardando Retorno, Resolvido, Cancelado).
- Meus Atendimentos: Filtro `Agente` = você.
- Pendências: Filtro `Status` ∈ {Em Atendimento, Aguardando Retorno} e `Última mensagem` > 24h.
- SLA/Envelhecimento: Ordenar por `Última mensagem` ascendente.

> Observação: o Notion API não cria Views programaticamente. Crie-as manualmente dentro do banco de `Atendimentos` conforme as sugestões acima.

## Fluxo de Uso (Dia a Dia)
1. Abrir o banco `Atendimentos` e usar a visão Kanban por `Status`.
2. Criar novos atendimentos:
   - Duplique a página "Template de Atendimento" dentro do banco.
   - Preencha `Contato`, `Departamento`, `Agente` e `Assunto`.
   - Defina `Prioridade` e mantenha `Status` em "Fila" até iniciar.
3. Trabalhar nos cartões:
   - Arraste entre colunas de `Status` conforme o andamento.
   - Registre mensagens e eventos:
     - Use o banco `Mensagens` e relacione ao `Atendimento`.
     - Ou adicione blocos de texto na página do atendimento para notas rápidas.
4. Encerrar:
   - Marque `Status` como "Resolvido" ou "Cancelado" e preencha `Data fim`.

## Automação (Projeto)
- Comando `setup_notion` cria toda a infraestrutura no Notion e salva os IDs em `configs/notion_schema.json`.
- Comando `export_to_notion` migra Clientes, Departamentos, Atendentes e Atendimentos do Django para Notion, mantendo relações.
- Criação automática de atendimentos a partir de mensagens:
  - O projeto possui client Notion e exemplos para `POST /v1/pages`. Integrações podem chamar o client quando novas mensagens forem recebidas (WhatsApp/Email/Web), abrindo um cartão na coluna "Fila".

## Boas Práticas
- Status: use apenas os estados pré-definidos para manter relatórios consistentes.
- Relações: sempre vincule `Contato`, `Agente` e `Departamento` para facilitar filtros.
- Prioridade: utilize `Urgente` com parcimônia; revise o critério periodicamente.
- Observabilidade: registre `Última mensagem` para ordenar e priorizar follow-ups.
- Segurança: a integração usa `NOTION_TOKEN` e `NOTION_PAGE_ID` do `.env`. Não compartilhe o token.

## Replicação para outras empresas
- Ao clonar o projeto, basta definir `NOTION_TOKEN` e `NOTION_PAGE_ID` no `.env`.
- Execute `python manage.py setup_notion` para criar bancos.
- Execute `python manage.py export_to_notion` para migrar dados existentes.
- Personalize prioridades, tags e cores diretamente no banco de `Atendimentos` no Notion conforme sua operação.