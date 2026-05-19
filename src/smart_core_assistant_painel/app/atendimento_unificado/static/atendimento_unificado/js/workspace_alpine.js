/*
 * Store Alpine.js do Workspace de Atendimento Unificado.
 *
 * - Gerencia estado de Conversas e Kanban
 * - Consome endpoints JSON declarados em workspace.html
 * - Conecta-se ao stream SSE para atualizações ao vivo
 *
 * MODOS DE FOCO:
 *  - `focusMode`: 'board' | 'split' | 'chat'  (persistido em localStorage)
 *  - 'board': Kanban toma a tela; chat minimizado em mini-bar flutuante
 *  - 'split': layout dividido (padrão) — kanban + chat + info drawer opcional
 *  - 'chat' : kanban colapsa em trilha de avatares; chat fica grande
 *
 * Atalhos de teclado (em base_workspace.html):
 *  - Alt+1 / Alt+2 / Alt+3 → board / split / chat
 *  - Esc                   → reduz o foco gradualmente
 *  - i                     → toggle do detail drawer
 *
 * Convenções:
 *  - `conversations`: lista (usada apenas como cache de preview para SSE)
 *  - `board`: { etapas: [...], cards: { '<etapa_id>': [...] } }
 *  - `activeConv`: conversa atualmente aberta no chat lateral
 *  - `activeDetail`: payload de /detail/ (campos personalizados, etc.)
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

    function buildConvUrl(base, atendimentoId, suffix) {
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
            fluxoId: init.fluxoId || null,
            fluxos: [],
            conversations: [],
            messages: [],
            board: { etapas: [], cards: {} },
            activeConv: null,
            activeDetail: null,
            composer: '',
            search: '',
            filterTag: '',
            sending: false,
            uploading: false,
            sseConnected: false,
            sse: null,
            _sseRetryDelay: 2000,
            _sseReconnectTimer: null,
            _sortableInstances: [],
            isDragging: false,
            endpoints: init.endpoints,
            customFieldsSaving: {},
            tenantSlug: init.tenantSlug,
            atendenteId: init.atendenteId,
            atendenteNome: init.atendenteNome,
            sseEnabled: init.sseEnabled === true,
            detailDrawerOpen: false,

            // ─────────────────────────────────────────────────────────
            // Lightbox para mídia (imagem/vídeo/PDF) em tela cheia
            // ─────────────────────────────────────────────────────────
            mediaLightbox: {
                open: false,
                kind: '',       // 'image' | 'video' | 'document'
                src: '',
                mimetype: '',
                filename: '',
                isPdf: false,
            },

            // ─────────────────────────────────────────────────────────
            // NOVO: Modos de foco + tema/densidade
            // ─────────────────────────────────────────────────────────
            focusMode: readLS(LS_FOCUS, 'split'),     // 'board' | 'split' | 'chat'
            theme:     readLS(LS_THEME, 'light'),     // 'light' | 'dark'
            density:   readLS(LS_DENSITY, 'normal'),  // 'compact' | 'normal' | 'confortable'
            showKbdHint: false,
            _hintTimer: null,

            // ─────────────────────────────────────────────────────────
            // Etiquetas, Notas, Mídias, Timeline, Notificações, Filtros
            // ─────────────────────────────────────────────────────────
            etiquetas: [],                  // catálogo de etiquetas disponíveis
            etiquetasAplicadas: [],         // etiquetas do atendimento ativo
            notas: [],                      // notas do atendimento ativo
            medias: [],                     // mídias/arquivos do atendimento ativo
            timeline: [],                   // eventos do atendimento ativo
            unreadCount: 0,                 // total geral para o sino
            etiquetaPopoverOpen: false,
            transferirPopoverOpen: false,
            filterPopoverOpen: false,
            filters: {
                q: '',
                prioridade: '',
                atendente_id: '',
                etiqueta_id: '',
                apenas_nao_lidos: false,
            },
            notaComposer: '',
            notaSaving: false,
            _unreadDebounce: null,

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
                    // Mostra hint de atalhos por 5s na primeira carga.
                    this.showKbdHint = true;
                    this._hintTimer = setTimeout(() => { this.showKbdHint = false; }, 5000);
                } catch (exc) {
                    console.error('Falha ao inicializar Workspace', exc);
                }
            },

            // ─────────────────────────────────────────────────────────
            // NOVO: Controle de foco
            // ─────────────────────────────────────────────────────────
            setFocus: function (mode) {
                if (['board', 'split', 'chat'].indexOf(mode) === -1) return;
                this.focusMode = mode;
                writeLS(LS_FOCUS, mode);
            },

            minimizeChat: function () { this.setFocus('board'); },

            // openChat(id?) — se vier um id, abre a conversa e expande pra split.
            openChat: function (id) {
                if (id != null) {
                    // Reusa o openChat original (renomeado para _doOpenChat abaixo).
                    return this._doOpenChat(id).then(() => this.setFocus('split'));
                }
                this.setFocus('split');
                return Promise.resolve();
            },

            // Handler do Esc — reduz foco gradualmente. Ignorado se digitando.
            onEscape: function ($event) {
                if (this.isTypingTarget($event)) return;
                if (this.mediaLightbox.open) { this.closeLightbox(); return; }
                if (this.detailDrawerOpen) { this.detailDrawerOpen = false; return; }
                if (this.focusMode === 'chat')  { this.setFocus('split'); return; }
                if (this.focusMode === 'split') { this.setFocus('board'); return; }
                // já está em 'board' — não faz nada
            },

            onToggleInfo: function ($event) {
                if (this.isTypingTarget($event)) return;
                this.detailDrawerOpen = !this.detailDrawerOpen;
            },

            // ─────────────────────────────────────────────────────────
            // Lightbox de mídia
            // ─────────────────────────────────────────────────────────
            openLightbox: function (media) {
                if (!media || !media.src) return;
                // Documentos não-PDF baixam direto, sem modal
                if (media.kind === 'document' && !media.is_pdf) {
                    const a = document.createElement('a');
                    a.href = media.src;
                    a.download = media.filename || 'documento';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    return;
                }
                this.mediaLightbox = {
                    open: true,
                    kind: media.kind || '',
                    src: media.src,
                    mimetype: media.mimetype || '',
                    filename: media.filename || '',
                    isPdf: !!media.is_pdf,
                };
            },

            closeLightbox: function () {
                this.mediaLightbox = {
                    open: false, kind: '', src: '',
                    mimetype: '', filename: '', isPdf: false,
                };
            },

            // Label legível para tipo de mídia (usado no fallback do balão)
            tipoMidiaLabel: function (tipo) {
                const map = {
                    imageMessage: 'Imagem',
                    stickerMessage: 'Figurinha',
                    audioMessage: 'Áudio',
                    videoMessage: 'Vídeo',
                    documentMessage: 'Documento',
                };
                return map[tipo] || 'Mídia';
            },

            // Ícone de status de entrega da mensagem (read receipts).
            // Mapeia status_envio → símbolo Unicode exibido no rodapé do balão.
            // pending  → ● (cinza claro — aguardando servidor)
            // sent     → ✓  (cinza — entregue ao servidor)
            // delivered→ ✓✓ (cinza — entregue ao dispositivo)
            // read     → ✓✓ (azul — lida)
            // failed   → ✗  (vermelho — falhou)
            // fallback → usa m.respondida para retrocompat
            statusEnvioIcon: function (status, respondida) {
                switch (status) {
                    case 'pending':   return '●';
                    case 'sent':      return '✓';
                    case 'delivered': return '✓✓';
                    case 'read':      return '✓✓';
                    case 'failed':    return '✗';
                    default:          return respondida ? '✓✓' : '✓';
                }
            },

            // Formata segundos em mm:ss (para duração de áudio/vídeo)
            formatDuration: function (seconds) {
                if (!seconds || seconds <= 0) return '';
                const s = Math.floor(seconds);
                const mm = Math.floor(s / 60);
                const ss = s % 60;
                return mm + ':' + (ss < 10 ? '0' : '') + ss;
            },

            // Texto a exibir no balão. Suprime placeholders sintéticos
            // ("[imagem]", "[audio]" etc.) quando a mensagem é de mídia —
            // a mídia já está representada visualmente.
            bubbleText: function (m) {
                if (!m) return '';
                const base = m.remetente === 'contato'
                    ? (m.conteudo || '')
                    : (m.resposta_bot || m.conteudo || '');
                const trimmed = (base || '').trim();
                if (m.media && /^\[(imagem|audio|áudio|video|vídeo|documento|figurinha|sticker)\]$/i.test(trimmed)) {
                    return '';
                }
                return base;
            },

            isTypingTarget: function ($event) {
                if (!$event || !$event.target) return false;
                const tag = ($event.target.tagName || '').toUpperCase();
                return tag === 'INPUT' || tag === 'TEXTAREA' || $event.target.isContentEditable;
            },

            // ─────────────────────────────────────────────────────────
            // Tema + densidade (persistidos)
            // ─────────────────────────────────────────────────────────
            setTheme: function (t) {
                this.theme = t;
                writeLS(LS_THEME, t);
            },
            setDensity: function (d) {
                this.density = d;
                writeLS(LS_DENSITY, d);
            },

            // ─────────────────────────────────────────────────────────
            // Fluxos / Board / Conversas (igual ao original)
            // ─────────────────────────────────────────────────────────
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

            // Constrói query string com filtros + busca livre.
            // `extraParams` permite forçar overrides (ex.: ?fluxo=X).
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

            loadBoard: function () {
                if (this.fluxoId == null) {
                    this.board = { etapas: [], cards: {} };
                    return Promise.resolve();
                }
                const params = this._buildFiltersParams({ fluxo: this.fluxoId });
                const url = this.endpoints.board + '?' + params.toString();
                return jsonFetch(url).then((data) => {
                    this.board = data || { etapas: [], cards: {} };
                    this.$nextTick(() => this.initSortable());
                });
            },

            initSortable: function () {
                this._sortableInstances.forEach(function (s) {
                    try { s.destroy(); } catch (_) {}
                });
                this._sortableInstances = [];
                if (typeof Sortable === 'undefined') {
                    console.warn('[workspace] SortableJS não carregado');
                    return;
                }
                const self = this;
                const cols = document.querySelectorAll('.kanban-col-body');
                cols.forEach(function (el) {
                    const instance = Sortable.create(el, {
                        group: 'kanban-cards',
                        draggable: '.kanban-card',
                        animation: 180,
                        ghostClass: 'kanban-ghost',
                        chosenClass: 'kanban-chosen',
                        dragClass: 'kanban-drag',
                        filter: '.kanban-no-drag, .kanban-no-drag *',
                        preventOnFilter: false,
                        onStart: function () { self.isDragging = true; },
                        onEnd: function (evt) {
                            setTimeout(function () { self.isDragging = false; }, 50);

                            const atendimentoId = parseInt(evt.item.getAttribute('data-atend-id'), 10);
                            const fromEtapaId = parseInt(evt.from.getAttribute('data-etapa-id'), 10);
                            const toEtapaId = parseInt(evt.to.getAttribute('data-etapa-id'), 10);

                            if (!atendimentoId || !toEtapaId) {
                                self.loadBoard();
                                return;
                            }
                            if (fromEtapaId === toEtapaId) return;

                            jsonFetch(self.endpoints.boardMove, {
                                method: 'POST',
                                body: JSON.stringify({
                                    atendimento_id: atendimentoId,
                                    etapa_destino_id: toEtapaId,
                                }),
                            }).then(function () {
                                self.loadBoard();
                            }).catch(function (exc) {
                                console.error('[workspace] Falha no boardMove', exc);
                                self.loadBoard();
                                alert((exc && exc.message) || 'Falha ao mover card.');
                            });
                        },
                    });
                    self._sortableInstances.push(instance);
                });
            },

            // ─────────────────────────────────────────────────────────
            // Clique em card do kanban
            // - Em modo 'board': abre conversa mas NÃO expande (mini-bar)
            // - Em outros modos: comportamento original (abre painel direito)
            // ─────────────────────────────────────────────────────────
            onCardClick: function (id, event) {
                if (this.isDragging) return;
                return this._doOpenChat(id);
            },

            onCardDetail: function (id, event) {
                if (event) { event.stopPropagation(); event.preventDefault(); }
                if (this.isDragging) return;
                const self = this;
                return this._doOpenChat(id).then(function () {
                    self.detailDrawerOpen = true;
                    if (self.focusMode === 'board') self.setFocus('split');
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

            // _doOpenChat = lógica de "abrir conversa" sem mexer em focusMode.
            // Use openChat(id) externamente — ele orquestra foco + abertura.
            _doOpenChat: function (id) {
                let conv = this.conversations.find((c) => c.atendimento_id === id);
                if (!conv) {
                    for (const [etapaId, cards] of Object.entries(this.board.cards || {})) {
                        const card = (cards || []).find((c) => c.atendimento_id === id);
                        if (card) {
                            conv = {
                                atendimento_id: id,
                                contato_nome: card.contato_nome || card.titulo || 'Contato',
                                assunto: card.assunto || '',
                                telefone: '',
                                etapa_nome: '',
                            };
                            break;
                        }
                    }
                }
                this.activeConv = conv || { atendimento_id: id };
                // Limpa estado anterior das seções do info drawer para evitar
                // mostrar dados de outra conversa enquanto carrega.
                this.etiquetasAplicadas = [];
                this.notas = [];
                this.medias = [];
                this.timeline = [];
                return Promise.all([
                    this.loadMessages(id),
                    this.loadDetail(id),
                    this.markRead(id),
                    this.loadConversationEtiquetas(id),
                    this.loadNotas(id),
                    this.loadMedias(id),
                    this.loadTimeline(id),
                ]).then(() => {
                    this.$nextTick(() => this.scrollMessagesBottom());
                });
            },

            // Compat: kanban_card.html ainda chama openChatDrawer em alguns lugares.
            openChatDrawer: function (id) { return this._doOpenChat(id); },

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
                    // Zera não-lidas no card do board correspondente
                    for (const cards of Object.values(this.board.cards || {})) {
                        const card = (cards || []).find((c) => c.atendimento_id === id);
                        if (card) card.nao_lidos = 0;
                    }
                    this._scheduleUnreadRefresh();
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
                const el = refs.messagesContainer;
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
                            this.loadMessages(data.atendimento_id).then(() => {
                                this.$nextTick(() => this.scrollMessagesBottom());
                                this.markRead(data.atendimento_id);
                            });
                        } else if (data.remetente === 'contato') {
                            this._scheduleUnreadRefresh();
                        }
                        break;
                    case 'board.moved':
                    case 'atendimento.updated':
                    case 'atendimento.created':
                        if (!this.isDragging) this.loadBoard();
                        this.loadConversations();
                        break;
                    case 'custom_field.updated':
                        if (this.activeConv &&
                            this.activeConv.atendimento_id === data.atendimento_id) {
                            this.loadDetail(data.atendimento_id);
                        }
                        break;
                }
            },

            uploadMedia: function (event, atendimentoId) {
                const file = event.target.files && event.target.files[0];
                if (!file || !atendimentoId) return;
                if (file.size > 10 * 1024 * 1024) {
                    alert('Arquivo muito grande. Limite: 10 MB.');
                    event.target.value = '';
                    return;
                }
                this.uploading = true;
                const url = buildConvUrl(this.endpoints.conversationsBase, atendimentoId, 'upload');
                const formData = new FormData();
                formData.append('file', file);
                fetch(url, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: formData,
                }).then(function (res) {
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    return res.json();
                }).then(() => {
                    this.loadMessages(atendimentoId).then(() => {
                        this.$nextTick(() => this.scrollMessagesBottom());
                    });
                }).catch(function (exc) {
                    console.error('Falha ao enviar mídia', exc);
                    alert((exc && exc.message) || 'Falha ao enviar mídia.');
                }).finally(() => {
                    this.uploading = false;
                    event.target.value = '';
                });
            },

            salvarCampo: function (campo, novoValor, onDone) {
                if (!this.activeConv) return;
                const id = this.activeConv.atendimento_id;
                const safeBase = (this.endpoints.customFieldsBase || '').replace(/\/+$/, '');
                const url = safeBase + '/' + id + '/custom-fields/' + campo.slug + '/';
                this.customFieldsSaving[campo.slug] = true;
                jsonFetch(url, {
                    method: 'PATCH',
                    body: JSON.stringify({ valor: novoValor }),
                }).then(() => {
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

            // ─────────────────────────────────────────────────────────
            // Etiquetas
            // ─────────────────────────────────────────────────────────
            loadEtiquetas: function () {
                const url = (this.endpoints.etiquetas || '/workspace/api/etiquetas/');
                return jsonFetch(url).then((data) => {
                    this.etiquetas = data.etiquetas || [];
                }).catch(() => { this.etiquetas = []; });
            },

            loadConversationEtiquetas: function (id) {
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'etiquetas');
                return jsonFetch(url).then((data) => {
                    this.etiquetasAplicadas = data.etiquetas || [];
                }).catch(() => { this.etiquetasAplicadas = []; });
            },

            isEtiquetaAplicada: function (etiquetaId) {
                return (this.etiquetasAplicadas || []).some((e) => e.id === etiquetaId);
            },

            toggleEtiqueta: function (etiquetaId) {
                if (!this.activeConv) return;
                const id = this.activeConv.atendimento_id;
                const url = buildConvUrl(
                    this.endpoints.conversationsBase, id, 'etiquetas/' + etiquetaId + '/toggle'
                );
                return jsonFetch(url, { method: 'POST' }).then((result) => {
                    if (result.ativa) {
                        const et = this.etiquetas.find((e) => e.id === etiquetaId);
                        if (et && !this.isEtiquetaAplicada(etiquetaId)) {
                            this.etiquetasAplicadas.push({ ...et });
                        }
                    } else {
                        this.etiquetasAplicadas = this.etiquetasAplicadas.filter(
                            (e) => e.id !== etiquetaId
                        );
                    }
                }).catch((exc) => {
                    console.error('Falha ao alternar etiqueta', exc);
                    alert((exc && exc.message) || 'Falha ao alternar etiqueta.');
                });
            },

            // ─────────────────────────────────────────────────────────
            // Notas
            // ─────────────────────────────────────────────────────────
            loadNotas: function (id) {
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'notas');
                return jsonFetch(url).then((data) => {
                    this.notas = data.notas || [];
                }).catch(() => { this.notas = []; });
            },

            criarNota: function () {
                if (!this.activeConv) return;
                const texto = (this.notaComposer || '').trim();
                if (!texto || this.notaSaving) return;
                this.notaSaving = true;
                const id = this.activeConv.atendimento_id;
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'notas');
                return jsonFetch(url, {
                    method: 'POST',
                    body: JSON.stringify({ texto: texto }),
                }).then((nota) => {
                    this.notas.unshift(nota);
                    this.notaComposer = '';
                }).catch((exc) => {
                    console.error('Falha ao criar nota', exc);
                    alert((exc && exc.message) || 'Falha ao criar nota.');
                }).finally(() => {
                    this.notaSaving = false;
                });
            },

            deletarNota: function (notaId) {
                if (!this.activeConv) return;
                if (!confirm('Remover esta nota?')) return;
                const id = this.activeConv.atendimento_id;
                const safeBase = (this.endpoints.conversationsBase || '').replace(/\/+$/, '');
                const url = safeBase + '/' + id + '/notas/' + notaId + '/';
                return jsonFetch(url, { method: 'DELETE' }).then(() => {
                    this.notas = this.notas.filter((n) => n.id !== notaId);
                }).catch((exc) => {
                    console.error('Falha ao remover nota', exc);
                    alert((exc && exc.message) || 'Falha ao remover nota.');
                });
            },

            abrirComposerNota: function () {
                this.detailDrawerOpen = true;
                if (this.focusMode === 'board') this.setFocus('split');
                this.$nextTick(() => {
                    const ta = document.querySelector('.ws-info__nota-form textarea');
                    if (ta) ta.focus();
                });
            },

            // ─────────────────────────────────────────────────────────
            // Mídias e Timeline
            // ─────────────────────────────────────────────────────────
            loadMedias: function (id) {
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'medias');
                return jsonFetch(url).then((data) => {
                    this.medias = data.medias || [];
                }).catch(() => { this.medias = []; });
            },

            loadTimeline: function (id) {
                const url = buildConvUrl(this.endpoints.conversationsBase, id, 'timeline');
                return jsonFetch(url).then((data) => {
                    this.timeline = data.timeline || [];
                }).catch(() => { this.timeline = []; });
            },

            // ─────────────────────────────────────────────────────────
            // Notificações (sino)
            // ─────────────────────────────────────────────────────────
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

            // ─────────────────────────────────────────────────────────
            // Transferência entre fluxos
            // ─────────────────────────────────────────────────────────
            transferirFluxo: function (fluxoDestinoId) {
                if (!this.activeConv) return;
                const id = this.activeConv.atendimento_id;
                const url = (this.endpoints.boardTransferFluxo || '/workspace/api/board/transfer-fluxo/');
                this.transferirPopoverOpen = false;
                return jsonFetch(url, {
                    method: 'POST',
                    body: JSON.stringify({
                        atendimento_id: id,
                        fluxo_destino_id: fluxoDestinoId,
                    }),
                }).then(() => {
                    // Recarrega tudo — o atendimento pode ter saído da visão atual.
                    this.loadConversations();
                    this.loadBoard();
                    this.activeConv = null;
                    this.messages = [];
                    this.activeDetail = null;
                }).catch((exc) => {
                    console.error('Falha ao transferir fluxo', exc);
                    alert((exc && exc.message) || 'Falha ao transferir atendimento.');
                });
            },

            fluxosParaTransferir: function () {
                const atualId = this.activeConv && this.activeConv.fluxo_id;
                const atualDetailId = this.activeDetail && this.activeDetail.fluxo_id;
                const excluirId = atualId || atualDetailId || null;
                return (this.fluxos || []).filter((f) => f.id !== excluirId);
            },

            // ─────────────────────────────────────────────────────────
            // Filtros (popover)
            // ─────────────────────────────────────────────────────────
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

            // Helper: número de filtros ativos (badge no botão funil)
            activeFiltersCount: function () {
                let n = 0;
                if (this.filters.q) n++;
                if (this.filters.prioridade) n++;
                if (this.filters.atendente_id) n++;
                if (this.filters.etiqueta_id) n++;
                if (this.filters.apenas_nao_lidos) n++;
                return n;
            },

            prioridadeClass: prioridadeClass,
            intentLabel: intentLabel,
            tipoMidiaLabel: tipoMidiaLabel,
        };
    };
})();
