// === Canvas & contexto ===
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");

// Posicionamiento detrás del contenido
canvas.style.position = "absolute";
canvas.style.top = "0";
canvas.style.left = "0";
canvas.style.zIndex = "-1";
canvas.style.pointerEvents = "auto";

let pentagons = [];
let mouseX = null;
let mouseY = null;

// === Parámetros base (por segundo) ===
const baseSpeed = 18;         // px/s (aprox. 0.3 * 60fps)
const scaleSpeed = 0.06;      // unidades de escala / s (antes ~0.001*60)
const vertexConnectionDistance = 50;

let reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Cantidades (menos en móvil)
let numSmall = 20, numMedium = 40, numLarge = 10;
if (/Mobi|Android/i.test(navigator.userAgent)) {
  numSmall = 10;
  numMedium = 20;
  numLarge = 5;
}
if (reduceMotion) {
  numSmall = Math.floor(numSmall * 0.6);
  numMedium = Math.floor(numMedium * 0.6);
  numLarge  = Math.floor(numLarge  * 0.6);
}

// Rangos por “tamaño”
const scaleRanges = {
  small:  { min: 0.5, max: 1.0, speedMultiplier: 1.5, rotationSpeed: 0.60 }, // rad/s
  medium: { min: 1.5, max: 2.5, speedMultiplier: 1.0, rotationSpeed: 0.30 },
  large:  { min: 4.0, max: 5.0, speedMultiplier: 0.5, rotationSpeed: 0.12 }
};

// === Efecto visual (onda/ripple) ===
const RIPPLE_DURATION = 0.6;           // s
const RIPPLE_MAX_RADIUS = 260;         // px
const RIPPLE_LINE_WIDTH = 3;

// === Campo visual continuo por mousemove ===
const FIELD_RADIUS = 170;      // mismo radio que la repulsión normal
const FIELD_RADIUS2 = 75;      // mismo radio que la repulsión normal
const FIELD_RINGS = 3;
const FIELD_WAVE_SPEED = 0.55; // ciclos/seg
const FIELD_LINE_WIDTH = 1.5;
const FIELD_ALPHA = 0.25;

// === Blast temporal por click (repulsión fuerte y speed boost local) ===
const CLICK_RADIUS     = FIELD_RADIUS; // zona afectada por el click
const CLICK_DURATION   = 5.0;          // segundos de efecto
const CLICK_FACTOR     = 2.2;          // velocidad objetivo durante el click
const CLICK_DIR_LERP   = 0.35;         // cuán rápido gira hacia la dirección de explosión
const CLICK_PUSH_MULT  = 2.0;          // multiplicador de empuje direccional (vs mousemove)
const CLICK_LERP_ON    = 0.28;         // rapidez al subir a velocidad boost
const CLICK_LERP_OFF   = 0.02;         // rapidez al volver a base

// Control de rendimiento para las ondas
const MAX_RIPPLES = 5;           // máximo de ondas simultáneas
const MIN_CLICK_INTERVAL = 120;  // ms entre ondas (anti-spam)

let ripples = []; // {x, y, startSec}
let lastClickMs = 0;

// Estado del blast (último click)
let blast = { x: 0, y: 0, endSec: 0 };

// Solo crea la onda visual Y activa el blast temporal
function triggerClickEffect(x, y) {
  const nowMs = performance.now();
  if (nowMs - lastClickMs < MIN_CLICK_INTERVAL) return; // rate-limit
  lastClickMs = nowMs;

  // Onda visual
  if (ripples.length >= MAX_RIPPLES) {
    let oldestIdx = 0;
    for (let i = 1; i < ripples.length; i++) {
      if (ripples[i].startSec < ripples[oldestIdx].startSec) oldestIdx = i;
    }
    ripples.splice(oldestIdx, 1);
  }
  ripples.push({ x, y, startSec: nowMs / 1000 });

  // Blast temporal
  blast.x = x;
  blast.y = y;
  blast.endSec = (nowMs / 1000) + CLICK_DURATION;
}

