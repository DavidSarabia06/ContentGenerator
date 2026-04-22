// recoverPassword.js
// Requiere haber cargado antes: config.js y auth_actions.js (para API y apiFetch)

// Estado interno sencillo para llevar el email verificado
let verifiedEmail = "";

/** Utilidad: setea texto en un elemento si existe */
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

/** Enviar código de recuperación al email (endpoint público, sin CSRF) */
async function sendResetCode() {
  const email = (document.getElementById("email")?.value || "").trim();
  const messageEl = document.getElementById("message");
  const sendCodeBtn = document.getElementById("send-code-btn");

  if (!email) {
    messageEl && (messageEl.textContent = "❌ Por favor, introduce tu correo electrónico.");
    return;
  }

  // (opcional) validación simple de email
  const simpleEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!simpleEmail.test(email)) {
    messageEl && (messageEl.textContent = "❌ El correo no tiene un formato válido.");
    return;
  }

  // UI estado
  if (sendCodeBtn) { sendCodeBtn.disabled = true; sendCodeBtn.textContent = "Enviando…"; }
  messageEl && (messageEl.textContent = "Procesando…");

  try {
    const res = await apiFetch("/auth/request_reset_password_code", {
      method: "POST",
      body: JSON.stringify({ email })
    }, { retryOn401: false }); // público; no hay sesión que refrescar

    if (await window.handleRateLimit(res, messageEl, sendCodeBtn)) return;

    const data = await res.json().catch(() => ({}));
    if (res.ok) {
      messageEl && (messageEl.textContent = "📩 Código enviado al correo.");
      const codeSection = document.getElementById("code-section");
      if (codeSection) codeSection.style.display = "block";
      if (sendCodeBtn) sendCodeBtn.textContent = "Reenviar código";
    } else {
      messageEl && (messageEl.textContent = data.detail || "❌ No se pudo enviar el código.");
    }
  } catch (err) {
    console.error("Error al enviar código:", err);
    messageEl && (messageEl.textContent = "❌ Error al contactar con el servidor.");
  } finally {
    if (sendCodeBtn) sendCodeBtn.disabled = false;
  }
}

/** Verificar código (endpoint público, sin CSRF) */
async function verifyCode() {
  const code  = (document.getElementById("reset-code")?.value || "").trim();
  const email = (document.getElementById("email")?.value || "").trim();
  const messageEl = document.getElementById("message");
  const sendCodeBtn = document.getElementById("send-code-btn");

  messageEl && (messageEl.textContent = "");

  if (!email || !code) {
    messageEl && (messageEl.textContent = "❗ Introduce el correo y el código recibido.");
    return;
  }

  // (opcional) si esperas 6 dígitos:
  if (!/^\d{6}$/.test(code)) { messageEl.textContent = "❗ El código debe tener 6 dígitos."; return; }

  try {
    const res = await apiFetch("/auth/validate_reset_password_code", {
      method: "POST",
      body: JSON.stringify({ email, code })
    }, { retryOn401: false });

    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      verifiedEmail = email;
      const codeSection = document.getElementById("code-section");
      if (codeSection) codeSection.style.display = "none";
      const newPassSection = document.getElementById("new-password-section");
      if (newPassSection) newPassSection.style.display = "block";
      if (sendCodeBtn) sendCodeBtn.style.display = "none";

      messageEl && (messageEl.textContent = "✅ Código verificado. Introduce tu nueva contraseña.");
    } else {
      messageEl && (messageEl.textContent = data.detail || "❌ Código incorrecto.");
    }
  } catch (err) {
    console.error("❌ Error al verificar código:", err);
    messageEl && (messageEl.textContent = "❌ No se pudo verificar el código.");
  }
}

/** Cambiar contraseña (sin sesión; flujo de fuerza por email verificado) */
async function resetPassword() {
  const password1 = (document.getElementById("password1")?.value || "").trim();
    const password2 = (document.getElementById("password2")?.value || "").trim();
  const messageEl = document.getElementById("message");

  if (!password1 || !password2) {
    messageEl && (messageEl.textContent = "❗ Por favor, completa ambos campos de contraseña.");
    return;
  }

  if (password1 !== password2) {
    messageEl && (messageEl.textContent = "❌ Las contraseñas no coinciden.");
    return;
  }

  if (!verifiedEmail) {
    messageEl && (messageEl.textContent = "❗ Falta el correo electrónico verificado.");
    return;
  }

  // (opcional) validación mínima
  if (password1.length < 4) {
    messageEl && (messageEl.textContent = "❗ La contraseña es demasiado corta.");
    return;
  }

  try {
    const res = await apiFetch("/auth/force_change_password", {
      method: "POST",
      body: JSON.stringify({ email: verifiedEmail, new_password: password1 })
    }, { retryOn401: false });

    // Manejo 429 si tienes un handler global
    if (typeof window.handleRateLimit === "function") {
      if (await window.handleRateLimit(res, messageEl, null)) return;
    }

    const data = await res.json().catch(() => ({}));
    if (res.ok) {
      messageEl && (messageEl.textContent = "✅ Contraseña cambiada con éxito. Redirigiendo…");
      const sec = document.getElementById("new-password-section");
      if (sec) sec.style.display = "none";
      if (typeof startRedirectCountdown === "function") {
        startRedirectCountdown(5, "login.html");
      } else {
        setTimeout(() => { window.location.href = "login.html"; }, 1500);
      }
    } else {
      messageEl && (messageEl.textContent = data.detail || "❌ No se pudo cambiar la contraseña.");
    }
  } catch (err) {
    console.error("❌ Error en la solicitud:", err);
    messageEl && (messageEl.textContent = "❌ Error de conexión con el servidor.");
  }
}
