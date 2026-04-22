/**
 * Inicia un contador con redirección automática.
 * @param {number} seconds - Segundos hasta redirigir.
 * @param {string} target - URL de destino.
 * @param {HTMLElement|null} customElement - Elemento donde mostrar el mensaje (opcional).
 */
function startRedirectCountdown(seconds = 5, target = "login.html", customElement = null) {
  const countdown = customElement || document.createElement("p");

  if (!customElement) {
    countdown.style.color = "#0078d4";
    countdown.style.fontWeight = "bold";
    countdown.style.marginTop = "1rem";
    document.querySelector(".container1")?.appendChild(countdown);
  }

  countdown.textContent = `Se te redirigirá en ${seconds} segundos...`;

  const interval = setInterval(() => {
    seconds--;
    countdown.textContent = `Se te redirigirá en ${seconds} segundos...`;
    if (seconds <= 0) {
      clearInterval(interval);
      window.location.href = target;
    }
  }, 1000);
}


/**
 * Inicia un contador con redirección SPA.
 * @param {number} seconds - Segundos hasta redirigir.
 * @param {string} target - Destino: p.ej. "settings", "history", "settings/change-password" o "back" para volver.
 * @param {HTMLElement|null} mountEl - Dónde pintar el mensaje (opcional). Si no, se añade a .container2.
 * @returns {{cancel: Function}} - Para cancelar el countdown si hace falta.
 */
function startRedirectCountdownSPA(seconds = 5, target = "settings", mountEl = null) {
  const host = mountEl || document.createElement("p");
  if (!mountEl) {
    host.style.color = "#0078d4";
    host.style.fontWeight = "bold";
    host.style.marginTop = "1rem";
    // Intenta inyectar en el layout actual
    (document.querySelector(".container2") || document.body).appendChild(host);
  }

  // Normaliza a page name para navigateTo
  const normalizeRoute = (t) => String(t || "").replace(/^#?\//, "");
  const go = () => {
    if (target === "back") {
      // Vuelve a la ruta anterior sin recargar
      if (history.length > 1) history.back();
      else if (window.navigateTo) navigateTo("generator");
      else location.hash = "#/generator";
      return;
    }
    const page = normalizeRoute(target);
    if (window.navigateTo) navigateTo(page);
    else location.hash = `#/${page}`; // fallback suave
  };

  host.textContent = host.textContent+`Se te redirigirá en ${seconds} segundos...`;
  const interval = setInterval(() => {
    seconds--;
    host.textContent = `Se te redirigirá en ${seconds} segundos...`;
    if (seconds <= 0) {
      clearInterval(interval);
      go();
    }
  }, 1000);

  return { cancel: () => clearInterval(interval) };
}
