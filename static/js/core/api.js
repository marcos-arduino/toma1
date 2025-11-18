export const API_BASE = (document.querySelector('meta[name="api-base"]')?.content)
  || (typeof window !== 'undefined' && window.API_BASE)
  || `${location.origin}/api`;

export async function fetchJSON(url, options = {}) {
  const ctrl = new AbortController();
  const timeoutMs = options.timeoutMs ?? 12000;
  const id = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: ctrl.signal });
    const data = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, data };
  } finally {
    clearTimeout(id);
  }
}
