/**
 * Общая функция экспорта таблицы в Excel
 * @param {Array<Array>} data - Двумерный массив данных
 * @param {string} filename - Имя файла для скачивания
 * @param {string} sheetName - Имя листа в Excel (по умолчанию 'Sheet')
 * @param {Array} columnWidths - Опциональный массив ширин колонок
 */
function exportTableToExcel(data, filename, sheetName = 'Sheet', columnWidths = null) {
    console.log('exportTableToExcel function started');
    
    if (!data || data.length === 0) {
        alert('Нет данных для экспорта');
        console.error('No data to export');
        return;
    }

    console.log('Data prepared:', data);
    console.log('XLSX object:', typeof XLSX);

    try {
        // Create workbook
        const ws = XLSX.utils.aoa_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, sheetName);

        // Set column widths if provided
        if (columnWidths && columnWidths.length > 0) {
            ws['!cols'] = columnWidths;
        }

        console.log('Writing file:', filename);
        // Download
        XLSX.writeFile(wb, filename);
        console.log('File written successfully');
    } catch (error) {
        console.error('Export error:', error);
        alert('Ошибка при экспорте: ' + error.message);
    }
}

/**
 * Извлечение данных из таблицы HTML
 * @param {HTMLTableElement} table - Таблица для экспорта
 * @param {Object} options - Опции экспорта
 *   - skipColumns: Array of column indices to skip
 *   - includeHeaders: boolean (default true)
 * @returns {Array<Array>} Двумерный массив данных
 */
function extractTableData(table, options = {}) {
    const {
        skipColumns = [],
        includeHeaders = true
    } = options;

    const data = [];
    
    // Extract headers if needed
    if (includeHeaders) {
        const thead = table.querySelector('thead tr');
        if (thead) {
            const headers = [];
            thead.querySelectorAll('th').forEach((th, idx) => {
                if (!skipColumns.includes(idx)) {
                    headers.push(th.textContent.trim());
                }
            });
            if (headers.length > 0) {
                data.push(headers);
            }
        }
    }

    // Extract rows
    const tbody = table.querySelector('tbody');
    if (tbody) {
        tbody.querySelectorAll('tr').forEach(row => {
            const rowData = [];
            row.querySelectorAll('td').forEach((td, idx) => {
                if (!skipColumns.includes(idx)) {
                    const input = td.querySelector('input');
                    if (input) {
                        rowData.push(input.value || '');
                    } else {
                        rowData.push(td.textContent.trim());
                    }
                }
            });
            if (rowData.length > 0) {
                data.push(rowData);
            }
        });
    }

    return data;
}
