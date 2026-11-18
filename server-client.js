(function () {
  "use strict";
  const cfg = window.SHOP_SCANNER_SERVER_CONFIG || {};
  function enabled() {
    if (!cfg.enabled) return false;
    try { const u = new URL(cfg.baseUrl); return u.protocol === 'https:' && !!u.hostname; }
    catch (_) { return false; }
  }
  async function request(path, options = {}) {
    if (!enabled()) throw new Error('Server connection disabled or invalid HTTPS endpoint');
    if (!/^\/[a-zA-Z0-9/_-]*$/.test(path)) throw new Error('Invalid API path');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), cfg.timeoutMs || 8000);
    try {
      const response = await fetch(new URL(path, cfg.baseUrl.replace(/\/$/, '') + '/'), {
        ...options, signal: controller.signal, credentials: 'omit',
        headers: { 'Accept': 'application/json', ...(options.headers || {}) }
      });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return await response.json();
    } finally { clearTimeout(timer); }
  }
  window.ShopScannerServer = Object.freeze({enabled, request});
})();
