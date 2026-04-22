// js/history.js — versión cookie-based (usa apiFetch)
(function () {
  const API_BASE   = window.API || "";
  const OUTLET_SEL = "#app-view";
  const LIST_SEL   = "#history-list";
  const MSG_SEL    = "#historyMsg";
  const BTN_SEL    = "#btnClearHistory, #clearHistorial"; // soporta ambos ids

  const esc = (s = "") =>
    String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // 1) Cargar historial (sin Authorization; cookies viajan con apiFetch)
  async function loadHistory(root) {
    const msg  = root.querySelector(MSG_SEL);
    const list = root.querySelector(LIST_SEL);
    if (msg) msg.textContent = "Cargando…";
    if (list) list.innerHTML = "";

    try {
      const res = await apiFetch("/generate/history", { method: "GET" });
      const raw = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(raw.detail || "No se pudo cargar el historial.");

      // Soportar varios formatos de respuesta
      let items = Array.isArray(raw) ? raw : (raw.items || raw.historial || raw.history || []);

      // Normaliza cada item a las claves esperadas
      items = items.map(it => ({
        timestamp: it.timestamp || it.date || it.fecha || it.created_at || null,
        content_type: it.content_type || it.tipo || it.type || "",
        tone: it.tone || it.tono || "",
        prompt: it.prompt || it.entrada || it.input || "",
        content: it.content ?? it.contenido ?? it.text ?? it.result ?? it.output ?? it.body ?? ""
      }));

      render(items, root);
    } catch (e) {
      if (msg) msg.textContent = "❌ " + (e.message || "Error de red");
      console.warn("Historial (error):", e);
    }
  }

  // 2) Pintar tarjetas
  function render(items, root) {
    const list = root.querySelector(LIST_SEL);
    const msg  = root.querySelector(MSG_SEL);
    if (!list) return;

    list.innerHTML = "";
    if (!items || !items.length) {
      if (msg) msg.textContent = "📭 No hay contenidos aún.";
      return;
    }
    if (msg) msg.textContent = "";

    const humanType = (t = "") => {
      const map = { email: "Email", post: "Publicación", product_description: "Descripción de producto" };
      return map[t] || (t ? (t[0].toUpperCase() + t.slice(1)) : "Contenido");
    };

    for (let i = 0; i < items.length; i++) {
      const it   = items[i];
      const when = it.timestamp ? new Date(it.timestamp).toLocaleString() : "—";
      const type = humanType(it.content_type);
      const tone = it.tone ? ` · ${esc(it.tone)}` : "";

      const card = document.createElement("div");
      card.className = "history-entry";
      card.innerHTML = `
        <h4 class="history-title">📌 Entrada #${i + 1}</h4>
        <div class="history-meta">
          <span><strong>📅 Fecha:</strong> ${esc(when)}</span>
        </div>
        <div class="history-meta">
          <span><strong>📂 Tipo:</strong> ${esc(type)}${tone}</span>
        </div>
        ${it.prompt ? `
          <p class="history-prompt"><strong>📝 Prompt:</strong> ${esc(it.prompt)}</p>
        ` : ""}
        <div class="entry-content">${esc(it.content)}</div>
        <hr class="history-divider">
      `;
      list.appendChild(card);
    }
  }

  // 3) Borrar historial (DELETE) — acción sensible → usa CSRF
  async function clearHistory(root, btn) {
    const msg = root.querySelector(MSG_SEL);
    const old = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = "Borrando…"; }

    async function tryDelete(url) {
      const res  = await apiFetch(url, { method: "DELETE" }, { csrf: true });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
      return data;
    }

    try {
      // 1ª opción
      let data;
      try {
        data = await tryDelete(`/generate/clear`);
      } catch {
        // fallback si tu backend usa /generate/history/clear
        data = await tryDelete(`/generate/history/clear`);
      }
      if (msg) msg.textContent = data.message || "Historial borrado.";
      render([], root);
    } catch (e) {
      if (msg) msg.textContent = "❌ " + (e.message || "No se pudo borrar el historial");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = old || "Borrar historial"; }
    }
  }

  // 4) Auto-inicialización y binding de botón
  function initIfPresent(root) {
    const list = root.querySelector(LIST_SEL);
    if (!list || list.dataset.inited) return;
    list.dataset.inited = "1";

    // Botón borrar (acepta #btnClearHistory o #clearHistorial)
    const btn = root.querySelector(BTN_SEL);
    if (btn && !btn.dataset.bound) {
      btn.dataset.bound = "1";
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        clearHistory(root, btn);
      });
    }

    loadHistory(root);
  }

  function setup() {
    const outlet = document.querySelector(OUTLET_SEL) || document;
    initIfPresent(outlet);
    const obs = new MutationObserver(() => initIfPresent(outlet));
    obs.observe(outlet, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
