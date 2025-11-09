// Atualiza o select de etapas quando o departamento é alterado no admin.
// Comentário: usa um endpoint do próprio admin para buscar etapas.

(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function clearOptions(sel) {
    while (sel.options.length > 0) sel.remove(0);
  }

  function addOption(sel, value, text) {
    var opt = document.createElement("option");
    opt.value = String(value);
    opt.text = String(text);
    sel.add(opt);
  }

  function updateEtapas(deptId) {
    var etapasSel = byId("id_etapa_atual") ||
      document.querySelector("select[name='etapa_atual']");
    if (!etapasSel) return;
    // Captura valor inicial salvo (caso o select ainda não tenha opções)
    var initialVal = etapasSel.getAttribute("data-initial") || "";
    clearOptions(etapasSel);
    if (!deptId) return;

    // Descobre base URL do admin a partir do path atual (add ou change)
    var href = window.location.pathname;
    // Calcula raiz do admin deste ModelAdmin: .../atendimentos/atendimento/
    var parts = href.split("/");
    var idx = parts.lastIndexOf("atendimento");
    var root = parts.slice(0, idx + 1).join("/") + "/";
    var url = root + "fetch-etapas/";
    var qs = "?departamento_id=" + encodeURIComponent(String(deptId));

    fetch(url + qs, { credentials: "same-origin" })
      .then(function (resp) {
        return resp.json();
      })
      .then(function (json) {
        var results = (json && json.results) || [];
        // Mantém uma opção vazia no topo para facilitar limpeza
        addOption(etapasSel, "", "---------");
        results.forEach(function (item) {
          addOption(etapasSel, item.id, item.label);
        });

        // Seleciona automaticamente a etapa previamente salva, se existir
        if (initialVal) {
          etapasSel.value = String(initialVal);
        }

        // Fallback: se não houve resultados, recarrega com querystring
        // para permitir que o servidor filtre o queryset via get_form.
        if (results.length === 0) {
          try {
            var urlObj = new URL(window.location.href);
            var hasParam = urlObj.searchParams.get("departamento");
            if (!hasParam) {
              urlObj.searchParams.set(
                "departamento",
                String(deptId)
              );
              window.location.assign(urlObj.toString());
            }
          } catch (e) {
            // Silencia falhas de URL; sem impacto
          }
        }
      })
      .catch(function () {
        // Silencia erros; admin continuará funcional
      });
  }

  function init() {
    var deptSel = byId("id_departamento");
    if (!deptSel) return;

    // Atualiza ao mudar departamento
    deptSel.addEventListener("change", function () {
      updateEtapas(deptSel.value);
    });

    // Se já houver departamento selecionado, carrega etapas
    if (deptSel.value) {
      updateEtapas(deptSel.value);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();