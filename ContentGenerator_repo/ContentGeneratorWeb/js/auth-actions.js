

// ===============================
// ======== UTILIDADES ===========
// ===============================

/**
 * Lee una cookie no-HttpOnly (como csrf_refresh_token).
 * Ojo: access/refresh son HttpOnly ↔ no se pueden leer en JS (¡bien!).
 */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return null;
}

/**
 * Helper: intenta refrescar la sesión con /auth/refresh (CSRF + cookies),
 * y si sale OK, ejecuta el callback para reintentar la operación original.
 */
async function refreshAndRetry(doRequest) {
  const csrf = getCookie("csrf_refresh_token");

  // Si no hay CSRF, no podemos refrescar: redirige a login y no lances error.
  if (!csrf) {
    console.warn("No CSRF cookie present → redirect to login");
    window.location.href = "login.html?msg=session_required";
    return null; // <- CLAVE: no lanzar error
  }

  const ref = await fetch(`${API}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrf }
  });

  if (!ref.ok) {
    console.warn("Refresh failed:", await ref.text());
    window.location.href = "login.html?msg=session_expired";
    return null; // <- CLAVE: no lanzar error
  }

  // Refresh OK → reintenta la request original
  return doRequest();
}
/**
 * Envoltura de fetch para:
 *  - incluir siempre cookies (credentials: 'include')
 *  - adjuntar CSRF cuando se pida (para endpoints que lo requieren)
 *  - reintentar una vez si recibimos 401 por falta de access token
 *
 * @param {string} path - Ruta relativa (p.ej. "/auth/change_password")
 * @param {RequestInit} options - opciones fetch
 * @param {{csrf?: boolean, retryOn401?: boolean}} config
 */
async function apiFetch(path, options = {}, config = {}) {
  const { csrf = false, retryOn401 = true } = config;

  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (csrf) {
    const token = getCookie("csrf_refresh_token");
    if (token) headers.set("X-CSRF-Token", token);
  }

  const exec = () => fetch(`${API}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });

  let res = await exec();

  if (retryOn401 && res.status === 401) {
    try {
      // Si el backend devuelve detalle útil
      const data = await res.clone().json().catch(() => ({}));
      const detail = data?.detail || "";
      if (/Falta access token/i.test(detail) || /Token expirado/i.test(detail)) {
        const retried = await refreshAndRetry(exec);
        if (retried) res = retried;   // si es null, mantenemos el 401 y el redirect ya habrá ocurrido
      } else {
        const retried = await refreshAndRetry(exec);
        if (retried) res = retried;
      }
    } catch {
      const retried = await refreshAndRetry(exec);
      if (retried) res = retried;
    }
  }

  return res;
}


// ===============================
// ======== AUTENTICACIÓN ========
// ===============================

/**
 * Login:
 *  - NO guarda tokens en localStorage (van en cookies HttpOnly).
 *  - Si "remember" está marcado, recuerda username y (opcional) password cifrada.
 */
async function login() {
  const usernameEl = document.getElementById("username");
  const passwordEl = document.getElementById("password");
  const rememberEl = document.getElementById("remember");
  const msgEl = document.getElementById("message");

  const username = (usernameEl?.value || "").trim();
  const password = (passwordEl?.value || "").trim();
  const remember = !!rememberEl?.checked;

  msgEl && (msgEl.textContent = "");

  try {
    const res = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    }, { retryOn401: false }); // no tiene sentido refrescar antes del primer login

    if (await window.handleRateLimit(res, msgEl, loginBtn)) return;

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      // ✔️ Cookies seteadas por el backend (HttpOnly). No guardes tokens en JS.
      // Opcional: recordar usuario y contraseña (cifrada por ti)
      localStorage.setItem("remembered_username", username);
      localStorage.setItem("remember", String(remember));

      if (remember && typeof encryptValue === "function") {
        const encryptedPassword = await encryptValue(password);
        if (encryptedPassword) {
          localStorage.setItem("remembered_password", encryptedPassword);
        }
      } else {
        localStorage.removeItem("remembered_password");
      }

      // Redirige a tu app
      window.location.href = "index.html";
    } else {
      msgEl && (msgEl.textContent = data.detail || data.message || "Error al iniciar sesión");
    }
  } catch (err) {
    console.error("❌ Error al iniciar sesión:", err);
    msgEl && (msgEl.textContent = "Error de conexión");
  }
}

