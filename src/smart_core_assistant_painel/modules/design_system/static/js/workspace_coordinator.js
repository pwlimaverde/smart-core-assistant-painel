(function() {
    'use strict';

    document.addEventListener('alpine:init', () => {
        Alpine.data('workspaceCoordinator', () => ({
            selectedCardId: null,
            init() {
                // Escuta o clique em um card e notifica a abertura do chat correspondente
                window.addEventListener('card:clicked', (e) => {
                    if (e.detail && e.detail.atendimentoId) {
                        this.selectedCardId = e.detail.cardId || e.detail.atendimentoId;
                        this.$dispatch('chat:open', { atendimentoId: e.detail.atendimentoId });
                    }
                });

                // Escuta quando o chat é fechado
                window.addEventListener('chat:closed', () => {
                    this.selectedCardId = null;
                });
            }
        }));
    });
})();
