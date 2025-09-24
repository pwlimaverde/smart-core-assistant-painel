# Planejamento da Central de Atendimento

Este diretório contém toda a documentação de planejamento para o desenvolvimento da nova Central de Atendimento do Smart Core Assistant. O objetivo é criar uma solução robusta, escalável e de fácil manutenção, utilizando uma arquitetura monolítica com Django.

## Visão Geral

A Central de Atendimento será um sistema integrado ao painel existente, permitindo o gerenciamento de conversas de clientes que são transferidas de um chatbot para atendimento humano. A interface será baseada em um quadro Kanban, proporcionando uma visualização clara e intuitiva do fluxo de trabalho.

## Documentos de Planejamento

Abaixo estão os documentos que detalham cada aspecto do projeto:

1.  **[Arquitetura Geral (`arquitetura_geral.md`)](arquitetura_geral.md)**
    *   Descreve a arquitetura monolítica baseada em Django, com o uso do Django REST Framework para a API, Django Channels para comunicação em tempo real (WebSockets) e Django Signals para eventos internos. Detalha os componentes principais e como eles interagem.

2.  **[Modelagem de Dados (`modelagem_dados.md`)](modelagem_dados.md)**
    *   Apresenta o diagrama e a descrição detalhada dos modelos de dados que já existem no sistema e que serão utilizados pela Central de Atendimento. Garante o alinhamento com a estrutura de dados atual do projeto, evitando redundâncias.

3.  **[Checklist de Desenvolvimento (`checklist_desenvolvimento.md`)](checklist_desenvolvimento.md)**
    *   Fornece um plano de tarefas detalhado para as equipes de backend e frontend. As tarefas estão alinhadas com a arquitetura e a modelagem de dados definidas, incluindo a implementação da lógica de negócio, APIs, comunicação em tempo real e a interface do usuário.

4.  **[Planejamento de Utilização da UI (`planejamento_utilizacao_ui.md`)](planejamento_utilizacao_ui.md)**
    *   Detalha o design e o fluxo de interação da interface do usuário (UI/UX). Descreve como os painéis Kanban funcionarão para os atendentes e gestores, incluindo a estrutura dos quadros, os cards de atendimento e as transições de status.

## Próximos Passos

Com o planejamento concluído e documentado, a equipe de desenvolvimento pode iniciar a implementação das funcionalidades descritas no `checklist_desenvolvimento.md`, seguindo a arquitetura e a modelagem de dados estabelecidas.