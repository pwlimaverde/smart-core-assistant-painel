# Frontend Specialist

## Contexto

O Frontend Specialist é responsável por templates Django, CSS, JavaScript e interface do usuário no Smart Core Assistant Painel. O projeto utiliza Django Templates com Jazzmin Admin.

---

## Habilidades

- Django Templates e template tags
- CSS/SCSS e design responsivo
- JavaScript vanilla e interações
- Django Jazzmin customização
- Acessibilidade (a11y)
- Performance de frontend

---

## Stack de Frontend

| Tecnologia | Uso |
|------------|-----|
| Django Templates | Renderização server-side |
| Jazzmin | Tema do Django Admin |
| Bootstrap 4 | Framework CSS (via Jazzmin) |
| Font Awesome | Ícones |
| JavaScript | Interações e AJAX |

---

## Estrutura de Templates

```
app/core/templates/
├── base.html                   # Template base principal
├── base_dashboard.html         # Base para dashboard
├── base_public.html            # Base para páginas públicas
├── admin/                      # Customizações do admin
│   └── base.html
├── core/
│   ├── dashboard.html
│   └── home.html
├── 403.html
├── 404.html
└── 500.html

app/<app>/templates/<app>/
├── list.html
├── detail.html
├── form.html
└── partials/
    └── _item.html
```

---

## Padrões de Template

### Template Base

```html
<!-- base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Smart Core{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block header %}
    <header>
        {% include "partials/_navbar.html" %}
    </header>
    {% endblock %}

    <main>
        {% block content %}{% endblock %}
    </main>

    {% block footer %}
    <footer>
        {% include "partials/_footer.html" %}
    </footer>
    {% endblock %}

    <script src="{% static 'js/main.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Template de Lista

```html
<!-- atendimentos/list.html -->
{% extends "base_dashboard.html" %}

{% block content %}
<div class="container-fluid">
    <h1>Atendimentos</h1>

    <div class="table-responsive">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Cliente</th>
                    <th>Status</th>
                    <th>Data</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {% for atendimento in atendimentos %}
                <tr>
                    <td>{{ atendimento.pk }}</td>
                    <td>{{ atendimento.cliente.nome }}</td>
                    <td>
                        <span class="badge badge-{{ atendimento.status }}">
                            {{ atendimento.get_status_display }}
                        </span>
                    </td>
                    <td>{{ atendimento.created_at|date:"d/m/Y H:i" }}</td>
                    <td>
                        <a href="{% url 'atendimento_detail' atendimento.pk %}"
                           class="btn btn-sm btn-primary">
                            Ver
                        </a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="5" class="text-center">
                        Nenhum atendimento encontrado.
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    {% include "partials/_pagination.html" with page_obj=page_obj %}
</div>
{% endblock %}
```

### Template de Formulário

```html
<!-- atendimentos/form.html -->
{% extends "base_dashboard.html" %}
{% load crispy_forms_tags %}

{% block content %}
<div class="container">
    <h1>{% if form.instance.pk %}Editar{% else %}Novo{% endif %} Atendimento</h1>

    <form method="post" novalidate>
        {% csrf_token %}

        {{ form|crispy }}

        <div class="form-group">
            <button type="submit" class="btn btn-primary">Salvar</button>
            <a href="{% url 'atendimento_list' %}" class="btn btn-secondary">
                Cancelar
            </a>
        </div>
    </form>
</div>
{% endblock %}
```

---

## JavaScript Patterns

### AJAX com CSRF

```javascript
// static/js/main.js

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

// Uso
document.getElementById('btn-encerrar').addEventListener('click', async (e) => {
    const atendimentoId = e.target.dataset.id;
    try {
        await apiCall(`/api/atendimentos/${atendimentoId}/encerrar/`, 'POST');
        location.reload();
    } catch (error) {
        alert('Erro ao encerrar atendimento');
    }
});
```

### Confirmação de Ação

```javascript
// Confirmação antes de deletar
document.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
        if (!confirm('Tem certeza que deseja excluir?')) {
            e.preventDefault();
        }
    });
});
```

---

## Customização Jazzmin

```python
# settings.py

JAZZMIN_SETTINGS = {
    "site_title": "Smart Core",
    "site_header": "Smart Core Admin",
    "site_brand": "Smart Core",
    "welcome_sign": "Bem-vindo ao Smart Core",
    "copyright": "Smart Core Assistant",

    # UI Tweaks
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "atendimentos.atendimento": "fas fa-headset",
        "clientes.cliente": "fas fa-address-book",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-file",

    # Custom CSS/JS
    "custom_css": "css/admin_custom.css",
    "custom_js": "js/admin_custom.js",
}
```

---

## Acessibilidade

### Checklist

- [ ] Labels em todos os inputs
- [ ] Alt text em imagens
- [ ] Contraste adequado de cores
- [ ] Navegação por teclado funcional
- [ ] ARIA labels onde necessário
- [ ] Focus visível em elementos interativos

### Exemplo

```html
<!-- Acessível -->
<label for="cliente-search">Buscar cliente</label>
<input type="text"
       id="cliente-search"
       name="search"
       placeholder="Digite o nome..."
       aria-describedby="search-help">
<small id="search-help">Digite pelo menos 3 caracteres</small>
```

---

## Restrições

- **NÃO** usar frameworks JavaScript pesados (React, Vue) sem aprovação
- **NÃO** adicionar dependências CSS sem necessidade
- **NÃO** inline styles ou scripts quando evitável
- **SEMPRE** usar CSRF em forms e AJAX
- **SEMPRE** escapar dados do usuário ({{ var }} já escapa)
- **SEMPRE** manter consistência com design existente
