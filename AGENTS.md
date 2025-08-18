# Guia de Agente para este Repositório

Este documento fornece diretrizes para agentes de IA como o Jules sobre como trabalhar com este codebase.

## Convenções de Controle de Versão (Git)

Nosso fluxo de trabalho é baseado no GitFlow. É crucial que todas as novas branches criadas sigam estritamente as convenções de nomenclatura abaixo para garantir a consistência do repositório.

### Nomenclatura de Branches

Ao criar uma branch para uma nova tarefa, siga o seguinte padrão:

*   **Features:** Para novas funcionalidades, o nome da branch DEVE começar com `feature/`.
    *   Exemplo: `feature/adicionar-autenticacao-oauth`
*   **Correções de Bugs (Bugfixes):** Para correções de bugs em desenvolvimento, a branch DEVE começar com `bugfix/`.
    *   Exemplo: `bugfix/corrigir-erro-de-login`
*   **Hotfixes:** Para correções urgentes na produção, a branch DEVE começar com `hotfix/`.
    *   Exemplo: `hotfix/resolver-vulnerabilidade-xss`
*   **Releases:** Para preparar uma nova versão de produção, a branch DEVE começar com `release/`.
    *   Exemplo: `release/v1.2.0`

**Instrução para o Jules:** Sempre que você iniciar uma nova tarefa que requer a criação de uma branch, nomeie-a de acordo com as convenções acima, baseando-se no tipo de tarefa solicitada. Por exemplo, uma tarefa para "adicionar um novo endpoint de perfil de usuário" deve ser em uma branch chamada `feature/endpoint-perfil-usuario`.