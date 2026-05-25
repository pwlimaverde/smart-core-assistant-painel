(function() {
    'use strict';

    window.workspaceChatMixin = function() {
        return {
            // ─────────────────────────────────────────────────────────
            // Estado do domínio Chat (movido do core na Fase 4 — separação
            // de responsabilidades; mesclado em workspaceStore via Object.assign)
            // ─────────────────────────────────────────────────────────
            messages: [],
            messagesError: '',
            activeConv: null,
            activeDetail: null,
            composer: '',
            sending: false,
            uploading: false,
            replyTo: null,
            mediaLightbox: {
                open: false, kind: '', src: '',
                mimetype: '', filename: '', isPdf: false,
            },
            showScrollBtn: false,
            _firstUnreadId: null,
            _scrollBtnThreshold: 120,
            contactPresence: null,
            _presenceTimer: null,
            _presenceSendTimer: null,
            isRecording: false,
            _mediaRecorder: null,
            _audioChunks: [],
            recordingSeconds: 0,
            _recordingTimer: null,

            // ─────────────────────────────────────────────────────────
            // Abertura de Chat e Roteamento
            // ─────────────────────────────────────────────────────────
            
            // Abre o chat em modo split se um ID for fornecido
            openChat: function (id) {
                if (id != null) {
                    return this._doOpenChat(id).then(() => this.setFocus('split'));
                }
                this.setFocus('split');
                return Promise.resolve();
            },

            // Executa a carga dos dados e mensagens de uma conversa específica
            _doOpenChat: function (id) {
                let conv = this.conversations.find((c) => c.atendimento_id === id);
                if (!conv) {
                    for (const [etapaId, cards] of Object.entries(this.board.cards || {})) {
                        const card = (cards || []).find((c) => c.atendimento_id === id);
                        if (card) {
                            conv = {
                                atendimento_id: id,
                                contato_nome: card.contato_nome || card.titulo || 'Contato',
                                contato_avatar_url: card.contato_avatar_url || '',
                                assunto: card.assunto || '',
                                telefone: '',
                                etapa_nome: '',
                            };
                            break;
                        }
                    }
                }
                this.activeConv = conv || { atendimento_id: id };
                
                // Captura a quantidade de mensagens não lidas antes de limpar/marcar como lidas
                const naoLidos = (conv && conv.nao_lidos) || 0;
                
                // Limpa o estado de carregamento anterior para evitar leak visual de outros contatos
                this.etiquetasAplicadas = [];
                this.notas = [];
                this.medias = [];
                this.timeline = [];
                this._firstUnreadId = null;
                this.showScrollBtn = false;
                
                return Promise.all([
                    this.loadMessages(id),
                    this.loadDetail(id),
                    this.markRead(id),
                    this.loadConversationEtiquetas(id),
                    this.loadNotas(id),
                    this.loadMedias(id),
                    this.loadTimeline(id),
                ]).then(() => {
                    // Marca a primeira mensagem não lida para exibição do divisor
                    if (naoLidos > 0 && this.messages.length >= naoLidos) {
                        const firstUnread = this.messages[this.messages.length - naoLidos];
                        this._firstUnreadId = firstUnread ? firstUnread.id : null;
                    }
                    this.$nextTick(() => this.scrollMessagesBottom());
                });
            },

            // Compatibilidade com templates antigos
            openChatDrawer: function (id) { 
                return this._doOpenChat(id); 
            },

            // ─────────────────────────────────────────────────────────
            // Carga de dados do Chat
            // ─────────────────────────────────────────────────────────

            loadMessages: function (id) {
                const url = this.endpoints.conversationsBase.endsWith('/')
                    ? this.endpoints.conversationsBase + id + '/messages/'
                    : this.endpoints.conversationsBase + '/' + id + '/messages/';
                this.messagesError = '';
                return fetch(url, { credentials: 'same-origin' })
                    .then((res) => {
                        if (!res.ok) {
                            // Sem este tratamento uma falha (ex: 403 fluxo sem
                            // permissão) caía silenciosamente em lista vazia,
                            // deixando o chat "vazio" sem explicação.
                            throw new Error('HTTP ' + res.status);
                        }
                        return res.json();
                    })
                    .then((data) => {
                        this.messages = data.messages || [];
                    })
                    .catch((err) => {
                        console.error('Falha ao carregar mensagens do atendimento', id, err);
                        this.messages = [];
                        this.messagesError = 'Não foi possível carregar as mensagens.';
                    });
            },

            loadDetail: function (id) {
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/detail/'
                    : this.endpoints.conversationsBase + '/' + id + '/detail/';
                return fetch(url, { credentials: 'same-origin' })
                    .then(res => res.json())
                    .then((data) => {
                        this.activeDetail = data;
                    }).catch(() => {
                        this.activeDetail = null;
                    });
            },

            markRead: function (id) {
                if (!this.atendenteId) return Promise.resolve();
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/mark-read/'
                    : this.endpoints.conversationsBase + '/' + id + '/mark-read/';
                
                const csrfToken = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
                const headers = { 'Accept': 'application/json' };
                if (csrfToken) {
                    headers['X-CSRFToken'] = decodeURIComponent(csrfToken[1]);
                }

                return fetch(url, { 
                    method: 'POST', 
                    credentials: 'same-origin',
                    headers: headers
                }).then(() => {
                    const conv = this.conversations.find((c) => c.atendimento_id === id);
                    if (conv) conv.nao_lidos = 0;
                    
                    // Zera não-lidas no card correspondente no Kanban
                    for (const cards of Object.values(this.board.cards || {})) {
                        const card = (cards || []).find((c) => c.atendimento_id === id);
                        if (card) card.nao_lidos = 0;
                    }
                    this._scheduleUnreadRefresh();
                }).catch(() => { /* Não-fatal */ });
            },

            // Envia mensagem via REST API
            sendMessage: function () {
                if (!this.activeConv || this.sending) return;
                const texto = (this.composer || '').trim();
                if (!texto) return;
                this.sending = true;
                
                const id = this.activeConv.atendimento_id;
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/send/'
                    : this.endpoints.conversationsBase + '/' + id + '/send/';

                const body = { texto: texto };
                if (this.replyTo && this.replyTo.id) {
                    body.quoted_message_id = this.replyTo.id;
                }
                const pendingReply = this.replyTo;

                const csrfToken = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
                const headers = { 
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                };
                if (csrfToken) {
                    headers['X-CSRFToken'] = decodeURIComponent(csrfToken[1]);
                }

                return fetch(url, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: headers,
                    body: JSON.stringify(body),
                }).then((res) => {
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    return res.json();
                }).then((msg) => {
                    this.composer = '';
                    this.replyTo = null;
                    this.messages.push({
                        id: msg.id,
                        atendimento_id: msg.atendimento_id,
                        tipo: 'extendedTextMessage',
                        conteudo: '',
                        resposta_bot: msg.resposta_bot,
                        remetente: 'atendente_humano',
                        timestamp: msg.timestamp,
                        respondida: false,
                        status_envio: 'pending',
                        quoted: pendingReply ? {
                            id: pendingReply.id,
                            remetente: pendingReply.remetente,
                            conteudo_preview: (pendingReply.conteudo || pendingReply.resposta_bot || '').slice(0, 200),
                        } : null,
                    });
                    this.$nextTick(() => this.scrollMessagesBottom());
                }).catch((exc) => {
                    console.error('Falha ao enviar mensagem', exc);
                    alert((exc && exc.message) || 'Falha ao enviar mensagem.');
                }).finally(() => {
                    this.sending = false;
                });
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

                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + atendimentoId + '/upload/'
                    : this.endpoints.conversationsBase + '/' + atendimentoId + '/upload/';

                const formData = new FormData();
                formData.append('file', file);

                const csrfToken = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
                const headers = { 'Accept': 'application/json' };
                if (csrfToken) {
                    headers['X-CSRFToken'] = decodeURIComponent(csrfToken[1]);
                }

                fetch(url, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: headers,
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

            // ─────────────────────────────────────────────────────────
            // Lightbox de Mídia
            // ─────────────────────────────────────────────────────────

            openLightbox: function (media) {
                if (!media || !media.src) return;
                // Documentos que não sejam PDF são baixados diretamente
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

            // Faz o download do arquivo para a pasta de Downloads do computador.
            // Funciona para URL servida pelo nginx (mesma origem) e data URI base64.
            downloadMedia: function (media) {
                if (!media || !media.src) return;
                const a = document.createElement('a');
                a.href = media.src;
                a.download = media.filename || 'arquivo';
                a.rel = 'noopener';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            },

            // ─────────────────────────────────────────────────────────
            // UX e UI Helpers do Chat
            // ─────────────────────────────────────────────────────────

            scrollMessagesBottom: function () {
                const refs = this.$refs || {};
                const el = refs.messagesContainer;
                if (el) el.scrollTop = el.scrollHeight;
                this.showScrollBtn = false;
            },

            setReplyTo: function (msg) {
                this.replyTo = msg ? {
                    id: msg.id,
                    remetente: msg.remetente,
                    conteudo: msg.conteudo || '',
                    resposta_bot: msg.resposta_bot || '',
                } : null;
                this.$nextTick(() => {
                    const el = this.$el && this.$el.querySelector
                        ? this.$el.querySelector('.ws-composer__input')
                        : null;
                    if (el) el.focus();
                });
            },

            clearReplyTo: function () { 
                this.replyTo = null; 
            },

            onChatScroll: function () {
                const el = (this.$refs || {}).messagesContainer;
                if (!el) return;
                const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
                this.showScrollBtn = distFromBottom > this._scrollBtnThreshold;
            },

            // ─────────────────────────────────────────────────────────
            // Presence (Digitação / Gravação de Áudio)
            // ─────────────────────────────────────────────────────────

            onComposerInput: function () {
                if (!this.activeConv) return;
                if (this._presenceSendTimer) clearTimeout(this._presenceSendTimer);
                this._presenceSendTimer = setTimeout(() => {
                    this._sendPresence('composing');
                    if (this._presenceSendTimer) clearTimeout(this._presenceSendTimer);
                    this._presenceSendTimer = setTimeout(() => {
                        this._sendPresence('paused');
                    }, 8000);
                }, 300);
            },

            _sendPresence: function (state, isAudio) {
                if (!this.activeConv) return;
                const id = this.activeConv.atendimento_id;
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/presence/'
                    : this.endpoints.conversationsBase + '/' + id + '/presence/';

                const csrfToken = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
                const headers = { 
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                };
                if (csrfToken) {
                    headers['X-CSRFToken'] = decodeURIComponent(csrfToken[1]);
                }

                fetch(url, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: headers,
                    body: JSON.stringify({ state: state, is_audio: !!isAudio }),
                }).catch(() => { /* best-effort — ignora erros */ });
            },

            handlePresenceUpdate: function (data) {
                if (!this.activeConv) return;
                if (data.atendimento_id !== this.activeConv.atendimento_id) return;
                const state = data.state || 'available';
                this.contactPresence = (state === 'composing' || state === 'recording')
                    ? state : null;
                if (this._presenceTimer) clearTimeout(this._presenceTimer);
                if (this.contactPresence) {
                    this._presenceTimer = setTimeout(() => {
                        this.contactPresence = null;
                    }, 8000);
                }
            },

            // ─────────────────────────────────────────────────────────
            // Gravação de Áudio de Voz
            // ─────────────────────────────────────────────────────────

            startRecording: async function () {
                if (this.isRecording || !this.activeConv) return;
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const mime = MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
                        ? 'audio/ogg;codecs=opus'
                        : 'audio/webm;codecs=opus';
                    this._mediaRecorder = new MediaRecorder(stream, { mimeType: mime });
                    this._audioChunks = [];
                    this._mediaRecorder.ondataavailable = (ev) => {
                        if (ev.data && ev.data.size > 0) this._audioChunks.push(ev.data);
                    };
                    this._mediaRecorder.onstop = () => {
                        stream.getTracks().forEach((t) => t.stop());
                        this._uploadAudioBlob(mime);
                    };
                    this._mediaRecorder.start(250);
                    this.isRecording = true;
                    this.recordingSeconds = 0;
                    this._recordingTimer = setInterval(() => { this.recordingSeconds++; }, 1000);
                    this._sendPresence('recording', true);
                } catch (err) {
                    alert('Não foi possível acessar o microfone: ' + (err.message || err));
                }
            },

            stopRecording: function () {
                if (!this.isRecording || !this._mediaRecorder) return;
                this._mediaRecorder.stop();
                this.isRecording = false;
                clearInterval(this._recordingTimer);
                this.recordingSeconds = 0;
                this._sendPresence('paused');
            },

            cancelRecording: function () {
                if (!this._mediaRecorder) return;
                this._mediaRecorder.onstop = null;
                try { this._mediaRecorder.stop(); } catch (_) {}
                this.isRecording = false;
                clearInterval(this._recordingTimer);
                this.recordingSeconds = 0;
                this._audioChunks = [];
                this._sendPresence('paused');
            },

            _uploadAudioBlob: function (mime) {
                if (!this._audioChunks.length || !this.activeConv) return;
                const ext = mime.includes('ogg') ? 'ogg' : 'webm';
                const blob = new Blob(this._audioChunks, { type: mime });
                this._audioChunks = [];
                const id = this.activeConv.atendimento_id;
                
                const url = this.endpoints.conversationsBase.endsWith('/') 
                    ? this.endpoints.conversationsBase + id + '/upload/'
                    : this.endpoints.conversationsBase + '/' + id + '/upload/';

                const fd = new FormData();
                fd.append('file', blob, `audio_${Date.now()}.${ext}`);
                this.uploading = true;

                const csrfToken = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);
                const headers = { 'Accept': 'application/json' };
                if (csrfToken) {
                    headers['X-CSRFToken'] = decodeURIComponent(csrfToken[1]);
                }

                fetch(url, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: headers,
                    body: fd,
                }).then(function (r) {
                    return r.json();
                }).then(() => {
                    return this.loadMessages(id);
                }).then(() => {
                    this.$nextTick(() => this.scrollMessagesBottom());
                }).catch(function (err) {
                    console.error('Falha ao enviar áudio', err);
                    alert('Falha ao enviar áudio gravado.');
                }).finally(() => {
                    this.uploading = false;
                });
            },

            // ─────────────────────────────────────────────────────────
            // Auxiliares de Visualização das Mensagens
            // ─────────────────────────────────────────────────────────

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

            formatDuration: function (seconds) {
                if (!seconds || seconds <= 0) return '';
                const s = Math.floor(seconds);
                const mm = Math.floor(s / 60);
                const ss = s % 60;
                return mm + ':' + (ss < 10 ? '0' : '') + ss;
            },

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

            // ─────────────────────────────────────────────────────────
            // Mensagens enriquecidas (separadores de data, agrupamento,
            // divisor de não-lidas) — movido do core na Fase 4
            // ─────────────────────────────────────────────────────────
            enrichedMessages: function() {
                const msgs = this.messages || [];
                const firstUnreadId = this._firstUnreadId;
                const now = new Date();
                const todayStr  = now.toDateString();
                const yesterday = new Date(now); yesterday.setDate(now.getDate() - 1);
                const yestStr   = yesterday.toDateString();

                const result = [];
                let prevDateStr = null;
                let prevRemetente = null;
                let prevTs = null;

                for (let i = 0; i < msgs.length; i++) {
                    const m = msgs[i];
                    const ts = m.timestamp ? new Date(m.timestamp) : null;
                    const dateStr = ts ? ts.toDateString() : null;

                    const showDateSep = !!dateStr && dateStr !== prevDateStr;
                    let dateLabel = '';
                    if (showDateSep) {
                        if (dateStr === todayStr)      dateLabel = 'Hoje';
                        else if (dateStr === yestStr)  dateLabel = 'Ontem';
                        else if (ts) {
                            const d = ts.getDate().toString().padStart(2, '0');
                            const mo = (ts.getMonth() + 1).toString().padStart(2, '0');
                            const yr = ts.getFullYear();
                            dateLabel = d + '/' + mo + '/' + yr;
                        }
                    }

                    const MIN5 = 5 * 60 * 1000;
                    const stacked = !showDateSep
                        && prevRemetente === m.remetente
                        && !!ts && !!prevTs
                        && (ts - prevTs) < MIN5;

                    result.push(Object.assign({}, m, {
                        _showDateSep: showDateSep,
                        _dateLabel: dateLabel,
                        _stacked: stacked,
                        _isFirstUnread: firstUnreadId != null && m.id === firstUnreadId,
                    }));

                    prevDateStr = dateStr;
                    prevRemetente = m.remetente;
                    prevTs = ts;
                }
                return result;
            }
        };
    };
})();
