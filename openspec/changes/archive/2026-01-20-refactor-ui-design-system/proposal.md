# Change: Refatorar UI para Padronizar Design System (Abordagem por Tela)

## Why

A análise inicial identificou inconsistências sistêmicas na interface (falta de sidebar em módulos críticos, navegação quebrada, acessos indevidos). A abordagem anterior por "fases gerais" mostrou-se insuficiente para garantir a qualidade final.
Esta reformulação propõe uma **auditoria e refatoração exaustiva tela a tela**, garantindo que cada view do sistema seja validada individualmente quanto a Design, Usabilidade e Segurança (Permissões).

## What Changes

O trabalho será executado através de uma varredura completa nas rotas da aplicação, dividida em módulos:

1.  **Autenticação**: Login, Signup e Onboarding.
2.  **Dashboards**: Tenant, Gerente e Backoffice.
3.  **Treinamento**: Fluxos de IA e verificação de dados.
4.  **Configurações**: Integrações (Database, Evolution, Trello).
5.  **Gestão de Usuários**: Controle de acesso e time.

Para CADA tela, serão aplicadas/verificadas:

- **MODIFIED**: Herança de template correta (`base_dashboard.html`).
- **MODIFIED**: Padronização de componentes visuais (Design System).
- **VERIFIED**: Auditoria de todos os links e botões de ação.
- **VERIFIED**: Auditoria de permissões (Role-based access control).
- **NEW**: Documentação final da topologia da UI (`UI_MAP.md`).

## Impact

- **Affected specs**: `template-hierarchy`, `navigation-map`, `permission-matrix`.
- **Affected code**: Templates Django em `ui/`, `tenants/` e `evolution_sync/`; Views correspondentes para ajustes de contexto.
