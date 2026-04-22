// generator.js

async function generate() {
  const prompt       = document.getElementById("prompt")?.value || "";
  const content_type = document.getElementById("type")?.value || "";
  const tone         = document.getElementById("tone")?.value || "";
  const resultEl     = document.getElementById("result");
  const btn          = document.getElementById("btnGenerate"); // si tienes un botón

  if (btn) { btn.disabled = true; btn.textContent = "Generando…"; }
  if (resultEl) resultEl.textContent = "Procesando…";

  try {
    // ⚠️ No mandamos Authorization. El backend leerá la cookie access_token.
    // CSRF NO es necesario salvo que tu backend lo exija en /generate/save.
    // Si lo exiges, usa:  apiFetch("/generate/save", {...}, { csrf: true })
    const res = await apiFetch("/generate/save", {
      method: "POST",
      body: JSON.stringify({ prompt, content_type, tone })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      resultEl && (resultEl.textContent = data.detail || data.message || "Error al generar contenido.");
      return;
    }

    resultEl && (resultEl.textContent = data.content || "✅ Contenido generado.");
  } catch (err) {
    resultEl && (resultEl.textContent = "❌ Error de conexión.");
    console.error(err);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Generar"; }
  }
}
