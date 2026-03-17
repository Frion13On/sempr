(() => {
  const sel = id => document.getElementById(id);
  const PASSWORD_MASK = '********';
  const entitySelector = sel('entitySelector');
  const searchInput = sel('searchInput');
  const thead = sel('thead_row');
  const tbody = sel('tbody_rows');

  const forms = {
    users_students: sel('form_users_students'),
    users_teachers: sel('form_users_teachers'),
    users_admins: sel('form_users_admins'),
    disciplines: sel('form_disciplines'),
    groups: sel('form_groups'),
    specialties: sel('form_specialties'),
    assign_teachers_disciplines: sel('form_assign_teachers_disciplines'),
    assign_specialties_disciplines: sel('form_assign_specialties_disciplines'),
    exams: sel('form_exams'),
    departments: sel('form_departments'),
    faculties: sel('form_faculties')
  };

  const headersByEntity = {
    users_students: ['ID', 'ФИО', 'Логин', 'Пол', 'Дата рождения', 'Телефон', 'Почта', 'Группа'],
    users_teachers: ['ID', 'ФИО', 'Логин', 'Пол', 'Дата рождения', 'Телефон', 'Почта', 'Должность', 'Кафедра'],
    users_admins: ['ID', 'ФИО', 'Логин'],
    disciplines: ['ID', 'Название', 'Количество занятий'],
    groups: ['Название группы', 'Специальность', 'Курс', 'Куратор'],
    specialties: ['ID', 'Название специальности', 'Уровень образования', 'Кафедра'],
    assign_teachers_disciplines: ['Преподаватель', 'Дисциплина'],
    assign_specialties_disciplines: ['Специальность', 'Дисциплина'],
    exams: ['ID', 'Дисциплина', 'Преподаватель', 'Группа', 'Дата экзамена'],
    departments: ['Название кафедры', 'Факультет', 'Заведующий', 'Должность', 'Почта', 'Телефон'],
    faculties: ['Название факультета', 'Декан', 'Должность', 'Почта', 'Телефон']
  };

  const apiMap = {
    disciplines: '/api/disciplines',
    groups: '/api/groups',
    specialties: '/api/specialties',
    assign_teachers_disciplines: '/api/discipline-assignments',
    assign_specialties_disciplines: '/api/specialty-assignments',
    exams: '/api/exams',
    departments: '/api/departments_list',
    faculties: '/api/faculties'
  };

  const rowFields = {
    users_students: ['id_студ', 'фио_студ', 'логин', 'пол', 'дата_рождения', 'телефон', 'почта', 'название_группы'],
    users_teachers: ['id_преп', 'фио_преп', 'логин', 'пол', 'дата_рождения', 'телефон', 'почта', 'должность', 'кафедра'],
    users_admins: ['код_адм', 'фио_адм', 'логин'],
    disciplines: ['id_дисц', 'название', 'количество_занятий'],
    groups: ['название_группы','Специальность','курс','Куратор'],
    specialties: ['id_спец','название_спец','уровень_образования','кафедра'],
    exams: ['id_экзамен','Дисциплина','Преподаватель','название_группы','дата_экзамена'],
    departments: ['назв_каф','факультет','заведующий','должность_каф','почта_каф','тел_каф'],
    faculties: ['назв_факультет','декан','должность_ф','почта_ф','тел_ф'],
    assign_teachers_disciplines: ['ФИО_преп','Название'],
    assign_specialties_disciplines: ['Название_спец','Название']
};

function renderRow(entityKey, row) {
    return rowFields[entityKey].map(field => {
        let value = row[field] || '';
        if (typeof value === "string" && field.toLowerCase().includes('дата')) {
            value = formatDate(value);
        }
        return `<td>${value}</td>`;
    }).join('');
}

  const idGetters = {
    users_students: (row) => row['id_студ'],
    users_teachers: (row) => row['id_преп'],
    users_admins: (row) => row['код_адм'],
    disciplines: (row) => row['id_дисц'],
    groups: (row) => row['название_группы'],
    specialties: (row) => row['id_спец'],
    exams: (row) => row['id_экзамен'],
    departments: (row) => row['назв_каф'],
    faculties: (row) => row['назв_факультет'],
    assign_teachers_disciplines: (row) => `${row['ФИО_преп']}|${row['Название']}`,
    assign_specialties_disciplines: (row) => `${row['Название_спец']}|${row['Название']}`
  };

  const payloadBuilders = {
    disciplines: () => ({
      Название: sel('d_name').value,
      Количество_занятий: parseInt(sel('d_lessons').value)
    }),
    groups: () => ({
      Название_группы: sel('g_name').value,
      Специальность: sel('g_specialty').value,
      Курс: parseInt(sel('g_course').value),
      Куратор: sel('g_curator').value
    }),
    specialties: () => ({
      ID_спец: sel('s_id').value,
      Название_спец: sel('s_name').value,
      Уровень_образования: sel('s_level').value,
      Кафедра: sel('s_department').value
    }),
    exams: () => ({
      Дисциплина: sel('e_discipline').value,
      Преподаватель: sel('e_teacher').value,
      Название_группы: sel('e_group').value,
      Дата_экзамена: sel('e_date').value
    }),
    departments: () => ({
      Назв_каф: sel('df_dep_name').value,
      Факультет: sel('df_dep_faculty').value,
      Заведующий: sel('df_dep_head').value,
      Должность_каф: sel('df_dep_position').value,
      Почта_каф: sel('df_dep_email').value,
      Тел_каф: sel('df_dep_phone').value
    }),
    faculties: () => ({
      Назв_факультет: sel('df_fac_name').value,
      Декан: sel('df_fac_dean').value,
      Должность_ф: sel('df_fac_position').value,
      Почта_ф: sel('df_fac_email').value,
      Тел_ф: sel('df_fac_phone').value
    }),
    assign_teachers_disciplines: () => ({
      ФИО_преп: sel('atd_teacher').value,
      Название: sel('atd_discipline').value
    }),
    assign_specialties_disciplines: () => ({
      Название_спец: sel('asd_specialty').value,
      Название: sel('asd_discipline').value
    })
  };

  let currentEntity = 'users_admins';
  let selectedId = null;
  let currentDataAbortController = null;
  let searchDebounceTimer = null;
  let requestInFlight = false;
  let lastDataRequestId = 0;
  const sortStateByEntity = {};

  function init() {
    entitySelector.addEventListener('change', onEntityChange);
    searchInput.addEventListener('input', onSearchChange);
    sel('btn_save').addEventListener('click', onSave);
    sel('btn_edit').addEventListener('click', onEdit);
    sel('btn_delete').addEventListener('click', onDelete);
    sel('btn_reload').addEventListener('click', onReload);
    tbody.addEventListener('click', onRowClick);
    tbody.addEventListener('dblclick', onRowDoubleClick);
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
      input.addEventListener('input', formatPhoneInput);
      input.addEventListener('keypress', validatePhoneKeypress);
    });
    setTimeout(() => {
      entitySelector.value = 'users_admins';
      currentEntity = entitySelector.value;
      entitySelector.selectedIndex = 2;
      onEntityChange();
    }, 100);
  }

  function onEntityChange() {
    if (requestInFlight) return;
    currentEntity = entitySelector.value;
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = null;
    }
    if (currentDataAbortController) {
      currentDataAbortController.abort();
      currentDataAbortController = null;
    }
    
    setVisibleForm(currentEntity);
    renderHeaders(currentEntity);
    loadData(currentEntity);
    clearForm();
    loadAutoCompleteData(currentEntity);
  }

  function setVisibleForm(entity) {
    Object.entries(forms).forEach(([key, el]) => {
      if (!el) return;
      el.classList.toggle('d-none', key !== entity);
    });
  }

  function renderHeaders(entity) {
    thead.innerHTML = '';
    const headers = headersByEntity[entity] || [];
    headers.forEach((h, idx) => {
      const th = document.createElement('th');
      th.textContent = h;
      th.style.cursor = 'pointer';
      th.dataset.index = String(idx);
      th.addEventListener('click', onHeaderClick);
      const indicator = document.createElement('span');
      indicator.className = 'ms-1 sort-ind';
      indicator.style.fontSize = '0.8em';
      th.appendChild(indicator);
      thead.appendChild(th);
    });
    updateHeaderIndicators();
  }

  async function loadData(entity, search = '') {
    tbody.innerHTML = '';
    const requestId = ++lastDataRequestId;
    try {
      if (currentDataAbortController) {
        currentDataAbortController.abort();
      }
      currentDataAbortController = new AbortController();
      const { signal } = currentDataAbortController;
      let url, data;
      
      if (entity.startsWith('users_')) {
        const tableMap = {
          'users_students': { table: 'студенты', fioField: 'фио_студ' },
          'users_teachers': { table: 'преподаватели', fioField: 'фио_преп' },
          'users_admins': { table: 'администраторы', fioField: 'фио_адм' }
        };
        const config = tableMap[entity];
        url = `/api/get_users?table=${config.table}&fioField=${config.fioField}&search=${encodeURIComponent(search)}`;
      } else {
        url = apiMap[entity];
        if (search) url += `?search=${encodeURIComponent(search)}`;
      }

      const response = await fetch(url, { signal });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      data = await response.json();

      if (requestId !== lastDataRequestId) {
        return;
      }
      const fragment = document.createDocumentFragment();
      data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = createTableRow(row, entity);
        tr.dataset.id = getRowId(row, entity);
        fragment.appendChild(tr);
      });
      tbody.appendChild(fragment);
      applyCurrentSort();

    } catch (error) {
      if (error.name === 'AbortError') {
        return;
      }
      console.error('Error loading data:', error);
      showError('Ошибка загрузки данных: ' + error.message);
    } finally {
      currentDataAbortController = null;
    }
  }

  function onHeaderClick(e) {
    const th = e.currentTarget;
    const index = parseInt(th.dataset.index, 10);
    const current = sortStateByEntity[currentEntity];
    if (!current || current.index !== index) {
      sortStateByEntity[currentEntity] = { index, dir: 'asc' };
    } else {
      sortStateByEntity[currentEntity].dir = current.dir === 'asc' ? 'desc' : 'asc';
    }
    applyCurrentSort();
    updateHeaderIndicators();
  }

  function updateHeaderIndicators() {
    const state = sortStateByEntity[currentEntity];
    Array.from(thead.children).forEach(th => {
      const ind = th.querySelector('.sort-ind');
      if (!ind) return;
      ind.textContent = '';
    });
    if (state) {
      const th = thead.querySelector(`th[data-index="${state.index}"]`);
      if (th) {
        const ind = th.querySelector('.sort-ind');
        if (ind) ind.textContent = state.dir === 'asc' ? '▲' : '▼';
      }
    }
  }

  function applyCurrentSort() {
    const state = sortStateByEntity[currentEntity];
    if (!state) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const idx = state.index;
    const sorted = sortRows(rows, row => (row.cells[idx] ? row.cells[idx].textContent : ''), state.dir);
    reattachRows(tbody, sorted);
  }

  function createTableRow(row, entity) {
    return renderRow(entity, row);
  }

  function getRowId(row, entity) {
    const getter = idGetters[entity];
    return getter ? getter(row) : null;
  }

  function onRowClick(e) {
    const row = e.target.closest('tr');
    if (!row) return;
    tbody.querySelectorAll('tr').forEach(r => r.classList.remove('table-active'));
    row.classList.add('table-active');
    selectedId = row.dataset.id;
  }

  function onRowDoubleClick(e) {
    const row = e.target.closest('tr');
    if (!row) return;
    
    selectedId = row.dataset.id;
    fillFormFromRow(row);
  }

  function fillFormFromRow(row) {
    const cells = row.cells;
    
    if (currentEntity.startsWith('users_')) {
      fillUserForm(cells);
    } else if (currentEntity === 'disciplines') {
      sel('d_name').value = cells[1].textContent;
      sel('d_lessons').value = cells[2].textContent;
    } else if (currentEntity === 'groups') {
      sel('g_name').value = cells[0].textContent;
      sel('g_specialty').value = cells[1].textContent;
      sel('g_course').value = cells[2].textContent;
      sel('g_curator').value = cells[3].textContent;
    } else if (currentEntity === 'specialties') {
      sel('s_id').value = cells[0].textContent;
      sel('s_name').value = cells[1].textContent;
      sel('s_level').value = cells[2].textContent;
      sel('s_department').value = cells[3].textContent;
    } else if (currentEntity === 'exams') {
      sel('e_discipline').value = cells[1].textContent;
      sel('e_teacher').value = cells[2].textContent;
      sel('e_group').value = cells[3].textContent;
      sel('e_date').value = cells[4].textContent;
    } else if (currentEntity === 'departments') {
      sel('df_dep_name').value = cells[0].textContent;
      sel('df_dep_faculty').value = cells[1].textContent;
      sel('df_dep_head').value = cells[2].textContent;
      sel('df_dep_position').value = cells[3].textContent;
      sel('df_dep_email').value = cells[4].textContent;
      sel('df_dep_phone').value = cells[5].textContent;
    } else if (currentEntity === 'faculties') {
      sel('df_fac_name').value = cells[0].textContent;
      sel('df_fac_dean').value = cells[1].textContent;
      sel('df_fac_position').value = cells[2].textContent;
      sel('df_fac_email').value = cells[3].textContent;
      sel('df_fac_phone').value = cells[4].textContent;
    } else if (currentEntity === 'assign_teachers_disciplines') {
      sel('atd_teacher').value = cells[0].textContent;
      sel('atd_discipline').value = cells[1].textContent;
    } else if (currentEntity === 'assign_specialties_disciplines') {
      sel('asd_specialty').value = cells[0].textContent;
      sel('asd_discipline').value = cells[1].textContent;
    }
  }

  function fillUserForm(cells) {
    if (currentEntity === 'users_students') {
      sel('s_fio').value = cells[1].textContent;
      sel('s_login').value = cells[2].textContent;
      sel('s_password').value = PASSWORD_MASK;
      const genderValue = cells[3].textContent;
      if (genderValue) {
        document.querySelector(`input[name="s_gender"][value="${genderValue}"]`).checked = true;
      }
      sel('s_birth').value = cells[4].textContent;
      sel('s_phone').value = cells[5].textContent;
      sel('s_email').value = cells[6].textContent;
      sel('s_group').value = cells[7].textContent;
    } else if (currentEntity === 'users_teachers') {
      sel('t_fio').value = cells[1].textContent;
      sel('t_login').value = cells[2].textContent;
      sel('t_password').value = PASSWORD_MASK;
      const genderValue = cells[3].textContent;
      if (genderValue) {
        document.querySelector(`input[name="t_gender"][value="${genderValue}"]`).checked = true;
      }
      sel('t_birth').value = cells[4].textContent;
      sel('t_phone').value = cells[5].textContent;
      sel('t_email').value = cells[6].textContent;
      sel('t_position').value = cells[7].textContent;
      sel('t_department').value = cells[8].textContent;
    } else if (currentEntity === 'users_admins') {
      sel('a_fio').value = cells[1].textContent;
      sel('a_login').value = cells[2].textContent;
      sel('a_password').value = PASSWORD_MASK;
    }
  }

  async function loadAutoCompleteData(entity) {
    try {
      if (entity === 'users_teachers') {
        await loadDepartmentsInto('departments_teachers');
      } else if (entity === 'specialties') {
        await loadDepartmentsInto('departments_specialty');
      } else if (entity === 'departments') {
      }
      
      if (entity === 'users_students') {
        await loadGroupsInto('groups_students');
      } else if (entity === 'exams') {
        await loadGroupsInto('groups_exam');
      } else if (entity === 'groups') {
      }
      
      if (entity === 'groups') {
        await loadSpecialtiesInto('specialties', true);
      }
      
      if (entity === 'exams') {
        await loadDisciplinesInto('disciplines');
        await loadTeachersInto('teachers_exam');
      }
      
      if (entity === 'departments') {
        const response = await fetch('/api/faculties');
        if (response.ok) {
          const faculties = await response.json();
          const datalist = sel('faculties');
          if (datalist) {
            datalist.innerHTML = '';
            faculties.forEach(faculty => {
              const option = document.createElement('option');
              option.value = faculty['назв_факультет'];
              datalist.appendChild(option);
            });
          }
        }
      }
      
    if (entity === 'assign_teachers_disciplines') {
      await loadTeachersInto('teachers_assign');
    }

    if (entity === 'assign_teachers_disciplines') {
      await loadDisciplinesInto('disciplines_assign');
    } else if (entity === 'assign_specialties_disciplines') {
      await loadDisciplinesInto('disciplines_assign2');
    }

    if (entity === 'assign_specialties_disciplines') {
      await loadSpecialtiesInto('specialties_assign', false);
    }

    } catch (error) {
      console.error('Error loading autocomplete data:', error);
    }
  }

  async function loadDepartmentsInto(datalistId) {
    const response = await fetch('/api/departments_list');
    if (!response.ok) return;
    const departments = await response.json();
    const datalist = sel(datalistId);
    if (!datalist) return;
    datalist.innerHTML = '';
    departments.forEach(dept => {
      const option = document.createElement('option');
      option.value = dept['назв_каф'];
      datalist.appendChild(option);
    });
  }

  async function loadGroupsInto(datalistId) {
    const response = await fetch('/api/groups');
    if (!response.ok) return;
    const groups = await response.json();
    const datalist = sel(datalistId);
    if (!datalist) return;
    datalist.innerHTML = '';
    groups.forEach(group => {
      const option = document.createElement('option');
      option.value = group['название_группы'];
      datalist.appendChild(option);
    });
  }

  async function loadDisciplinesInto(datalistId) {
    const response = await fetch('/api/disciplines');
    if (!response.ok) return;
    const disciplines = await response.json();
    const datalist = sel(datalistId);
    if (!datalist) return;
    datalist.innerHTML = '';
    disciplines.forEach(disc => {
      const option = document.createElement('option');
      option.value = disc['название'];
      datalist.appendChild(option);
    });
  }

  async function loadTeachersInto(datalistId) {
    const teachersResponse = await fetch('/api/get_users?table=преподаватели&fioField=фио_преп');
    if (!teachersResponse.ok) return;
    const teachers = await teachersResponse.json();
    const datalist = sel(datalistId);
    if (!datalist) return;
    datalist.innerHTML = '';
    teachers.forEach(teacher => {
      const option = document.createElement('option');
      option.value = teacher['фио_преп'];
      datalist.appendChild(option);
    });
  }

  function onSearchChange() {
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      loadData(currentEntity, searchInput.value);
    }, 300);
  }

  function onSave() {
    if (requestInFlight) return;
    if (!validateForm()) return;
    submitEntity('POST')
      .then(() => { loadData(currentEntity); clearForm(); })
      .catch(err => showError('Ошибка сохранения: ' + err.message));
  }

  function onEdit() {
    if (requestInFlight) return;
    if (!selectedId) {
      showError('Выберите запись для редактирования');
      return;
    }
    
    if (!validateForm()) return;

    submitEntity('PUT')
      .then(() => { loadData(currentEntity); clearForm(); })
      .catch(err => showError('Ошибка обновления: ' + err.message));
  }

  function onDelete() {
    if (requestInFlight) return;
    if (!selectedId) {
      showError('Выберите запись для удаления');
      return;
    }
    
    showConfirm('Удалить запись?', () => {
      submitEntity('DELETE')
        .then(() => { showMessage('Запись удалена!'); loadData(currentEntity); clearForm(); })
        .catch(err => showError('Ошибка удаления: ' + err.message));
    });
  }

  function onReload() {
    if (requestInFlight) return;
    loadData(currentEntity);
    loadAutoCompleteData(currentEntity);
    clearForm();
  }

  function setBusy(isBusy) {
    requestInFlight = isBusy;
    const ids = ['btn_save', 'btn_edit', 'btn_delete', 'btn_reload', 'entitySelector', 'searchInput'];
    ids.forEach(id => {
      const el = sel(id);
      if (el) el.disabled = isBusy;
    });
  }

  async function apiFetch(url, method, payload, timeoutMs = 15000) {
    setBusy(true);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const resp = await fetch(url, {
        method,
        headers: window.withCsrfHeader({ 'Content-Type': 'application/json' }),
        body: payload ? JSON.stringify(payload) : undefined,
        signal: controller.signal
      });
      clearTimeout(timer);
      let data = {};
      try { data = await resp.json(); } catch (_) { /* ignore */ }
      if (!resp.ok) {
        const msg = data && data.error ? data.error : `HTTP ${resp.status}`;
        throw new Error(msg);
      }
      return data;
    } catch (e) {
      if (e.name === 'AbortError') throw new Error('Таймаут запроса. Попробуйте ещё раз.');
      throw e;
    } finally {
      setBusy(false);
    }
  }

  function submitEntity(verb) {
    const { url, payload } = buildRequest(verb);
    return apiFetch(url, verb, payload);
  }

  function buildRequest(method) {
    if (currentEntity.startsWith('users_')) {
      const tableMap = {
        'users_students': { table: 'студенты', idField: 'id_студ' },
        'users_teachers': { table: 'преподаватели', idField: 'id_преп' },
        'users_admins': { table: 'администраторы', idField: 'код_адм' }
      };
      const { table, idField } = tableMap[currentEntity];
      const data = getUserFormData();

      if (method === 'POST') {
        return {
          url: '/api/add_user',
          payload: { table, data }
        };
      }
      if (method === 'PUT') {
        return {
          url: '/api/update_user',
          payload: { table, idField, id: selectedId, data }
        };
      }
      if (method === 'DELETE') {
        return {
          url: '/api/delete_user',
          payload: { table, idField, id: selectedId }
        };
      }
    }

    const baseMap = {
      disciplines: '/api/disciplines',
      groups: '/api/groups',
      specialties: '/api/specialties',
    assign_teachers_disciplines: '/api/discipline-assignments',
    assign_specialties_disciplines: '/api/specialty-assignments',
      exams: '/api/exams',
      departments: '/api/departments',
      faculties: '/api/faculties'
    };
    const idPath = buildRestIdPath();
  let url;
  if (method === 'POST') {
    url = baseMap[currentEntity];
  } else {
    if ((currentEntity === 'assign_teachers_disciplines' || currentEntity === 'assign_specialties_disciplines')) {
      url = baseMap[currentEntity];
    } else {
      url = `${baseMap[currentEntity]}/${idPath}`;
    }
  }
    const payload = buildEntityPayload(method);
    return { url, payload };
  }

  function buildRestIdPath() {
  if (currentEntity === 'assign_teachers_disciplines' || currentEntity === 'assign_specialties_disciplines') {
    return '';
  }
  return encodeURIComponent(selectedId);
  }

  function buildEntityPayload(method) {
    const builder = payloadBuilders[currentEntity];
    return builder ? builder() : {};
  }

  function getUserFormData() {
    const stripMaskedPassword = (v) => {
      const value = (v || '').trim();
      if (!value || value === PASSWORD_MASK) return undefined;
      return value;
    };

    if (currentEntity === 'users_students') {
      const payload = {
        фио_студ: sel('s_fio').value,
        логин: sel('s_login').value,
        пол: document.querySelector('input[name="s_gender"]:checked').value,
        дата_рождения: sel('s_birth').value,
        телефон: sel('s_phone').value,
        почта: sel('s_email').value,
        название_группы: sel('s_group').value
      };
      const pwd = stripMaskedPassword(sel('s_password').value);
      if (pwd !== undefined) payload.пароль = pwd;
      return payload;
    } else if (currentEntity === 'users_teachers') {
      const payload = {
        фио_преп: sel('t_fio').value,
        логин: sel('t_login').value,
        пол: document.querySelector('input[name="t_gender"]:checked').value,
        дата_рождения: sel('t_birth').value,
        телефон: sel('t_phone').value,
        почта: sel('t_email').value,
        должность: sel('t_position').value,
        кафедра: sel('t_department').value
      };
      const pwd = stripMaskedPassword(sel('t_password').value);
      if (pwd !== undefined) payload.пароль = pwd;
      return payload;
    } else if (currentEntity === 'users_admins') {
      const payload = {
        фио_адм: sel('a_fio').value,
        логин: sel('a_login').value,
      };
      const pwd = stripMaskedPassword(sel('a_password').value);
      if (pwd !== undefined) payload.пароль = pwd;
      return payload;
    }
    return {};
  }

  function validateForm() {
    return validateAdminManageForm(currentEntity, forms, sel, showError);
  }

  function clearForm() {
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
      if (input.id === 'entitySelector') return;
      
      if (input.type === 'radio') {
        input.checked = false;
      } else {
        input.value = '';
      }
      input.classList.remove('is-invalid', 'is-valid');
    });
    
    const maleRadios = [sel('s_male'), sel('t_male')];
    maleRadios.forEach(radio => {
      if (radio) radio.checked = true;
    });
    selectedId = null;
    tbody.querySelectorAll('tr').forEach(r => r.classList.remove('table-active'));
  }

  function formatPhoneInput(e) {
    let value = e.target.value;
    value = value.replace(/\D/g, '');
    if (value.length > 11) {
      value = value.slice(0, 11);
    }
    e.target.value = value;
  }

  function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toISOString().split('T')[0];
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();