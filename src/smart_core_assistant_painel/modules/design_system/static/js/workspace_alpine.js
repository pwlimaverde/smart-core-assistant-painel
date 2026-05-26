/*
 * Store Alpine.js do Workspace de Atendimento Unificado (Core Shell).
 *
 * - Gerencia o estado comum e a orquestração do layout.
 * - Centraliza a conexão SSE única por tenant.
 * - Roteia os filtros de busca e as configurações de visualização.
 *
 * Idioma dos comentários: Português. Identificadores: Inglês.
 */
(function () {
    'use strict';

    var LS_FOCUS = 'workspace.focusMode';
    var LS_THEME = 'workspace.theme';
    var LS_DENSITY = 'workspace.density';

    function getCookie(name) {
        const match = document.cookie.match(
            new RegExp('(?:^|; )' + name.replace(/[.$?*|{}()[\]\\\/+^]/g, '\\$&') + '=([^;]*)')
        );
        return match ? decodeURIComponent(match[1]) : '';
    }

    function readLS(key, fallback) {
        try { return localStorage.getItem(key) || fallback; } catch (_) { return fallback; }
    }
    function writeLS(key, value) {
        try { localStorage.setItem(key, value); } catch (_) { /* ignore */ }
    }

    function jsonFetch(url, init) {
        const cfg = init || {};
        cfg.credentials = 'same-origin';
        cfg.headers = Object.assign(
            { 'Accept': 'application/json' },
            cfg.headers || {}
        );
        if (cfg.method && cfg.method !== 'GET') {
            cfg.headers['Content-Type'] = 'application/json';
            cfg.headers['X-CSRFToken'] = getCookie('csrftoken');
        }
        return fetch(url, cfg).then(function (res) {
            if (!res.ok) {
                return res.json().catch(function () { return {}; }).then(function (body) {
                    const err = new Error(body && body.error ? body.error : 'HTTP ' + res.status);
                    err.status = res.status;
                    err.body = body;
                    throw err;
                });
            }
            return res.json();
        });
    }

    window.workspaceCoreMixin = function (init) {
        return {
            // ─────────────────────────────────────────────────────────
            // Estado do shell (layout, fluxos, lista de conversas, filtros,
            // SSE único, notificações). O estado de domínio chat/kanban vive
            // nos respectivos mixins (workspaceChatMixin / workspaceKanbanMixin),
            // mesclados em workspaceStore via Object.assign (Fase 4).
            // ─────────────────────────────────────────────────────────
            fluxoId: init.fluxoId || null,
            fluxos: [],
            conversations: [],
            search: '',
            filterTag: '',
            endpoints: init.endpoints,
            tenantSlug: init.tenantSlug,
            atendenteId: init.atendenteId,
            atendenteNome: init.atendenteNome,
            detailDrawerOpen: false,

            // SSE único por tenant
            sseConnected: false,
            sse: null,
            _sseRetryDelay: 2000,
            _sseReconnectTimer: null,
            sseEnabled: init.sseEnabled === true,

            // Modos de foco e visualização
            focusMode: readLS(LS_FOCUS, 'split'),
            theme:     readLS(LS_THEME, 'light'),
            density:   readLS(LS_DENSITY, 'normal'),
            showKbdHint: false,
            _hintTimer: null,

            // Notificações e filtros
            unreadCount: 0,
            _unreadDebounce: null,
            filterPopoverOpen: false,
            filters: {
                q: '',
                prioridade: '',
                atendente_id: '',
                etiqueta_id: '',
                apenas_nao_lidos: false,
            },

            init: async function () {
                try {
                    await this.loadFluxos();
                    if (this.fluxoId == null && this.fluxos.length > 0) {
                        this.fluxoId = this.fluxos[0].id;
                    }
                    await Promise.all([
                        this.loadConversations(),
                        this.loadBoard(),
                        this.loadEtiquetas(),
                        this.loadUnreadCount(),
                    ]);
                    if (this.sseEnabled) {
                        this.connectSSE();
                    }
                    this.showKbdHint = true;
                    this._hintTimer = setTimeout(() => { this.showKbdHint = false; }, 5000);
                } catch (exc) {
                    console.error('Falha ao inicializar Workspace Core', exc);
                }
            },

            // Controle de Foco
            setFocus: function (mode) {
                if (['board', 'split', 'chat'].indexOf(mode) === -1) return;
                this.focusMode = mode;
                writeLS(LS_FOCUS, mode);
            },

            minimizeChat: function () { this.setFocus('board'); },

            onEscape: function ($event) {
                if (this.isTypingTarget($event)) return;
                if (this.mediaLightbox.open) { this.closeLightbox(); return; }
                if (this.detailDrawerOpen) { this.detailDrawerOpen = false; return; }
                if (this.focusMode === 'chat')  { this.setFocus('split'); return; }
                if (this.focusMode === 'split') { this.setFocus('board'); return; }
            },

            onToggleInfo: function ($event) {
                if (this.isTypingTarget($event)) return;
                this.detailDrawerOpen = !this.detailDrawerOpen;
            },

            isTypingTarget: function ($event) {
                if (!$event || !$event.target) return false;
                const tag = ($event.target.tagName || '').toUpperCase();
                return tag === 'INPUT' || tag === 'TEXTAREA' || $event.target.isContentEditable;
            },

            setTheme: function (t) {
                this.theme = t;
                writeLS(LS_THEME, t);
            },
            setDensity: function (d) {
                this.density = d;
                writeLS(LS_DENSITY, d);
            },

            // Filtros e Carregamento Base
            onFluxoChange: function () {
                return Promise.all([
                    this.loadConversations(),
                    this.loadBoard(),
                ]);
            },

            loadFluxos: function () {
                return jsonFetch(this.endpoints.fluxos).then((data) => {
                    this.fluxos = data.fluxos || [];
                });
            },

            _buildFiltersParams: function (extraParams) {
                const params = new URLSearchParams();
                if (this.search) params.set('q', this.search);
                else if (this.filters.q) params.set('q', this.filters.q);
                if (this.filterTag) params.set('tag', this.filterTag);
                if (this.filters.prioridade) params.set('prioridade', this.filters.prioridade);
                if (this.filters.atendente_id) params.set('atendente_id', this.filters.atendente_id);
                if (this.filters.etiqueta_id) params.set('etiqueta_id', this.filters.etiqueta_id);
                if (this.filters.apenas_nao_lidos) params.set('apenas_nao_lidos', '1');
                if (extraParams) {
                    Object.keys(extraParams).forEach((k) => {
                        if (extraParams[k] != null) params.set(k, extraParams[k]);
                    });
                }
                return params;
            },

            loadConversations: function () {
                const params = this._buildFiltersParams(
                    this.fluxoId != null ? { fluxo: this.fluxoId } : null
                );
                const url = this.endpoints.conversations + '?' + params.toString();
                return jsonFetch(url).then((data) => {
                    this.conversations = data.conversations || [];
                });
            },

            // SSE único e roteamento de eventos
            connectSSE: function () {
                if (!this.endpoints.sse) return;
                this._sseRetryDelay = this._sseRetryDelay || 2000;
                try {
                    this.sse = new EventSource(this.endpoints.sse);
                } catch (exc) {
                    console.warn('SSE indisponível:', exc);
                    this._scheduleSSEReconnect();
                    return;
                }
                const handle = (eventType) => (ev) => {
                    let data = {};
                    try { data = JSON.parse(ev.data); } catch (_) { data = {}; }
                    this.handleSSE(eventType, data);
                };
                this.sse.addEventListener('open', () => {
                    this.sseConnected = true;
                    this._sseRetryDelay = 2000;
                });
                this.sse.addEventListener('error', () => {
                    this.sseConnected = false;
                    try { this.sse && this.sse.close(); } catch (_) {}
                    this._scheduleSSEReconnect();
                });
                this.sse.addEventListener('message.new', handle('message.new'));
                this.sse.addEventListener('message.updated', handle('message.updated'));
                this.sse.addEventListener('board.moved', handle('board.moved'));
                this.sse.addEventListener('atendimento.created', handle('atendimento.created'));
                this.sse.addEventListener('atendimento.updated', handle('atendimento.updated'));
                this.sse.addEventListener('custom_field.updated', handle('custom_field.updated'));
                this.sse.addEventListener('presence.update', handle('presence.update'));
            },

            _scheduleSSEReconnect: function () {
                if (this._sseReconnectTimer) return;
                const delay = Math.min(this._sseRetryDelay || 2000, 30000);
                this._sseReconnectTimer = setTimeout(() => {
                    this._sseReconnectTimer = null;
                    this._sseRetryDelay = Math.min(delay * 2, 30000);
                    this.connectSSE();
                }, delay);
            },

            handleSSE: function (eventType, data) {
                if (!data) return;
                switch (eventType) {
                    case 'message.new':
                    case 'message.updated':
                        const conv = this.conversations.find((c) => c.atendimento_id === data.atendimento_id);
                        if (conv) {
                            conv.preview_msg = data.preview || conv.preview_msg;
                            conv.preview_remetente = data.remetente;
                            conv.data_ultima_mensagem = data.timestamp;
                            if (data.remetente === 'contato' &&
                                (!this.activeConv || this.activeConv.atendimento_id !== data.atendimento_id)) {
                                conv.nao_lidos = (conv.nao_lidos || 0) + 1;
                            }
                        }
                        if (this.activeConv && this.activeConv.atendimento_id === data.atendimento_id) {
                            if (typeof this.loadMessages === 'function') {
                                this.loadMessages(data.atendimento_id).then(() => {
                                    if (typeof this.scrollMessagesBottom === 'function') {
                                        this.$nextTick(() => this.scrollMessagesBottom());
                                    }
                                });
                            }
                        } else if (data.remetente === 'contato') {
                            this._scheduleUnreadRefresh();
                        }
                        break;
                    case 'board.moved':
                    case 'atendimento.updated':
                    case 'atendimento.created':
                        if (!this.isDragging && typeof this.loadBoard === 'function') {
                            this.loadBoard();
                        }
                        this.loadConversations();
                        break;
                    case 'custom_field.updated':
                        if (this.activeConv &&
                            this.activeConv.atendimento_id === data.atendimento_id &&
                            typeof this.loadDetail === 'function') {
                            this.loadDetail(data.atendimento_id);
                        }
                        break;
                    case 'presence.update':
                        if (typeof this.handlePresenceUpdate === 'function') {
                            this.handlePresenceUpdate(data);
                        }
                        break;
                }
            },

            // Sino de Notificações
            loadUnreadCount: function () {
                const url = (this.endpoints.unreadCount || '/workspace/api/notifications/unread-count/');
                return jsonFetch(url).then((data) => {
                    this.unreadCount = data.total || 0;
                }).catch(() => { /* não-fatal */ });
            },

            _scheduleUnreadRefresh: function () {
                if (this._unreadDebounce) clearTimeout(this._unreadDebounce);
                this._unreadDebounce = setTimeout(() => {
                    this._unreadDebounce = null;
                    this.loadUnreadCount();
                }, 500);
            },

            // Filtros Adicionais
            applyFilters: function () {
                this.filterPopoverOpen = false;
                return Promise.all([
                    this.loadConversations(),
                    this.loadBoard(),
                ]);
            },

            clearFilters: function () {
                this.filters = {
                    q: '',
                    prioridade: '',
                    atendente_id: '',
                    etiqueta_id: '',
                    apenas_nao_lidos: false,
                };
                this.search = '';
                return this.applyFilters();
            },

            activeFiltersCount: function () {
                let n = 0;
                if (this.filters.q) n++;
                if (this.filters.prioridade) n++;
                if (this.filters.atendente_id) n++;
                if (this.filters.etiqueta_id) n++;
                if (this.filters.apenas_nao_lidos) n++;
                return n;
            }
        };
    };

    window.workspaceStore = function(init) {
        return Object.assign({},
            window.workspaceCoreMixin(init),
            window.workspaceChatMixin ? window.workspaceChatMixin() : {},
            window.workspaceKanbanMixin ? window.workspaceKanbanMixin() : {}
        );
    };
})();
