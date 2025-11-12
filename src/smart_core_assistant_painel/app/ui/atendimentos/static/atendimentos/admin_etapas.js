// Atualiza selects em cascata: Departamento -> Fluxo -> Etapa
// Comentário: usa endpoints do admin para buscar fluxos e etapas.

(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function clearOptions(sel) {
    while (sel.options.length > 0) sel.remove(0);
    addOption(sel, "", "---------");
  }

  function addOption(sel, value, text) {
    var opt = document.createElement("option");
    opt.value = String(value);
    opt.text = String(text);
    sel.add(opt);
  }

  function buildRoot() {
    var href = window.location.pathname;
    var parts = href.split("/");
    var idx = parts.lastIndexOf("atendimento");
    return parts.slice(0, idx + 1).join("/") + "/";
  }

  function updateFluxos(deptId) {
    var fluxoSel = byId("id_fluxo_atendimento") ||
      document.querySelector("select[name='fluxo_atendimento']");
    var etapaSel = byId("id_etapa_atual") ||
      document.querySelector("select[name='etapa_atual']");
    if (!fluxoSel || !etapaSel) return;

    var initialFluxo = fluxoSel.getAttribute("data-initial") || "";
    clearOptions(fluxoSel);
    clearOptions(etapaSel);
    if (!deptId) return;

    var url = buildRoot() + "fetch-fluxos/";
    var qs = "?departamento_id=" + encodeURIComponent(String(deptId));

    fetch(url + qs, { credentials: "same-origin" })
      .then(function (resp) { return resp.json(); })
      .then(function (json) {
        var results = (json && json.results) || [];
        results.forEach(function (item) {
          addOption(fluxoSel, item.id, item.label);
        });
        if (initialFluxo) {
          fluxoSel.value = String(initialFluxo);
          updateEtapasByFluxo(initialFluxo);
        }
      })
      .catch(function () { /* Silencia erros */ });
  }

  function updateEtapasByFluxo(fluxoId) {
    var etapaSel = byId("id_etapa_atual") ||
      document.querySelector("select[name='etapa_atual']");
    if (!etapaSel) return;
    var initialEtapa = etapaSel.getAttribute("data-initial") || "";
    clearOptions(etapaSel);
    if (!fluxoId) return;

    var url = buildRoot() + "fetch-etapas-by-fluxo/";
    var qs = "?fluxo_id=" + encodeURIComponent(String(fluxoId));

    fetch(url + qs, { credentials: "same-origin" })
      .then(function (resp) { return resp.json(); })
      .then(function (json) {
        var results = (json && json.results) || [];
        results.forEach(function (item) {
          addOption(etapaSel, item.id, item.label);
        });
        if (initialEtapa) {
          etapaSel.value = String(initialEtapa);
        }
      })
      .catch(function () { /* Silencia erros */ });
  }

  function init() {
    var deptSel = byId("id_departamento");
    var fluxoSel = byId("id_fluxo_atendimento");
    if (!deptSel || !fluxoSel) return;

    // Atualiza ao mudar departamento
    deptSel.addEventListener("change", function () {
      updateFluxos(deptSel.value);
    });

    // Atualiza ao mudar fluxo
    fluxoSel.addEventListener("change", function () {
      updateEtapasByFluxo(fluxoSel.value);
    });

    // Estado inicial (edição): carrega fluxos e possivelmente etapas
    if (deptSel.value) {
      updateFluxos(deptSel.value);
    }
    if (fluxoSel.value) {
      updateEtapasByFluxo(fluxoSel.value);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();