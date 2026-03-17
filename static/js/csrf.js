function getCsrfToken() {
  const el = document.querySelector('meta[name="csrf-token"]');
  return el ? (el.getAttribute('content') || '') : '';
}

function withCsrfHeader(headers) {
  const token = getCsrfToken();
  if (!token) return headers || {};
  return Object.assign({}, headers || {}, { 'X-CSRFToken': token });
}

window.getCsrfToken = getCsrfToken;
window.withCsrfHeader = withCsrfHeader;

