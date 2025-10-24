# Sugestões de Commit - Integração Notion v4.0

**Versão:** 4.0  
**Data:** Janeiro 2025  
**Tipo:** Refatoração e Simplificação

---

## 📋 Commits Principais por Fase

### Fase 1: Estrutura Base do App

```bash
# Commit 1: Criação do app notion_sync
feat(notion): create notion_sync app structure
- Create app directory structure
- Add __init__.py with imports
- Configure in INSTALLED_APPS
- Add basic apps.py configuration
```

```bash
# Commit 2: Models essenciais
feat(notion): implement core models
- Add NotionDatabaseConfig model
- Add NotionObjectMapping model
- Add SyncLog model
- Add indexes and meta configurations
- Create initial migrations
```

### Fase 2: Shadow Models

```bash
# Commit 3: Shadow Models principais
feat(notion): implement shadow models
- Add ContatoSync model
- Add ClienteSync model  
- Add AtendimentoSync model
- Add related managers and methods
- Add performance optimizations
```

```bash
# Commit 4: Shadow Models secundários
feat(notion): add remaining shadow models
- Add DepartamentoSync model
- Add AtendenteSync model
- Add MensagemSync model
- Add model-specific methods and properties
- Create migrations for all models
```

### Fase 3: Mappers

```bash
# Commit 5: Mappers de transformação
feat(notion): implement data mappers
- Add ContatoMapper class
- Add AtendimentoMapper class
- Add ClienteMapper class
- Add DepartamentoMapper class
- Add validation and sanitization methods
```

```bash
# Commit 6: Mappers avançados
feat(notion): complete mapper implementations
- Add AtendenteMapper class
- Add MensagemMapper class
- Add base mapper utilities
- Add field transformation helpers
- Add comprehensive test coverage
```

### Fase 4: Serviços e Tasks

```bash
# Commit 7: Serviço principal Notion
feat(notion): implement NotionSyncService
- Add NotionSyncService class
- Implement create_page method
- Implement update_page method
- Implement get_page method
- Add error handling and retry logic
```

```bash
# Commit 8: Tasks Celery
feat(notion): add celery tasks
- Add sync_to_notion task
- Add sync_from_notion task
- Add cleanup_logs task
- Add retry with backoff
- Add task monitoring
```

### Fase 5: Signals e Webhook

```bash
# Commit 9: Django signals
feat(notion): implement django signals
- Add post_save handlers for main models
- Add pre_delete handlers
- Add loop prevention logic
- Add signal configuration
```

```bash
# Commit 10: Webhook endpoint
feat(notion): add notion webhook support
- Add webhook view for notion events
- Implement page.created handler
- Implement page.updated handler
- Add webhook verification
```

### Fase 6: Configuração e Deploy

```bash
# Commit 11: Configurações
feat(notion): add configuration
- Add NOTION_* environment variables
- Add celery beat schedules
- Add admin interface
- Add management commands
```

```bash
# Commit 12: Documentação
docs(notion): add integration documentation
- Add models documentation
- Add mapper examples
- Add setup instructions
- Add troubleshooting guide
```

---

## 🏷️ Padrão de Nomenclatura

### Tipos de Commit

| Tipo | Uso | Exemplos |
|------|-----|----------|
| `feat` | Nova funcionalidade | `feat(notion): add shadow models` |
| `fix` | Correção de bug | `fix(notion): handle empty external_id` |
| `refactor` | Refatoração | `refactor(notion): optimize mapper methods` |
| `docs` | Documentação | `docs(notion): update API examples` |
| `test` | Testes | `test(notion): add mapper unit tests` |
| `chore` | Configuração | `chore(notion): add dependencies` |

### Escopo

- `notion` - Para tudo relacionado ao app notion_sync
- `models` - Mudanças nos models
- `mappers` - Mudanças nos mappers
- `tasks` - Mudanças nas tasks Celery
- `webhook` - Mudanças no webhook endpoint

