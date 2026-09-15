/* ==========================================================================
   PAGA — scroll-driven satellite deconstruction (Canvas 2D, asset-free)

   Draws a stylized satellite with glossy PBR-ish materials faked via
   gradients + a moving specular sweep, then explodes it into an annotated
   engineering view as scroll progress (0..1) increases. Two-speed layers
   (background dust vs. foreground satellite) give real parallax depth
   inside the canvas itself. No external images/video required — this is
   the whole point: it always renders, on any machine, with zero 404s.
   ========================================================================== */

function css(varName, fallback) {
  const v = getComputedStyle(document.body).getPropertyValue(varName).trim();
  return v || fallback;
}

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function lerp(a, b, t) { return a + (b - a) * t; }
function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

function roundRectPath(ctx, x, y, w, h, r) {
  const rr = Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

// Fills a shape already set as the current path with a base gradient + a
// slowly-sweeping specular highlight clipped to that same shape. This is
// the "glossy" material technique reused for every part (gold MLI, blue
// glass panels, ceramic dish, brushed metal boom/thrusters).
function glossFill(ctx, x, y, w, h, colorA, colorB, t, sweepSpeed = 0.35) {
  const grad = ctx.createLinearGradient(x, y, x, y + h);
  grad.addColorStop(0, colorA);
  grad.addColorStop(0.5, colorB);
  grad.addColorStop(1, colorA);
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.save();
  ctx.clip();
  const sweepX = x + w / 2 + Math.sin(t * sweepSpeed) * w * 0.7;
  const hg = ctx.createLinearGradient(sweepX - w * 0.3, y, sweepX + w * 0.3, y + h);
  hg.addColorStop(0, 'rgba(255,255,255,0)');
  hg.addColorStop(0.5, 'rgba(255,255,255,0.32)');
  hg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = hg;
  ctx.fillRect(x, y, w, h);
  ctx.restore();
}

export function createSatelliteScene(canvas) {
  const ctx = canvas.getContext('2d');
  let dpr = Math.min(window.devicePixelRatio || 1, 2);
  let width = 0, height = 0;
  let progress = 0;      // raw scroll progress, 0..1
  let displayProgress = 0; // eased/lerped for smooth motion
  let running = false;
  let rafId = null;
  const clock = { t: 0 };
  const mouse = { x: 0, y: 0, tx: 0, ty: 0 };

  const dust = Array.from({ length: 46 }, () => ({
    x: Math.random(), y: Math.random(), r: Math.random() * 1.4 + 0.3, a: Math.random() * 0.5 + 0.15,
  }));

  const PARTS = [
    { id: 'bus',    title: 'Spacecraft Bus',    spec: 'Aluminum honeycomb chassis · gold MLI blanket', side: 'left',  slot: 0, dx: 0,     dy: 0.05,  dist: 0.10 },
    { id: 'panelL', title: null,                spec: null,                                              side: null,   slot: 0, dx: -1,    dy: 0,     dist: 0.42 },
    { id: 'panelR', title: 'Solar Array',       spec: 'GaAs triple-junction cells · 28% efficiency',    side: 'right', slot: 0, dx: 1,     dy: 0,     dist: 0.42 },
    { id: 'dish',   title: 'Ka-Band Antenna',   spec: '1.2m parabolic dish · high-gain feed',           side: 'right', slot: 1, dx: 0.25,  dy: -1,    dist: 0.34 },
    { id: 'boom',   title: 'Sensor Boom',       spec: 'Magnetometer + star tracker mount',              side: 'left',  slot: 1, dx: -0.2,  dy: 0.9,   dist: 0.36 },
    { id: 'thrust', title: 'Thruster Cluster',  spec: 'Bipropellant RCS · attitude control',            side: 'left',  slot: 2, dx: 0.05,  dy: 1,     dist: 0.30 },
  ];

  function resize() {
    const rect = canvas.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = rect.width;
    height = rect.height;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function setProgress(p) {
    progress = clamp(p, 0, 1);
  }

  // explosion rises 0.08→0.42, holds at 1 through the mid-scroll, falls back
  // to 0 by the very end so the satellite is reassembled leaving the section
  function explosionAmount(p) {
    const rise = smoothstep(0.08, 0.42, p);
    const fall = smoothstep(0.86, 1.0, p);
    return clamp(rise - fall, 0, 1);
  }

  function phaseLabel(p) {
    if (p < 0.1) return 'ASSEMBLED';
    if (p < 0.45) return 'DECONSTRUCTING';
    if (p < 0.86) return 'ENGINEERING VIEW';
    return 'REASSEMBLING';
  }

  function draw() {
    if (!width || !height) return;
    ctx.clearRect(0, 0, width, height);

    displayProgress = lerp(displayProgress, progress, 0.08);
    const explosion = explosionAmount(displayProgress);
    const t = clock.t;

    mouse.tx = lerp(mouse.tx, mouse.x, 0.04);
    mouse.ty = lerp(mouse.ty, mouse.y, 0.04);

    // origin sits in the right ~55% of the canvas so left-side captions have room
    const ox = width * (width < 760 ? 0.5 : 0.66);
    const oy = height * 0.52;
    const scale = Math.min(width, height) * (width < 760 ? 0.34 : 0.42);

    // --- background parallax dust (faster-moving layer = feels farther / reads as motion) ---
    const dustDrift = displayProgress * scale * 1.3;
    ctx.save();
    dust.forEach((d, i) => {
      const dx = ox + (d.x - 0.5) * width * 0.9 - dustDrift * 0.6;
      const dy = oy + (d.y - 0.5) * height * 0.9 + Math.sin(t * 0.2 + i) * 4;
      ctx.beginPath();
      ctx.fillStyle = `rgba(62,166,255,${d.a * (0.4 + explosion * 0.6)})`;
      ctx.arc(dx, dy, d.r, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.restore();

    // --- foreground group: idle rotation + subtle scroll drift + mouse tilt (slower than dust = parallax) ---
    const idleRotate = Math.sin(t * 0.15) * 0.05;
    const scrollDrift = -displayProgress * scale * 0.35;
    const tiltX = mouse.tx * 0.06;
    const tiltY = mouse.ty * 0.04;

    ctx.save();
    ctx.translate(ox + scrollDrift + tiltX * scale, oy + tiltY * scale);
    ctx.rotate(idleRotate);

    // faint orbit ring behind everything, fades as it explodes
    ctx.save();
    ctx.globalAlpha = (1 - explosion) * 0.35;
    ctx.strokeStyle = css('--ice-dim', '#1c4a73');
    ctx.setLineDash([3, 6]);
    ctx.lineDashOffset = -t * 12;
    ctx.beginPath();
    ctx.ellipse(0, 0, scale * 1.35, scale * 0.5, 0.35, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    const ice = css('--ice', '#3ea6ff');
    const iceDim = css('--ice-dim', '#1c4a73');
    const rust = css('--rust', '#ff6b35');
    const textHi = css('--text-hi', '#eaf1f8');

    // ---- BUS (gold MLI, glossy clearcoat) ----
    {
      const w = scale * 0.5, h = scale * 0.68;
      const dxp = 0 * scale * explosion * 0.15;
      const dyp = 0.05 * scale * explosion;
      ctx.save();
      ctx.translate(dxp, dyp);
      roundRectPath(ctx, -w / 2, -h / 2, w, h, 6);
      glossFill(ctx, -w / 2, -h / 2, w, h, '#7a5a1c', '#e7c675', t, 0.3);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(234,241,248,0.25)';
      ctx.stroke();
      ctx.restore();
    }

    // ---- SOLAR PANELS (deep glass-blue, cell grid) ----
    [-1, 1].forEach((dir) => {
      const w = scale * 0.85, h = scale * 0.22;
      const restX = dir * scale * 0.45;
      const x = restX + dir * scale * 0.42 * explosion;
      const rot = dir * 0.18 * explosion;
      ctx.save();
      ctx.translate(x, 0);
      ctx.rotate(rot);
      roundRectPath(ctx, -w / 2, -h / 2, w, h, 3);
      glossFill(ctx, -w / 2, -h / 2, w, h, '#0a1826', '#204a72', t + dir, 0.4);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(62,166,255,0.4)';
      ctx.stroke();
      // cell grid lines
      ctx.strokeStyle = 'rgba(62,166,255,0.18)';
      ctx.lineWidth = 0.6;
      for (let i = 1; i < 7; i++) {
        const gx = -w / 2 + (w / 7) * i;
        ctx.beginPath();
        ctx.moveTo(gx, -h / 2 + 2);
        ctx.lineTo(gx, h / 2 - 2);
        ctx.stroke();
      }
      ctx.restore();
    });

    // ---- ANTENNA DISH (ceramic white, glossy) ----
    {
      const w = scale * 0.42, h = scale * 0.3;
      const x = 0.25 * scale * explosion;
      const y = -0.05 * scale - scale * 0.34 * explosion;
      ctx.save();
      ctx.translate(x, y);
      ctx.beginPath();
      ctx.ellipse(0, 0, w / 2, h / 2, 0, 0, Math.PI * 2);
      glossFill(ctx, -w / 2, -h / 2, w, h, '#c7d3de', '#f4f8fb', t, 0.5);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(62,166,255,0.3)';
      ctx.stroke();
      // feed horn
      ctx.fillStyle = iceDim;
      ctx.beginPath();
      ctx.arc(0, 0, w * 0.08, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // ---- SENSOR BOOM (metallic line + head) ----
    {
      const len = scale * 0.55;
      const x = -0.15 * scale * explosion;
      const y = 0.15 * scale + scale * 0.36 * explosion;
      ctx.save();
      ctx.translate(x, y);
      ctx.strokeStyle = '#8b96a5';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(0, -len * 0.4);
      ctx.lineTo(0, len * 0.4);
      ctx.stroke();
      const hw = scale * 0.09;
      roundRectPath(ctx, -hw / 2, len * 0.4 - hw / 4, hw, hw, 2);
      glossFill(ctx, -hw / 2, len * 0.4 - hw / 4, hw, hw, '#3b4652', '#9aa7b4', t, 0.6);
      ctx.fillStyle = ice;
      ctx.beginPath();
      ctx.arc(0, len * 0.4 + hw * 0.35, hw * 0.18, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // ---- THRUSTER CLUSTER ----
    {
      const x = 0.03 * scale * explosion;
      const y = 0.34 * scale + scale * 0.3 * explosion;
      ctx.save();
      ctx.translate(x, y);
      [-1, 0, 1].forEach((i) => {
        const tw = scale * 0.07, th = scale * 0.14;
        ctx.save();
        ctx.translate(i * tw * 1.6, 0);
        ctx.beginPath();
        ctx.moveTo(-tw / 2, 0);
        ctx.lineTo(tw / 2, 0);
        ctx.lineTo(tw * 0.3, th);
        ctx.lineTo(-tw * 0.3, th);
        ctx.closePath();
        glossFill(ctx, -tw / 2, 0, tw, th, '#2a2f36', '#6b7580', t, 0.5);
        ctx.restore();
      });
      ctx.restore();
    }

    ctx.restore(); // end foreground group

    // ---- callout leader lines + labels (screen space, not rotated with group) ----
    const labelAlpha = clamp((explosion - 0.5) / 0.35, 0, 1);
    if (labelAlpha > 0.01) {
      const partsWithLabels = PARTS.filter((p) => p.title);
      const leftSlots = partsWithLabels.filter((p) => p.side === 'left');
      const rightSlots = partsWithLabels.filter((p) => p.side === 'right');

      const drawLabel = (part, index, total, side) => {
        const slotY = height * (0.28 + (index / Math.max(1, total - 1 || 1)) * 0.44);
        const labelX = side === 'left' ? width * 0.05 : width * 0.62;
        const boxW = Math.min(230, width * 0.28);
        const anchorX = ox + part.dx * scale * 0.42 * explosion + (part.id === 'panelR' ? scale * 0.42 * explosion : 0);
        const anchorY = oy + part.dy * scale * 0.36 * explosion;
        const leaderStartX = side === 'left' ? labelX + boxW : labelX;

        ctx.save();
        ctx.globalAlpha = labelAlpha * (part.side ? 1 : 0);
        ctx.strokeStyle = ice;
        ctx.setLineDash([3, 4]);
        ctx.lineDashOffset = -t * 14;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(leaderStartX, slotY);
        ctx.lineTo(anchorX, anchorY);
        ctx.stroke();

        ctx.beginPath();
        ctx.fillStyle = ice;
        ctx.arc(anchorX, anchorY, 3, 0, Math.PI * 2);
        ctx.fill();

        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(10,15,22,0.7)';
        roundRectPath(ctx, labelX, slotY - 22, boxW, 44, 5);
        ctx.fill();
        ctx.strokeStyle = 'rgba(62,166,255,0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.textAlign = side === 'left' ? 'right' : 'left';
        const textX = side === 'left' ? labelX + boxW - 10 : labelX + 10;
        ctx.fillStyle = textHi;
        ctx.font = '600 13px "Space Grotesk", sans-serif';
        ctx.fillText(part.title, textX, slotY - 3);
        ctx.fillStyle = css('--text-mid', '#a9b7c6');
        ctx.font = '11px "JetBrains Mono", monospace';
        const specText = part.spec.length > 42 ? part.spec.slice(0, 40) + '…' : part.spec;
        ctx.fillText(specText, textX, slotY + 13);
        ctx.restore();
      };

      leftSlots.forEach((p, i) => drawLabel(p, i, leftSlots.length, 'left'));
      rightSlots.forEach((p, i) => drawLabel(p, i, rightSlots.length, 'right'));
    }

    clock.t += 0.016;
  }

  function frame() {
    draw();
    if (running) rafId = requestAnimationFrame(frame);
  }

  function start() {
    if (running) return;
    running = true;
    frame();
  }
  function stop() {
    running = false;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
  }

  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = ((e.clientY - rect.top) / rect.height) * 2 - 1;
  });
  canvas.addEventListener('mouseleave', () => { mouse.x = 0; mouse.y = 0; });

  resize();
  return { resize, setProgress, start, stop, explosionAmount, phaseLabel };
}