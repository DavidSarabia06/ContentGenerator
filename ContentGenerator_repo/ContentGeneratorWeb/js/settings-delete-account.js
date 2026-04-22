// settings.js

// Eliminar cuenta (requiere CSRF: cookie + header X-CSRF-Token)
function deleteAccount(e) {
  if (e) e.preventDefault();

  const confirm_text     = document.getElementById("confirmText")?.value.trim() || "";
  const current_password = document.getElementById("currentPassDelete")?.value?.trim() || ""; // opcional
  const msgEl            = document.getElementById("message");
  const redirHost        = document.getElementById("redirect") || msgEl;
  const btn              = document.getElementById("btnDeleteAccount");

  if (confirm_text.toUpperCase() !== "ELIMINAR") {
    if (msgEl) msgEl.innerText = "❌ Debes escribir ELIMINAR para confirmar.";
    return false;
  }

  const payload = current_password ? { confirm_text, current_password } : { confirm_text };

  if (btn) { btn.disabled = true; btn.textContent = "Eliminando…"; }
  if (msgEl) msgEl.innerText = "Procesando…";

  apiFetch("/auth/delete_account", {
    method: "POST",
    body: JSON.stringify(payload)
  }, { csrf: true }) // 👈 acción destructiva → exige CSRF
  .then(async res => {
    const data = await res.json().catch(() => ({}));
    const ok = res.ok;
    if (msgEl) msgEl.innerText = data.message || data.detail || (ok ? "Cuenta eliminada." : "Error al eliminar.");
    if (ok) {
      // El backend ya limpia cookies y revoca refresh; simplemente redirige.
      if (typeof startRedirectCountdownSPA === "function") {
        startRedirectCountdown(3, "login.html", redirHost);
      } else {
        window.location.href = "login.html";
      }
    }
  })
  .catch(err => {
    if (msgEl) msgEl.innerText = "❌ " + (err?.message || "Error de red");
  })
  .finally(() => {
    if (btn) { btn.disabled = false; btn.textContent = "Eliminar cuenta"; }
  });

  return false;
}
