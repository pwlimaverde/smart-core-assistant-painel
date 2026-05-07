/**
 * whitelist_contact_autofill.js
 *
 * Ao selecionar um contato no formulário de White List, busca
 * automaticamente o nome e o telefone do contato via AJAX e
 * preenche os campos correspondentes.
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var contactField = document.getElementById("id_contact");
        var nameField = document.getElementById("id_name");
        var phoneField = document.getElementById("id_phone_number");

        if (!contactField || !nameField || !phoneField) {
            return;
        }

        contactField.addEventListener("change", function () {
            var contactId = this.value;

            if (!contactId) {
                return;
            }

            fetch("/api/evolution/contact-data/" + contactId + "/", {
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("HTTP " + response.status);
                    }
                    return response.json();
                })
                .then(function (data) {
                    // Preenche somente se o campo estiver vazio
                    if (data.name && !nameField.value.trim()) {
                        nameField.value = data.name;
                    }
                    if (
                        data.phone_number &&
                        !phoneField.value.trim()
                    ) {
                        phoneField.value = data.phone_number;
                    }
                })
                .catch(function (err) {
                    console.warn(
                        "[WhiteList] Erro ao buscar dados do contato:",
                        err
                    );
                });
        });
    });
})();
