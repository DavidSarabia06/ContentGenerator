// general.js
(function () {
  // Páginas públicas (no requieren sesión)
  const PUBLIC_PAGES = new Set(["login.html", "register.html", "recover_password.html", "", "/"]);

  /**
   * Comprueba sesión con /auth/me (usa cookies HttpOnly).
   * Si no hay sesión válida (ni tras refresh), redirige a login.
   */
  async function requireSessionOrRedirect() {
    const currentPage = window.location.pathname.split("/").pop();
    if (PUBLIC_PAGES.has(currentPage)) return null;

    const res = await apiFetch("/auth/me", { method: "GET" });
    if (!res.ok) {
      window.location.href = "login.html?msg=session_required";
      return null;
    }
    const me = await res.json().catch(() => ({}));

    // Saludo opcional
    const welcomeEl = document.getElementById("welcome-text");
    if (welcomeEl) {
      const username = localStorage.getItem("remembered_username") || me.user_id || "";
      welcomeEl.textContent = username ? `👋 Hola, ${username}` : "👋 Hola";
    }
    return me;
  }

  /**
   * Devuelve true si el usuario es admin; maneja 401/403 sin romper.
   */
  async function isAdmin() {
    try {
      const res = await apiFetch("/auth/check_admin", { method: "GET" }, { retryOn401: true });
      if (!res.ok) return false; // 401/403 => no admin
      const data = await res.json().catch(() => false);
      return Boolean(data);
    } catch {
      return false;
    }
  }

  /**
   * Inserta el item "Administrador" en la sidebar si procede.
   */
  async function ensureAdminSidebarItem() {
    if (!(await isAdmin())) return;

    const bottom = document.querySelector(".bottom-links");
    if (!bottom) return;

    // Evita duplicados si ya existe
    if (bottom.querySelector('li[data-route="/admin"]')) return;

    const settingsLi = bottom.querySelector('li[data-route="/settings"]');
    if (!settingsLi) return;

    const li = document.createElement("li");
    li.setAttribute("data-route", "/admin");
    li.onclick = () => navigateTo("admin");

    const img = document.createElement("img");
    img.src = "icons/admin_light.png";
    img.alt = "Admin";
    img.className = "icon";

    const span = document.createElement("span");
    span.className = "label";
    span.textContent = "Administrador";

    li.appendChild(img);
    li.appendChild(span);
    bottom.insertBefore(li, settingsLi);
  }

  async function boot() {
    const me = await requireSessionOrRedirect();
    if (!me) return;
    await ensureAdminSidebarItem();
  }

  // Espera a que auth_actions.js haya expuesto window.apiFetch
  function waitForApiFetchAndBoot() {
    if (window.apiFetch) {
      boot().catch(() => {});
    } else {
      setTimeout(waitForApiFetchAndBoot, 25);
    }
  }

  document.addEventListener("DOMContentLoaded", waitForApiFetchAndBoot);
})();