---

## 📝 Exemplos de Commits Detalhados

### Commit de Funcionalidade Principal

```bash
feat(notion): implement ContatoMapper with full transformation support

- Add ContatoMapper class with Django ↔ Notion transformation
- Implement to_notion_properties method
- Implement from_notion_properties method  
- Add phone number normalization
- Add email validation
- Add text truncation for rich_text fields
- Add status mapping between Django choices and Notion selects
- Add comprehensive unit tests
- Add validation for required fields

Fixes: #123
Related: #124
```

### Commit de Correção

```bash
fix(notion): handle missing external_id in webhook processing

- Add null check for external_id in NotionObjectMapping
- Prevent 500 errors when webhook receives unmapped pages
- Add graceful handling of orphan Notion pages
- Add logging for debugging missing mappings

Closes: #156
```

### Commit de Refatoração

```bash
refactor(notion): optimize shadow model queries with select_related

- Add select_related to ContatoSyncManager.pending_sync()
- Add prefetch_related for cliente relationships
- Reduce database queries from 15 to 3 per sync batch
- Improve sync performance by 60%
- Add query count tests

Performance improvement for large datasets
```

---

## 🔄 Fluxo de Branches

### Feature Branch Pattern

```bash
# Criar branch de feature
git checkout -b feature/notion-integration

# Commits pequenos e focados
git commit -m "feat(notion): create app structure"
git commit -m "feat(notion): add NotionDatabaseConfig model"
git commit -m "feat(notion): add ContatoSync shadow model"

# Merge após revisão
git checkout develop
git merge feature/notion-integration
```

### Pull Request Template

```markdown
## Descrição
Implementação da integração com Notion usando abordagem simplificada de shadow models.

## Mudanças
- ✅ Models redefinidos com foco em performance
- ✅ Mappers específicos por modelo
- ✅ Sincronização assíncrona via Celery
- ✅ Tratamento de erros e retry

## Testes
- [x] Unit tests para mappers
- [x] Integration tests para services
- [x] Tests para shadow models
- [ ] Manual testing (aguardando ambiente)

## Checklist
- [x] Code follows style guidelines
- [x] Self-review completed
- [x] Tests pass locally
- [x] Documentation updated
```

---

## 📊 Métricas de Qualidade

### Código

- **Coverage mínimo:** 80%
- **Complexidade ciclomática:** < 10 por método
- **Máximo de linhas por método:** 50
- **Máximo de parâmetros:** 5

### Commits

- **Tamanho médio:** < 500 linhas alteradas
- **Mensagens descritivas:** Sim, sempre
- **Code review:** Obrigatório
- **Automated tests:** Obrigatórios

---

## 🎯 Próximos Commits Esperados

```bash
# Após implementação base
feat(notion): add admin interface for sync management
feat(notion): implement batch sync for performance
feat(notion): add monitoring dashboard

# Melhorias futuras  
feat(notion): add conflict resolution for bidirectional sync
feat(notion): implement selective field sync
feat(notion): add audit trail for data changes
```

---

## 📋 Resumo da Refatoração

### Mudanças Principais

1. **Simplificação:** 8 arquivos → 4 arquivos focados
2. **Models:** 6 complexos → 4 essenciais + shadow models
3. **Abordagem:** Over-engineered → Foco no essencial
4. **Documentação:** 5.000 linhas → 2.000 linhas diretas
5. **Implementação:** 22-29 dias → 15-20 dias

### Benefícios

✅ **Manutenibilidade:** Código mais simples e focado  
✅ **Performance:** Shadow models com cache  
✅ **Flexibilidade:** Mappers modulares  
✅ **Robustez:** Tratamento de erros simplificado  
✅ **Testabilidade:** Componentes isolados  

---

**Status:** ✅ Sugestões de commit definidas  
**Próximo passo:** Iniciar implementação da Fase 1  
