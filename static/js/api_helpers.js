function notifyError(message) {
  // Use same UX if ui_utils.js loaded; otherwise fallback to browser alert.
  if (typeof showError === 'function') {
    showError(message);
    return;
  }
  alert(message);
}

function notifyMessage(message) {
  if (typeof showMessage === 'function') {
    showMessage(message);
    return;
  }
  alert(message);
}

async function apiGetJson(url) {
  const resp = await fetch(url);
  let data = null;
  try {
    data = await resp.json();
  } catch (_) {
    data = null;
  }

  if (!resp.ok) {
    const msg = (data && (data.error || data.message)) ? (data.error || data.message) : `HTTP ${resp.status}`;
    throw new Error(msg);
  }
  return data;
}

async function apiRequestJson(url, method, payload = undefined) {
  const options = { method };
  if (payload !== undefined) {
    // window.withCsrfHeader is injected by csrf.js on pages.
    const headers = (typeof window.withCsrfHeader === 'function')
      ? window.withCsrfHeader({ 'Content-Type': 'application/json' })
      : { 'Content-Type': 'application/json' };
    options.headers = headers;
    options.body = JSON.stringify(payload);
  }

  const resp = await fetch(url, options);
  let data = null;
  try {
    data = await resp.json();
  } catch (_) {
    data = null;
  }

  if (!resp.ok) {
    const msg = (data && (data.error || data.message)) ? (data.error || data.message) : `HTTP ${resp.status}`;
    throw new Error(msg);
  }
  return data;
}

