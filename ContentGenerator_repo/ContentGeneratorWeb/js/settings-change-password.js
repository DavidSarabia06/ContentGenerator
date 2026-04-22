// settings.js

// Cambiar contraseña (usa cookie access_token; no requiere CSRF)
function changePassword(e) {
  if (e) e.preventDefault();

  const current_password = document.getElementById("oldPass")?.value.trim() || "";
  const new_password     = document.getElementById("newPass")?.value.trim() || "";
  const confirm          = document.getElementById("confirmPass")?.value.trim() || "";
  const msgEl            = document.getElementById("message");
  const redir            = document.getElementById("redirect");
  const btn              = document.getElementById("btnChangePassword");

  if (!current_password || !new_password) {
    if (msgEl) msgEl.innerText = "❌ Completa todos los campos.";
    return false;
  }
  if (new_password !== confirm) {
    if (msgEl) msgEl.innerText = "❌ Las contraseñas no coinciden.";
    return false;
  }

  if (btn) { btn.disabled = true; btn.textContent = "Actualizando…"; }
  if (msgEl) msgEl.innerText = "Procesando…";

  apiFetch("/auth/change_password", {
    method: "POST",
    body: JSON.stringify({ current_password, new_password })
  })
  .then(async res => {
    const data = await res.json().catch(() => ({}));
    const ok = res.ok;
    if (msgEl) msgEl.innerText = data.message || data.detail || (ok ? "Contraseña actualizada." : "Error al actualizar.");
    if (ok && typeof startRedirectCountdownSPA === "function") {
      startRedirectCountdownSPA(5, "settings", redir || msgEl);
    }
  })
  .catch(err => {
    if (msgEl) msgEl.innerText = "❌ " + (err?.message || "Error de red");
  })
  .finally(() => {
    if (btn) { btn.disabled = false; btn.textContent = "Cambiar contraseña"; }
  });

  return false;
}
