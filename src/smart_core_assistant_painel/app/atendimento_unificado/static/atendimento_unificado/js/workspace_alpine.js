/*
 * Store Alpine.js do Workspace de Atendimento Unificado.
 *
 * - Gerencia estado de Conversas e Kanban
 * - Consome endpoints JSON declarados em workspace.html
 * - Conecta-se ao stream SSE para atualizações ao vivo
 *
 * Convenções:
 *  - `mode`: 'conversas' | 'kanban'
 *  - `conversations`: lista da sidebar (modo conversas)
 *  - `board`: { etapas: [...], cards: { '<etapa_id>': [...] } }
 *  - `activeConv`: conversa atualmente aberta (chat ativo ou drawer)
 *  - `activeDetail`: payload de /detail/ para o painel direito
 */
(function () {
    'use strict';

    function getCookie(name) {
        const match = document.cookie.match(
            new RegExp('(?:^|; )' + name.replace(/[.$?*|{}()[\]\\\/+^]/g, '\\$&') + '=([^;]*)')
        );
        return match ? decodeURIComponent(match[1]) : '';
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

    function buildConvUrl(base, atendimentoId, suffix) {
        // base é a URL de listagem de conversations e termina com '/'.
        // Ex.: '/workspace/api/conversations/' + 42 + '/messages/'
        const safeBase = base.endsWith('/') ? base : base + '/';
        return safeBase + atendimentoId + '/' + suffix + '/';
    }

    function prioridadeClass(p) {
        switch ((p || '').toLowerCase()) {
            case 'baixa': return 'bg-green-100 text-green-800';
            case 'normal': return 'bg-blue-100 text-blue-800';
            case 'alta': return 'bg-orange-100 text-orange-800';
            case 'urgente': return 'bg-red-100 text-red-800';
            default: return 'bg-stone-100 text-stone-700';
        }
    }

    function intentLabel(it) {
        if (!it) return '';
        if (typeof it === 'string') return it;
        return it.type || it.nome || it.name || JSON.stringify(it);
    }

    function tipoMidiaLabel(tipo) {
        switch (tipo) {
            case 'imageMessage': return '🖼️ Imagem';
            case 'videoMessage': return '🎬 Vídeo';
            case 'audioMessage': return '🎤 Áudio';
            case 'documentMessage': return '📄 Documento';
            case 'stickerMessage': return 'Sticker';
            case 'locationMessage': return '📍 Localização';
            default: return tipo;
        }
    }

    window.workspaceStore = function (init) {
        return {
            mode: 'conversas',
            fluxoId: init.fluxoId || null,
            fluxos: [],
            conversations: [],
            messages: [],
            board: { etapas: [], cards: {} },
            activeConv: null,
            activeDetail: null,
            composer: '',
            search: '',
            sending: false,
            chatDrawerOpen: false,
            sseConnected: false,
            sse: null,
            _sseRetryDelay: 2000,
            _sseReconnectTimer: null,
            endpoints: init.endpoints,
            customFieldsSaving: {},
            tenantSlug: init.tenantSlug,
            atendenteId: init.atendenteId,
            atendenteNome: init.atendenteNome,

            init: async function () {
                try {
                    await this.loadFluxos();
                    if (this.fluxoId == null && this.fluxos.length > 0) {
                        this.fluxoId = this.fluxos[0].id;
                    }
                    await Promise.all([
                        this.loadConversations(),
                        this.loadBoard(),
                    ]);
                    this.connectSSE();
                } catch (exc) {
                    console.error('Falha ao inicializar Workspace', exc);
                }
                this.$watch && this.$watch('mode', (m) => {
                    if (m === 'kanban') this.loadBoard();
                });
            },

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

            loadConversations: function () {
                const params = new URLSearchParams();
                if (this.fluxoId != null) params.set('fluxo', this.fluxoId);
                if (this.search) params.set('q', this.search);
                const url = this.endpoints.conversations + '?' + params.toString();
                return jsonFetch(url).then((data) => {
                    this.conversations = data.conversations || [];
                });
            },

            loadBoard: function () {
                if (this.fluxoId == null) {
                    this.board = { etapas: [], cards: {} };
                    return Promise.resolve();
                }
                const url = this.endpoints.board + '?fluxo=' + this.fluxoId;
                return jsonFetch(url).then((data) => {
                    this.board = data || { etapas: [], cards: {} };
                });
            },

            openConversation: function (id) {
                const conv = this.conversations.find((c) => c.atendimento_id === id);
                this.activeConv = conv || null;
                return Promise.all([
                    this.loadMessages(id),
                    this.loadDetail(id),
                    this.markRead(id),
                ]).then(() => {
                    this.$nextTick(() => this.scrollMessagesBottom());
                });
            },

            openChatDrawer: function (id) {
                this.chatDrawerOpen = true;
                // Sintetiza conversa rasa a partir do card kanban
                let conv = this.conversations.find((c) => c.atendimento_id === id);
                if (!conv) {
                    // Procura entre os cards do board
                    for (const [etapaId, cards] of Object.entries(this.board.cards || {})) {
                        const card = (cards || []).find((c) => c.atendimento_id === id);
                        if (card) {
                            conv = {
                                atendimento_id: id,
                                contato_nome: (card.titulo || '').split(' - ')[0] || 'Contato',
                                telefone: '',
                                etapa_nome: '',
                            };
                            break;
                        }
                    }
                }
                this.activeConv = conv || { atendimento_id: id };
                return Promise.all([
                    this.loadMessages(id),
                    this.loadDetail(id),
                    this.markRead(id),
                ]).then(() => {
                    this.$nextTick(() => this.scrollMessagesBottom());
                });
            },

            loadMessages: function (id) {
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'messages');
                return jsonFetch(url).then((data) => {
                    this.messages = data.messages || [];
                });
            },

            loadDetail: function (id) {
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'detail');
                return jsonFetch(url).then((data) => {
                    this.activeDetail = data;
                }).catch(() => {
                    this.activeDetail = null;
                });
            },

            markRead: function (id) {
                if (!this.atendenteId) return Promise.resolve();
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'mark-read');
                return jsonFetch(url, { method: 'POST' }).then(() => {
                    const conv = this.conversations.find((c) => c.atendimento_id === id);
                    if (conv) conv.nao_lidos = 0;
                }).catch(() => { /* não-fatal */ });
            },

            sendMessage: function () {
                if (!this.activeConv || this.sending) return;
                const texto = (this.composer || '').trim();
                if (!texto) return;
                this.sending = true;
                const id = this.activeConv.atendimento_id;
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'send');
                return jsonFetch(url, {
                    method: 'POST',
                    body: JSON.stringify({ texto: texto }),
                }).then((msg) => {
                    this.composer = '';
                    this.messages.push({
                        id: msg.id,
                        atendimento_id: msg.atendimento_id,
                        tipo: 'extendedTextMessage',
                        conteudo: '',
                        resposta_bot: msg.resposta_bot,
                        remetente: 'atendente_humano',
                        timestamp: msg.timestamp,
                        respondida: false,
                    });
                    this.$nextTick(() => this.scrollMessagesBottom());
                }).catch((exc) => {
                    console.error('Falha ao enviar', exc);
                    alert((exc && exc.message) || 'Falha ao enviar mensagem.');
                }).finally(() => {
                    this.sending = false;
                });
            },

            scrollMessagesBottom: function () {
                const refs = this.$refs || {};
                const el = refs.messagesContainer || refs.drawerMessages;
                if (el) el.scrollTop = el.scrollHeight;
            },

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
                    this._sseRetryDelay = 2000;  // reset backoff
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
                        // Atualiza preview na sidebar
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
                        // Se for a conversa ativa, append mensagem (refetch leve)
                        if (this.activeConv && this.activeConv.atendimento_id === data.atendimento_id) {
                            this.loadMessages(data.atendimento_id).then(() => {
                                this.$nextTick(() => this.scrollMessagesBottom());
                                this.markRead(data.atendimento_id);
                            });
                        }
                        break;
                    case 'board.moved':
                    case 'atendimento.updated':
                    case 'atendimento.created':
                        // Recarrega snapshot do board
                        if (this.mode === 'kanban') this.loadBoard();
                        this.loadConversations();
                        break;
                    case 'custom_field.updated':
                        // Recarrega detail para atualizar painel de campos
                        if (this.activeConv &&
                            this.activeConv.atendimento_id === data.atendimento_id) {
                            this.loadDetail(data.atendimento_id);
                        }
                        break;
                }
            },

            salvarCampo: function (campo, novoValor, onDone) {
                if (!this.activeConv) return;
                const id = this.activeConv.atendimento_id;
                // URL: /workspace/api/conversations/<id>/custom-fields/<slug>/
                const safeBase = (this.endpoints.customFieldsBase || '').replace(/\/+$/, '');
                const url = safeBase + '/' + id + '/custom-fields/' + campo.slug + '/';
                this.customFieldsSaving[campo.slug] = true;
                jsonFetch(url, {
                    method: 'PATCH',
                    body: JSON.stringify({ valor: novoValor }),
                }).then(() => {
                    // Atualiza valor no activeDetail sem reload
                    if (this.activeDetail && Array.isArray(this.activeDetail.campos)) {
                        const c = this.activeDetail.campos.find((x) => x.slug === campo.slug);
                        if (c) {
                            c.valor_raw = novoValor;
                            c.valor_display = Array.isArray(novoValor)
                                ? novoValor.join(', ')
                                : String(novoValor ?? '');
                            c.origem = 'MANUAL';
                            c.confianca = null;
                        }
                    }
                    if (typeof onDone === 'function') onDone();
                }).catch((exc) => {
                    console.error('Falha ao salvar campo', campo.slug, exc);
                    alert((exc && exc.message) || 'Falha ao salvar campo.');
                }).finally(() => {
                    this.customFieldsSaving[campo.slug] = false;
                });
            },

            prioridadeClass: prioridadeClass,
            intentLabel: intentLabel,
            tipoMidiaLabel: tipoMidiaLabel,
        };
    };
})();
