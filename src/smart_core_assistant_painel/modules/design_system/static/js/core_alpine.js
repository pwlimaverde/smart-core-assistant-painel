/**
 * Core Alpine.js Design System Helpers
 * Centraliza os stores de modal, notificações e funções utilitárias.
 *
 * IMPORTANTE: este arquivo é carregado como script CLÁSSICO (sem
 * `type="module"`). NÃO usar `export`/`import` aqui — em script clássico
 * isso gera SyntaxError que aborta o arquivo inteiro e impede o registro
 * de `Alpine.store`/`Alpine.directive` no `alpine:init`. Helpers utilitários
 * são expostos via `window.DesignSystem`.
 */
(function () {
  'use strict';

document.addEventListener('alpine:init', () => {
  // Store global de notificações (toasts)
  Alpine.store('notifications', {
    items: [],
    push(type, msg, title = '') {
      const id = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 9);
      this.items.push({ id, type, msg, title: title || (type === 'success' ? 'Sucesso' : type === 'danger' ? 'Erro' : 'Informação') });
      setTimeout(() => this.dismiss(id), 4000);
    },
    dismiss(id) {
      this.items = this.items.filter(i => i.id !== id);
    },
  });

  // Store global para gerenciar abertura e payload de modais
  Alpine.store('modal', {
    open: false,
    name: null,
    payload: null,
    show(name, payload = null) {
      this.name = name;
      this.payload = payload;
      this.open = true;
    },
    close() {
      this.open = false;
      this.name = null;
      this.payload = null;
    },
  });

  // Diretiva para formatação de data de forma relativa simples
  Alpine.directive('format-date', (el, { expression }, { evaluate }) => {
    const value = evaluate(expression);
    if (!value) return;
    
    const date = new Date(value);
    if (isNaN(date.getTime())) return;
    
    el.textContent = formatRelative(date);
  });
});

/**
 * Formata um número de telefone no padrão brasileiro.
 * Exemplo: 5511912345678 -> +55 (11) 91234-5678
 */
function formatPhone(num) {
  const cleaned = String(num).replace(/\D/g, '');
  const match = cleaned.match(/^55?(\d{2})(\d{4,5})(\d{4})$/);
  return match ? `+55 (${match[1]}) ${match[2]}-${match[3]}` : num;
}

/**
 * Cria uma função debounce para limitar a frequência de chamadas.
 */
function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Retorna uma string relativa simples para a data (ex: "Há 5 min", "Ontem às 14:32")
 */
function formatRelative(date) {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHrs = Math.floor(diffMin / 60);
  
  if (diffSec < 60) return 'Agora mesmo';
  if (diffMin < 60) return `Há ${diffMin} min`;
  if (diffHrs < 24) return `Há ${diffHrs} h`;
  
  const options = { hour: '2-digit', minute: '2-digit' };
  if (diffHrs < 48) return `Ontem às ${date.toLocaleTimeString('pt-BR', options)}`;

  return date.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' });
}

  // Expõe utilitários globalmente (substitui os antigos `export`).
  window.DesignSystem = Object.assign(window.DesignSystem || {}, {
    formatPhone,
    debounce,
    formatRelative,
  });
})();