// === HiDPI: manejar CSS px vs buffer real ===
let dpr = 1;
let vignette = null; // offscreen canvas para el viñeteado

function buildVignette() {
  // Canvas offscreen para un gradiente radial multiplicado
  const off = document.createElement("canvas");
  const w = canvas.width, h = canvas.height;
  off.width = w; off.height = h;
  const gtx = off.getContext("2d");

  const grad = gtx.createRadialGradient(
    w / 2, h / 2, Math.min(w, h) / 8,
    w / 2, h / 2, Math.max(w, h)
  );
  grad.addColorStop(0, "rgba(14,14,28,0.4)");
  grad.addColorStop(1, "rgba(0,0,0,1)");

  gtx.fillStyle = grad;
  gtx.fillRect(0, 0, w, h);
  return off;
}

function resizeCanvas() {
  dpr = Math.max(1, window.devicePixelRatio || 1);
  const { innerWidth: w, innerHeight: h } = window;

  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);

  // Proyecta a “CSS px”
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Rehacer viñeteado offscreen
  vignette = buildVignette();
}
resizeCanvas();
window.addEventListener("resize", () => {
  resizeCanvas();
  // Recalcula vértices tras resize
  for (const p of pentagons) calculatePentagonVertices(p);
});

// === Utilidades ===
function normalizeVelocity(p) {
  const mag = Math.hypot(p.dx, p.dy);
  if (!mag) return;
  // Mantiene la magnitud en px/s
  p.dx = (p.dx / mag) * p.speed;
  p.dy = (p.dy / mag) * p.speed;
}

function calculatePentagonVertices(p) {
  const sides = 5;
  const step = (2 * Math.PI) / sides;
  const radius = p.baseRadius * p.scale;
  p.vertices = [];
  for (let i = 0; i < sides; i++) {
    const angle = i * step + p.rotation;
    p.vertices.push({
      x: p.x + radius * Math.cos(angle),
      y: p.y + radius * Math.sin(angle)
    });
  }
}

