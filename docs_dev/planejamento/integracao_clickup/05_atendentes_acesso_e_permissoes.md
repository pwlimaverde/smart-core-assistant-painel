# Atendentes, Acesso e Permissões (ClickUp)

## Papéis e Acesso
- Workspace: Owner, Admin, Member, Guest.
- Custom Roles: `GET /api/v2/team/{team_id}/customroles` (consultar papéis customizados).
- Space/Folder/List: controlar visibilidade e membros conforme necessidade.

## Provisionamento de Equipe
- Adicionar membros ao Space e, opcionalmente, restringir Folders/Lists.
- Atribuição por Task (`assignees`) e Watchers para notificações.

## Privacidade
- Lists privadas para fluxos sensíveis.
- CF com dados pessoais: armazenar mínimo necessário; usar `.env` e variáveis seguras.

## Webhooks e Auditoria
- `POST /api/v2/team/{team_id}/webhook` para eventos chave.
- Logar mudanças críticas e manter trilha de auditoria.