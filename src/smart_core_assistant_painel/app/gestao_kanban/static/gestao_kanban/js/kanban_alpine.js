(function() {
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

    window.workspaceKanbanMixin = function() {
        return {
            // ─────────────────────────────────────────────────────────
            // Carga do Board e SortableJS
            // ─────────────────────────────────────────────────────────
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
            // Interação com Cards
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
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/etiquetas/'
                    : this.endpoints.conversationsBase + '/' + id + '/etiquetas/';
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
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/etiquetas/' + etiquetaId + '/toggle/'
                    : this.endpoints.conversationsBase + '/' + id + '/etiquetas/' + etiquetaId + '/toggle/';
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
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/notas/'
                    : this.endpoints.conversationsBase + '/' + id + '/notas/';
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
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/notas/'
                    : this.endpoints.conversationsBase + '/' + id + '/notas/';
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
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/medias/'
                    : this.endpoints.conversationsBase + '/' + id + '/medias/';
                return jsonFetch(url).then((data) => {
                    this.medias = data.medias || [];
                }).catch(() => { this.medias = []; });
            },

            loadTimeline: function (id) {
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/timeline/'
                    : this.endpoints.conversationsBase + '/' + id + '/timeline/';
                return jsonFetch(url).then((data) => {
                    this.timeline = data.timeline || [];
                }).catch(() => { this.timeline = []; });
            },

            // ─────────────────────────────────────────────────────────
            // Transferência entre Fluxos
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
            // Custom Fields (Campos Personalizados)
            // ─────────────────────────────────────────────────────────
            salvarCampo: function (campo, novoValor, onDone) {
                if (!this.activeConv) return;
                const id = this.activeConv.atendimento_id;
                const safeBase = (this.endpoints.kanbanConversationsBase || '').replace(/\/+$/, '');
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
            }
        };
    };
})();