/**
 * Registro (sin cambios sustanciales; puedes dejarlo igual).
 * No necesita CSRF; el backend no lo pide.
 */
async function register() {
  const username = (document.getElementById("username")?.value || "").trim();
  const email = (document.getElementById("email")?.value || "").trim();
  const password = (document.getElementById("password")?.value || "").trim();
  const button = (document.getElementById("register-button")?.value || "").trim();

  let allow_notifications = true;
  const allowEl = document.getElementById("allow_notifications");
  if (allowEl) allow_notifications = !!allowEl.checked;

  const msgEl = document.getElementById("message");

  try {
    const res = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, email, allow_notifications })
    }, { retryOn401: false });

    if (await window.handleRateLimit(res, msgEl, button)) return;

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      window.location.href = "email_confirmation.html";
    } else {
      if (res.status === 422 && Array.isArray(data.detail) && data.detail.some(d => (d.loc || []).includes("email"))) {
        msgEl && (msgEl.textContent = "❌ El correo electrónico no es válido.");
      } else {
        msgEl && (msgEl.textContent = data.message || data.detail || "Error al registrar usuario.");
      }
    }
  } catch (err) {
    console.error("❌ Error al registrar usuario:", err);
    msgEl && (msgEl.textContent = "Error al registrar usuario.");
  }
}

/**
 * Autocompletar login si se marcó "recordarme".
 */
async function prefillUser() {
  const remember = localStorage.getItem("remember") === "true";
  const username = localStorage.getItem("remembered_username") || "";

  const rememberEl = document.getElementById("remember");
  const usernameEl = document.getElementById("username");
  const passwordEl = document.getElementById("password");

  if (rememberEl) rememberEl.checked = remember;
  if (usernameEl) usernameEl.value = username;

  if (remember && typeof decryptStoredValue === "function") {
    const decrypted = await decryptStoredValue("remembered_password");
    if (decrypted && passwordEl) passwordEl.value = decrypted;
  }
}

/**
 * Cambiar contraseña:
 *  - Usa cookie access_token (no Authorization).
 *  - Si falta access o expira → apiFetch hará refresh y reintentará.
 */

/**
 * Logout:
 *  - Requiere CSRF (cabecera X-CSRF-Token + cookie csrf_refresh_token).
 *  - El backend limpiará cookies.
 */
async function logout() {
  const msgEl = document.getElementById("message");
  try {
    const res = await apiFetch("/auth/logout", { method: "POST" }, { csrf: true, retryOn401: false });
    if (res.ok) {
      // Limpieza local de “recordarme” (opcional)
      // localStorage.removeItem("remembered_username");
      // localStorage.removeItem("remembered_password");
      // localStorage.removeItem("remember");
      window.location.href = "login.html?msg=logged_out";
    } else {
      const data = await res.json().catch(() => ({}));
      msgEl && (msgEl.textContent = data.detail || "No se pudo cerrar sesión");
    }
  } catch (e) {
    msgEl && (msgEl.textContent = "Error de conexión");
  }
}

// ===============================
// ====== BOOTSTRAP PÁGINA =======
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const msg = params.get("msg");

  if (msg === "verified") {
    const messageEl = document.getElementById("message");
    if (messageEl) {
      messageEl.textContent = "✅ Correo verificado con éxito. Ya puedes iniciar sesión.";
    }
  }

  if (window.location.pathname.includes("login.html")) {
    prefillUser();
  }
});

// Al final de auth_actions.js
if (typeof window !== "undefined") {
  window.apiFetch = apiFetch;
  window.refreshAndRetry = refreshAndRetry;
  window.getCookie = getCookie;
}
