# /security - Auditoria de Segurança

Realiza auditoria de segurança seguindo OWASP Top 10.

## Instruções

1. **Use o skill de security-audit**
   - `.context/skills/security-audit/SKILL.md`

2. **Consulte o agente especializado**
   - `.context/agents/security-auditor.md`

3. **OWASP Top 10 Checklist**
   - A01: Broken Access Control
   - A02: Cryptographic Failures
   - A03: Injection
   - A04: Insecure Design
   - A05: Security Misconfiguration
   - A06: Vulnerable Components
   - A07: Authentication Failures
   - A08: Data Integrity Failures
   - A09: Logging Failures
   - A10: SSRF

4. **Ferramentas**
   ```bash
   pip-audit                    # Dependências
   bandit -r src/               # Análise estática
   python manage.py check --deploy  # Config Django
   ```

## Parâmetros

- `$ARGUMENTS`: Módulo ou escopo da auditoria

## Exemplo de Uso

```
/security                        # Auditoria completa
/security app/atendimentos    # Audita módulo específico
/security dependencies           # Verifica dependências
```

## Output

Relatório com:
- Vulnerabilidades encontradas
- Severidade (Alta/Média/Baixa)
- Remediação recomendada
