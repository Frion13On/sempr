function ensureOverlay(withBackdrop = false) {
  let overlay = document.getElementById('ui-overlay');
  let content;
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'ui-overlay';
    overlay.style.position = 'fixed';
    overlay.style.inset = '0';
    overlay.style.zIndex = '3000';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.pointerEvents = 'none';
    const inner = document.createElement('div');
    inner.id = 'ui-overlay-inner';
    inner.style.pointerEvents = 'auto';
    overlay.appendChild(inner);
    document.body.appendChild(overlay);
  }
  content = document.getElementById('ui-overlay-inner');
  const show = () => {
    overlay.style.display = 'flex';
    overlay.style.background = withBackdrop ? 'rgba(0,0,0,0.35)' : 'transparent';
  };
  const hide = () => {
    overlay.style.display = 'none';
    overlay.style.background = 'transparent';
    content.innerHTML = '';
  };
  return { container: overlay, content, show, hide };
}

function renderAlert(kind, message) {
  const { content, show, hide } = ensureOverlay();
  content.innerHTML = '';
  const box = document.createElement('div');
  box.style.background = 'var(--color-card-bg)';
  box.style.color = 'var(--color-text)';
  box.style.minWidth = '320px';
  box.style.maxWidth = '560px';
  box.style.border = '1px solid var(--color-border)';
  box.style.borderRadius = '8px';
  box.style.boxShadow = 'var(--elevation-2)';
  box.style.padding = '16px';
  const msg = document.createElement('div');
  msg.className = `alert alert-${kind} show`;
  msg.textContent = message;
  msg.style.margin = '0';
  content.appendChild(box);
  box.appendChild(msg);
  show();
  setTimeout(() => hide(), 2000);
}

function showMessage(message) {
  renderAlert('success', message);
}

function showError(message) {
  renderAlert('danger', message);
}

function showConfirm(message, onConfirm) {
  const { content, show, hide } = ensureOverlay(true);
  content.innerHTML = '';
  const box = document.createElement('div');
  box.style.background = 'var(--color-card-bg)';
  box.style.color = 'var(--color-text)';
  box.style.minWidth = '320px';
  box.style.maxWidth = '560px';
  box.style.border = '1px solid var(--color-border)';
  box.style.borderRadius = '8px';
  box.style.boxShadow = 'var(--elevation-2)';
  box.style.padding = '16px';
  const title = document.createElement('div');
  title.textContent = message;
  title.style.fontWeight = '600';
  title.style.marginBottom = '12px';
  const buttons = document.createElement('div');
  buttons.style.display = 'flex';
  buttons.style.gap = '8px';
  buttons.style.justifyContent = 'flex-end';
  const btnYes = document.createElement('button');
  btnYes.className = 'btn btn-danger btn-sm';
  btnYes.textContent = 'Удалить';
  const btnNo = document.createElement('button');
  btnNo.className = 'btn btn-secondary btn-sm';
  btnNo.textContent = 'Отмена';
  buttons.appendChild(btnNo);
  buttons.appendChild(btnYes);
  content.appendChild(box);
  box.appendChild(title);
  box.appendChild(buttons);
  show();
  const close = () => hide();
  btnNo.addEventListener('click', close);
  btnYes.addEventListener('click', () => { close(); onConfirm && onConfirm(); });
}


