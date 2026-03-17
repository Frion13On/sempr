function applyGradeClass(element, value, options) {
  const opts = options || {};
  const vRaw = value == null ? '' : String(value).trim();
  const vUpper = vRaw.toUpperCase();

  element.classList.remove('grade-good', 'grade-mid', 'grade-warn', 'grade-bad', 'grade-absent');

  if (!vRaw) return;

  if (opts.naBad && vRaw.toLowerCase() === 'н/а') {
    element.classList.add('grade-bad');
    return;
  }

  if (vUpper === 'Н') {
    element.classList.add('grade-absent');
    return;
  }

  const num = parseFloat(vRaw.replace(',', '.'));
  if (Number.isNaN(num)) return;

  if (num >= 5) element.classList.add('grade-good');
  else if (num >= 4) element.classList.add('grade-mid');
  else if (num >= 3) element.classList.add('grade-warn');
  else element.classList.add('grade-bad');
}

function normalizeGradeValue(raw) {
  const v = (raw == null ? '' : String(raw)).trim().toUpperCase();
  if (!v) return '';
  if (v === 'Н') return v;
  if (v >= '1' && v <= '5') return v;
  return '';
}

function updateAbsencesVisual(value) {
    const card = document.querySelector('.stats-card');
    if (!card || Number.isNaN(value)) return;
    card.classList.remove('absence-good', 'absence-warn', 'absence-bad');

    if (value <= 1) {
        card.classList.add('absence-good');
    } else if (value <= 3) {
        card.classList.add('absence-warn');
    } else {
        card.classList.add('absence-bad');
    }
}



