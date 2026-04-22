// js/router.js
(function () {
  const outlet  = document.getElementById("app-view");
  const titleEl = document.getElementById("title-text");
  if (!outlet) { console.error("Falta #app-view en el HTML"); return; }

  const routes = {
    "/generator": { title: "Generador de Contenido", template: "views/generator.html", controller: null },
    "/history":   { title: "Historial de Contenidos", template: "views/history.html",   controller: null },
    "/admin":     { title: "Panel de administración", template: "views/admin.html",      controller: null },
    "/settings":  { title: "Ajustes",                 template: "views/settings.html",   controller: null },
    "/settings/change-password": {
      title: "Cambiar contraseña · Ajustes",
      template: "views/settings-change-password.html",
      controller: null, // usamos scripts de la vista
    },
    "/settings/delete-account": {
      title: "Eliminar cuenta · Ajustes",
      template: "views/settings-delete-account.html",
      controller: null,
    },
    "/404": { title: "No encontrado", template: "views/404.html", controller: null },
  };

  const templateCache = new Map();

  function getPath() {
    const h = location.hash || "#/generator";
    const path = h.replace(/^#/, "");
    return routes[path] ? path : "/404";
  }

  async function loadTemplate(url) {
    if (templateCache.has(url)) return templateCache.get(url);
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error(`No se pudo cargar ${url} (${res.status})`);
    const html = await res.text();
    templateCache.set(url, html);
    return html;
  }

  // 👇 Helper para ejecutar <script> de la vista inyectada
  function hydrateScripts(root) {
    const scripts = Array.from(root.querySelectorAll("script"));
    for (const old of scripts) {
      const s = document.createElement("script");
      if (old.type) s.type = old.type;          // evita type="module" si quieres globals
      if (old.src) {
        s.src = new URL(old.getAttribute("src"), location.href).href;
      } else {
        s.textContent = old.textContent || "";
      }
      if (old.defer) s.defer = true;
      if (old.async) s.async = true;
      old.replaceWith(s);
    }
  }

  async function render() {
    const path = getPath();
    const view = routes[path] || routes["/404"];

    outlet.style.opacity = "0";
    await new Promise(r => requestAnimationFrame(r));

    try {
      const html = await loadTemplate(view.template);
      outlet.innerHTML = html;

      // 👇 MUY IMPORTANTE: hidratar scripts justo después de inyectar la vista
      hydrateScripts(outlet);

    } catch (err) {
      outlet.innerHTML = `
        <div class="card">
          <h3>Error</h3>
          <p class="muted">No se pudo cargar la vista.</p>
        </div>`;
      console.warn(err);
    }

    if (titleEl) titleEl.textContent = view.title;
    document.title = view.title;

    await new Promise(r => requestAnimationFrame(r));
    outlet.style.transition = "opacity 160ms ease";
    outlet.style.opacity = "1";
    setTimeout(() => (outlet.style.transition = ""), 180);

    highlightActive(path);
  }

  function highlightActive(path) {
    document.querySelectorAll('.nav-links li[data-route]').forEach(li => {
      const route = li.getAttribute('data-route');
      const isActive =
        route === path ||
        (route === "/settings" && path.startsWith("/settings")) ||
        (route === "/admin" && path.startsWith("/admin")) ||
        (!location.hash && route === "/generator");
      li.classList.toggle('active', isActive);
    });
  }

  // Navegación
  Object.defineProperty(window, "navigateTo", {
    value: function navigateTo(pageOrRoute) {
      let route = pageOrRoute || "/";
      if (typeof route === "string" && !route.startsWith("/")) route = "/" + route;
      const targetHash = "#" + route;
      if (location.hash !== targetHash) {
        location.hash = targetHash;
      } else {
        render();
      }
      return false;
    }
  });

  window.addEventListener("hashchange", render);
  render();
})();
