/* ==========================================================================
   CINT-70 — shared theme toggle
   Persists light/dark across Home · Dashboard · Systems via localStorage.
   ========================================================================== */

const KEY = 'cint70-theme';

export function initTheme(btnId, onChange) {
  const btn = document.getElementById(btnId);
  let isLight = false;
  try { isLight = localStorage.getItem(KEY) === 'light'; } catch (_) {}

  apply(isLight);

  btn?.addEventListener('click', () => {
    isLight = !isLight;
    try { localStorage.setItem(KEY, isLight ? 'light' : 'dark'); } catch (_) {}
    apply(isLight);
  });

  function apply(light) {
    document.body.classList.toggle('light', light);
    if (btn) btn.textContent = light ? '☀️ Light' : '🌙 Dark';
    if (typeof onChange === 'function') onChange(light);
  }
}