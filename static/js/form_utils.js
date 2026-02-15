function isValidEmail(value) {
  const v = String(value || '').trim();
  if (!v) return true;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(v);
}

function isValidPhoneValue(value) {
  const v = String(value || '').trim();
  if (!v) return true;
  return /^\d{1,11}$/.test(v);
}

function loginEqualsPassword(loginValue, passwordValue) {
  const l = String(loginValue || '').trim();
  const p = String(passwordValue || '').trim();
  if (!l || !p) return false;
  return l === p;
}

function validatePhoneKeypress(e) {
  if (e.key === 'Backspace' || e.key === 'Delete') return true;
  if (e.target.value.length >= 11) {
    e.preventDefault();
    return false;
  }
  if (!/^\d$/.test(e.key)) {
    e.preventDefault();
    return false;
  }
}

function validateAdminManageForm(currentEntity, forms, sel, showError) {
  const formRoot = forms[currentEntity];
  if (!formRoot) return true;
  const requiredFields = formRoot.querySelectorAll('input[required], select[required]');
  let isValid = true;

  requiredFields.forEach(field => {
    const isHidden = field.offsetParent === null;
    if (isHidden) return;
    if (!String(field.value || '').trim()) {
      field.classList.add('is-invalid');
      isValid = false;
    } else {
      field.classList.remove('is-invalid');
    }
  });

  if (isValid) {
    if (currentEntity === 'users_students') {
      const phone = sel('s_phone');
      const email = sel('s_email');
      const login = sel('s_login');
      const password = sel('s_password');
      if (phone && !isValidPhoneValue(phone.value)) { phone.classList.add('is-invalid'); isValid = false; }
      if (email && !isValidEmail(email.value)) { email.classList.add('is-invalid'); isValid = false; }
      if (loginEqualsPassword(login && login.value, password && password.value)) {
        login.classList.add('is-invalid');
        password.classList.add('is-invalid');
        isValid = false;
      }
    } else if (currentEntity === 'users_teachers') {
      const phone = sel('t_phone');
      const email = sel('t_email');
      const login = sel('t_login');
      const password = sel('t_password');
      if (phone && !isValidPhoneValue(phone.value)) { phone.classList.add('is-invalid'); isValid = false; }
      if (email && !isValidEmail(email.value)) { email.classList.add('is-invalid'); isValid = false; }
      if (loginEqualsPassword(login && login.value, password && password.value)) {
        login.classList.add('is-invalid');
        password.classList.add('is-invalid');
        isValid = false;
      }
    } else if (currentEntity === 'users_admins') {
      const login = sel('a_login');
      const password = sel('a_password');
      if (loginEqualsPassword(login && login.value, password && password.value)) {
        login.classList.add('is-invalid');
        password.classList.add('is-invalid');
        isValid = false;
      }
    } else if (currentEntity === 'departments') {
      const phone = sel('df_dep_phone');
      const email = sel('df_dep_email');
      if (phone && !isValidPhoneValue(phone.value)) { phone.classList.add('is-invalid'); isValid = false; }
      if (email && !isValidEmail(email.value)) { email.classList.add('is-invalid'); isValid = false; }
    } else if (currentEntity === 'faculties') {
      const phone = sel('df_fac_phone');
      const email = sel('df_fac_email');
      if (phone && !isValidPhoneValue(phone.value)) { phone.classList.add('is-invalid'); isValid = false; }
      if (email && !isValidEmail(email.value)) { email.classList.add('is-invalid'); isValid = false; }
    }
  }

  if (!isValid) showError('Проверьте корректность заполнения полей');
  return isValid;
}



