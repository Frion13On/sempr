function sortRows(rows, getValue, dir, locale = 'ru') {
  const dirMul = dir === 'asc' ? 1 : -1;
  const collator = new Intl.Collator(locale, { numeric: true, sensitivity: 'base' });
  rows.sort((a, b) => {
    const va = (getValue(a) || '').trim();
    const vb = (getValue(b) || '').trim();
    const na = parseFloat(va.replace(',', '.'));
    const nb = parseFloat(vb.replace(',', '.'));
    const isNum = !isNaN(na) && !isNaN(nb) && va !== '' && vb !== '';
    const da = Date.parse(va);
    const db = Date.parse(vb);
    const isDate = !isNaN(da) && !isNaN(db);
    let cmp = 0;
    if (isNum) cmp = na === nb ? 0 : (na < nb ? -1 : 1);
    else if (isDate) cmp = da === db ? 0 : (da < db ? -1 : 1);
    else cmp = collator.compare(va, vb);
    return cmp * dirMul;
  });
  return rows;
}

function reattachRows(tbody, rows) {
  const frag = document.createDocumentFragment();
  rows.forEach(r => frag.appendChild(r));
  tbody.appendChild(frag);
}


