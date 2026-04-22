// admin_actions.js

function adminRegisterUser() {
  const username            = document.getElementById("regUsername")?.value.trim() || "";
  const email               = document.getElementById("regEmail")?.value.trim() || "";
  const password            = document.getElementById("regPassword")?.value || "";
  const isAdmin             = !!document.getElementById("regIsAdmin")?.checked;
  const allow_notifications = !!document.getElementById("regAllowNotifications")?.checked;
  const msgEl               = document.getElementById("adminMsg") || document.getElementById("message");

  if (!username || !email || !password) {
    if (msgEl) msgEl.textContent = "❌ Rellena usuario, email y contraseña.";
    return;
  }

  const btn = document.getElementById("btnAdminRegister");
  const original = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = "Creando…"; }

  // ⬇️ Sin Authorization. Cookies + CSRF (X-CSRF-Token) van con apiFetch
  apiFetch("/admin/register_user_by_admin", {
    method: "POST",
    body: JSON.stringify({ username, email, password, isAdmin, allow_notifications })
  }, { csrf: true }) // 👈 requiere CSRF
  .then(async res => {

    if (await window.handleRateLimit(res, msgEl, btn)) return;

    const data = await res.json().catch(() => ({}));
    if (msgEl) msgEl.textContent = data.message || data.detail || (res.ok ? "Usuario creado." : "No se pudo crear el usuario.");
    if (res.ok) {
      ["regUsername","regEmail","regPassword"].forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });
      const c1 = document.getElementById("regIsAdmin"); if (c1) c1.checked = false;
      const c2 = document.getElementById("regAllowNotifications"); if (c2) c2.checked = true;
    }
  })
  .catch(err => { if (msgEl) msgEl.textContent = "❌ " + (err?.message || "Error de red"); })
  .finally(() => { if (btn) { btn.disabled = false; btn.textContent = original || "Crear usuario"; } });
}

function adminDeleteUserByName() {
  const username = document.getElementById("adminDelUser")?.value.trim() || "";
  const msgEl    = document.getElementById("adminMsgDelete") || document.getElementById("adminMsg");

  if (!username) { if (msgEl) msgEl.textContent = "❌ Indica el username a eliminar."; return; }

  const btn = document.getElementById("btnDeleteUser");
  const old = btn?.textContent;
  if (btn) { btn.disabled = true; btn.textContent = "Eliminando…"; }
  if (msgEl) msgEl.textContent = "Procesando…";

  // ⬇️ Sin Authorization. Cookies + CSRF (X-CSRF-Token) van con apiFetch
  apiFetch(`/admin/users/${encodeURIComponent(username)}`, {
    method: "DELETE"
  }, { csrf: true }) // 👈 requiere CSRF
  .then(async res => {
    const data = await res.json().catch(() => ({}));
    if (msgEl) msgEl.textContent = (data.message || data.detail || (res.ok ? "Usuario eliminado." : "No se pudo eliminar el usuario."));
    if (res.ok) {
      const inp = document.getElementById("adminDelUser");
      if (inp) inp.value = "";
    }
  })
  .catch(err => { if (msgEl) msgEl.textContent = "❌ " + (err?.message || "Error de red"); })
  .finally(() => { if (btn) { btn.disabled = false; btn.textContent = old || "Eliminar usuario"; } });
}