function smoothstep(edge0, edge1, x) {
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

// Parallax ligero (opcional)
let parallax = { x: 0, y: 0 };
window.addEventListener("mousemove", (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
  const cx = window.innerWidth / 2;
  const cy = window.innerHeight / 2;
  parallax.x = (e.clientX - cx) / cx; // -1..1
  parallax.y = (e.clientY - cy) / cy;
});
window.addEventListener("mouseout", () => {
  mouseX = null;
  mouseY = null;
});
window.addEventListener("click", (e) => {
  triggerClickEffect(e.clientX, e.clientY);
});
window.addEventListener("touchstart", (e) => {
  const t = e.touches && e.touches[0];
  if (t) triggerClickEffect(t.clientX, t.clientY);
}, { passive: true });

// === Creación de pentágonos ===
function createPentagonInRange(range) {
  const radius = Math.random() * 10 + 10; // baseRadius
  const x = Math.random() * (canvas.width / dpr - 2 * radius) + radius;
  const y = Math.random() * (canvas.height / dpr - 2 * radius) + radius;

  const angle = Math.random() * 2 * Math.PI;
  const speedBase = baseSpeed * range.speedMultiplier; // px/s
  const dx = Math.cos(angle) * speedBase;
  const dy = Math.sin(angle) * speedBase;

  const initialScale = Math.random() * (range.max - range.min) + range.min;

  return {
    x, y,
    baseRadius: radius,
    dx, dy,
    speed: speedBase,          // velocidad actual (varía con blast)
    speedBase: speedBase,      // velocidad base (constante)
    rotation: Math.random() * 2 * Math.PI,
    scale: initialScale,
    scaleDirection: Math.random() > 0.5 ? 1 : -1,
    minScale: Math.max(0.1, initialScale - 0.5),
    maxScale: initialScale + 0.5,
    rotationSpeed: range.rotationSpeed, // rad/s
    vertices: []
  };
}

function initPentagons() {
  pentagons = [];
  for (let i = 0; i < numSmall;  i++) pentagons.push(createPentagonInRange(scaleRanges.small));
  for (let i = 0; i < numMedium; i++) pentagons.push(createPentagonInRange(scaleRanges.medium));
  for (let i = 0; i < numLarge;  i++) pentagons.push(createPentagonInRange(scaleRanges.large));
  for (const p of pentagons) calculatePentagonVertices(p);
}
initPentagons();

// === Dibujo ===
let hueShift = 0;

function drawPentagon(p) {
  // Parallax por “profundidad”
  const depth = p.baseRadius < 14 ? 0.03 : (p.baseRadius < 22 ? 0.02 : 0.01);
  const ox = parallax.x * 20 * depth;
  const oy = parallax.y * 20 * depth;

  // Paleta coherente por tamaño con desplazamiento global
  const baseHue = p.baseRadius < 14 ? 205 : (p.baseRadius < 22 ? 145 : 10);
  const hue = (baseHue + hueShift) % 360;
  const color = `hsla(${hue}, 70%, 60%, 0.6)`;

  const sides = 5;
  const step = (2 * Math.PI) / sides;
  const radius = p.baseRadius * p.scale;

  // Glow aditivo ligero
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.beginPath();
  for (let i = 0; i <= sides; i++) {
    const a = i * step + p.rotation;
    const px = (p.x + ox) + radius * Math.cos(a);
    const py = (p.y + oy) + radius * Math.sin(a);
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  }
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();
  ctx.restore();
}

// Helper: mismo criterio de color que tus pentágonos
function getPentagonHue(p) {
  const baseHue = p.baseRadius < 14 ? 205 : (p.baseRadius < 22 ? 145 : 10);
  return (baseHue + hueShift) % 360;
}

function drawVertexConnections() {
  const maxConn = vertexConnectionDistance;
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.lineCap = "round";

  for (let i = 0; i < pentagons.length; i++) {
    const p = pentagons[i];
    const r1 = p.baseRadius * p.scale;

    // Parallax del pentágono A
    const depthA = p.baseRadius < 14 ? 0.03 : (p.baseRadius < 22 ? 0.02 : 0.01);
    const oxA = parallax.x * 20 * depthA;
    const oyA = parallax.y * 20 * depthA;
    const hueA = getPentagonHue(p);

    for (let j = i + 1; j < pentagons.length; j++) {
      const q = pentagons[j];
      const r2 = q.baseRadius * q.scale;

      // Culling rápido por centros+radios
      const dx0 = p.x - q.x, dy0 = p.y - q.y;
      const limit = (r1 + r2 + maxConn);
      if (dx0*dx0 + dy0*dy0 > limit * limit) continue;

      // Parallax del pentágono B
      const depthB = q.baseRadius < 14 ? 0.03 : (q.baseRadius < 22 ? 0.02 : 0.01);
      const oxB = parallax.x * 20 * depthB;
      const oyB = parallax.y * 20 * depthB;
      const hueB = getPentagonHue(q);

      const A = p.vertices, B = q.vertices;
      for (let vi = 0; vi < 5; vi++) {
        const va = A[vi];
        for (let vj = 0; vj < 5; vj++) {
          const vb = B[vj];

          const dx = va.x - vb.x, dy = va.y - vb.y;
          const dist = Math.hypot(dx, dy);
          if (dist >= maxConn) continue;

          const ax = va.x + oxA, ay = va.y + oyA;
          const bx = vb.x + oxB, by = vb.y + oyB;

          const t = dist / maxConn; // 0 cerca, 1 lejos
          const alpha = (1 - t) * 0.7;
          const lineW = Math.max(0.2, 1.3 - t);

          const grad = ctx.createLinearGradient(ax, ay, bx, by);
          grad.addColorStop(0, `hsla(${hueA}, 70%, 60%, ${alpha})`);
          grad.addColorStop(1, `hsla(${hueB}, 70%, 60%, ${alpha})`);

          ctx.strokeStyle = grad;
          ctx.lineWidth = lineW;

          ctx.beginPath();
          ctx.moveTo(ax, ay);
          ctx.lineTo(bx, by);
          ctx.stroke();
        }
      }
    }
  }

  ctx.restore();
}

// Ondas de click con optimización (menos paths)
function drawRipples(nowSec) {
  if (ripples.length === 0) return;

  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.lineWidth = RIPPLE_LINE_WIDTH;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";

  const next = [];
  for (const r of ripples) {
    const t = (nowSec - r.startSec) / RIPPLE_DURATION; // 0..1
    if (t <= 0 || t >= 1) continue;

    const radius = t * RIPPLE_MAX_RADIUS;
    const alpha = 1 - t;
    const hue = (200 + hueShift) % 360;

    ctx.beginPath();
    ctx.strokeStyle = `hsla(${hue}, 80%, 70%, ${alpha})`;
    ctx.arc(r.x, r.y, radius, 0, Math.PI * 2);
    ctx.stroke();

    next.push(r);
  }
  ripples = next;
  ctx.restore();
}

// Campo visual continuo del ratón
function drawMouseField(nowSec) {
  if (mouseX === null || mouseY === null) return;

  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.lineWidth = FIELD_LINE_WIDTH;

  const hue = (200 + hueShift) % 360;

  if (reduceMotion) {
    ctx.beginPath();
    ctx.strokeStyle = `hsla(${hue}, 80%, 70%, 0.15)`;
    ctx.arc(mouseX, mouseY, FIELD_RADIUS2 - 25, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
    return;
  }

  for (let i = 0; i < FIELD_RINGS; i++) {
    const t = (nowSec * FIELD_WAVE_SPEED + i / FIELD_RINGS) % 1;
    const r = (0.6 + 0.4 * t) * FIELD_RADIUS2;
    const alpha = (1 - t) * FIELD_ALPHA;

    ctx.beginPath();
    ctx.strokeStyle = `hsla(${hue}, 80%, 70%, ${alpha})`;
    ctx.arc(mouseX, mouseY, r, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.restore();
}

// === Update ===
function updatePentagons(dt, nowSec) {
  const influenceRadius = FIELD_RADIUS; // repulsión normal por mousemove
  const lerp = 0.18;                    // suavidad hacia objetivo

  const blastActive = nowSec < blast.endSec;

  for (let i = 0; i < pentagons.length; i++) {
    const p = pentagons[i];

    // Movimiento
    p.x += p.dx * dt;
    p.y += p.dy * dt;
    p.rotation += p.rotationSpeed * dt;

    // Rebotes
    const r = p.baseRadius * p.scale;
    const W = canvas.width / dpr, H = canvas.height / dpr;
    if (p.x - r < 0 || p.x + r > W) { p.dx *= -1; p.dy *= 0.98; p.x = Math.max(r, Math.min(W - r, p.x)); }
    if (p.y - r < 0 || p.y + r > H) { p.dy *= -1; p.dx *= 0.98; p.y = Math.max(r, Math.min(H - r, p.y)); }

    // Repulsión normal por ratón (si está dentro del área)
    if (mouseX !== null && mouseY !== null) {
      const dx = mouseX - p.x, dy = mouseY - p.y;
      const d = Math.hypot(dx, dy);
      if (d < influenceRadius && d > 1e-3) {
        const dirx = -(dx / d), diry = -(dy / d);
        const k = smoothstep(influenceRadius, 0, d); // 0..1
        const targetX = dirx * p.speed * (k * 1.4) + p.dx * (1 - k);
        const targetY = diry * p.speed * (k * 1.4) + p.dy * (1 - k);
        p.dx = p.dx + (targetX - p.dx) * lerp;
        p.dy = p.dy + (targetY - p.dy) * lerp;
      }
    }

    // --- Repulsión extra por CLICK (más fuerte, temporal, zona del blast) ---
    let affectedByBlast = false;
    if (blastActive) {
      const bdx = p.x - blast.x; // empuje hacia afuera (desde el click)
      const bdy = p.y - blast.y;
      const bd  = Math.hypot(bdx, bdy);
      if (bd < CLICK_RADIUS && bd > 1e-3) {
        const dirx = bdx / bd, diry = bdy / bd; // dirección de explosión
        const k = smoothstep(CLICK_RADIUS, 0, bd); // 0..1 más fuerte cerca
        const targetX = dirx * p.speed * (k * CLICK_PUSH_MULT) + p.dx * (1 - k);
        const targetY = diry * p.speed * (k * CLICK_PUSH_MULT) + p.dy * (1 - k);
        p.dx = p.dx + (targetX - p.dx) * CLICK_DIR_LERP;
        p.dy = p.dy + (targetY - p.dy) * CLICK_DIR_LERP;
        affectedByBlast = true;
      }
    }

    // Colisiones (manteniendo magnitud con la velocidad ACTUAL de cada uno)
    for (let j = i + 1; j < pentagons.length; j++) {
      const q = pentagons[j];
      const dist = Math.hypot(q.x - p.x, q.y - p.y);
      const minDist = p.baseRadius * p.scale + q.baseRadius * q.scale;

      if (dist < minDist && dist > 0) {
        const angle = Math.atan2(q.y - p.y, q.x - p.x);
        const overlap = 0.5 * (minDist - dist + 1);
        const offsetX = overlap * Math.cos(angle);
        const offsetY = overlap * Math.sin(angle);

        p.x -= offsetX; p.y -= offsetY;
        q.x += offsetX; q.y += offsetY;

        // Reorienta velocidades manteniendo su magnitud actual
        p.dx = -Math.cos(angle) * p.speed;
        p.dy = -Math.sin(angle) * p.speed;
        q.dx =  Math.cos(angle) * q.speed;
        q.dy =  Math.sin(angle) * q.speed;
      }
    }

    // Escalado suave
    if (!reduceMotion) {
      p.scale += scaleSpeed * p.scaleDirection * dt;
      if (p.scale > p.maxScale || p.scale < p.minScale) p.scaleDirection *= -1;
    }

    // --- Control de velocidad temporal (sube con click, baja cuando termina) ---
    const desiredSpeed = (blastActive && affectedByBlast)
      ? (p.speedBase * CLICK_FACTOR)
      : p.speedBase;
    const lerpAmt = (blastActive && affectedByBlast) ? CLICK_LERP_ON : CLICK_LERP_OFF;
    p.speed = p.speed + (desiredSpeed - p.speed) * lerpAmt;

    // Mantener magnitud (con la velocidad actualizada)
    normalizeVelocity(p);
    calculatePentagonVertices(p);
  }
}

// === Loop ===
let last = performance.now();
function animate(now = performance.now()) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  const nowSec = now / 1000;

  // Paleta
  hueShift = (hueShift + (reduceMotion ? 0.02 : 0.05)) % 360;

  // Trails
  ctx.save();
  ctx.globalCompositeOperation = "source-over";
  ctx.fillStyle = reduceMotion ? "rgba(0,0,0,0.15)" : "rgba(0,0,0,0.08)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.restore();

  // Viñeteado
  if (vignette) {
    ctx.save();
    ctx.globalCompositeOperation = "multiply";
    ctx.drawImage(vignette, 0, 0);
    ctx.restore();
  }

  // Campo del ratón
  drawMouseField(nowSec);

  // Ondas por click
  drawRipples(nowSec);

  // Update con blast temporal
  updatePentagons(dt, nowSec);

  drawVertexConnections();
  for (const p of pentagons) drawPentagon(p);

  requestAnimationFrame(animate);
}
animate();
