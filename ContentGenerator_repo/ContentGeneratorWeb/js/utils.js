
window.encryptValue = async function (value) {
  try {
    const response = await fetch(`${API}/crypto/encrypt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: value })
    });

    const data = await response.json();
    return data.encrypted || null;
  } catch (err) {
    console.error("❌ Error al cifrar:", err);
    return null;
  }
};

window.decryptStoredValue = async function (encryptedKey) {
  const encrypted = localStorage.getItem(encryptedKey);
  if (!encrypted) return null;

  try {
    const response = await fetch(`${API}/crypto/decrypt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: encrypted })
    });

    const data = await response.json();
    return data.decrypted || null;
  } catch (err) {
    console.error("❌ Error al descifrar:", err);
    return null;
  }
};

// Rate-limits
window.handleRateLimit = async function(res, msgEl, btn) {
  if (res.status !== 429) return false;
  const data = await res.clone().json().catch(() => ({}));
  const baseMsg = data.detail || "Demasiadas solicitudes. Intenta más tarde.";

  // Si no tenemos permiso para leer Retry-After o no viene, mostramos el mensaje plano
  const retry = parseInt(res.headers.get("Retry-After") || "0", 10);
  if (!retry || retry <= 0) {
    if (msgEl) msgEl.textContent = "❌ " + baseMsg;
    return true;
  }

  // Countdown UI y bloqueo de botón
  if (btn) btn.disabled = true;
  let secs = retry;
  const update = () => {
    if (msgEl) msgEl.textContent = `⏳ ${baseMsg} Reintenta en ${secs}s…`;
  };
  update();
  await new Promise(resolve => {
    const id = setInterval(() => {
      secs--;
      update();
      if (secs <= 0) { clearInterval(id); resolve(); }
    }, 1000);
  });
  if (btn) btn.disabled = false;
  return true;
};



// Generalizar mostrar/ocultar contraseña para múltiples campos
document.addEventListener("DOMContentLoaded", () => {
  // Selecciona todos los iconos de tipo 'eye' dentro de .eye-icon
  document.querySelectorAll(".eye-icon").forEach(toggle => {
    toggle.addEventListener("click", () => {
      const input = toggle.previousElementSibling; // El input debe estar justo antes del icono
      const icon = toggle.querySelector("i");

      if (input && input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else if (input) {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    });
  });
});
