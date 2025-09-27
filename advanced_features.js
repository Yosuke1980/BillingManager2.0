/**
 * 高度な検索・フィルタリング機能とUI拡張
 */

// グローバル変数
let currentData = {
    payments: [],
    expenses: [],
    masters: []
};
let currentFilters = {};
let sortConfig = { key: null, direction: 'asc' };
let currentPage = 1;
let itemsPerPage = 50;

/**
 * 高度なフィルタリング機能
 */
function applyAdvancedFilters(data, filters, dataType) {
    return data.filter(item => {
        // テキスト検索
        if (filters.search) {
            const searchTerm = filters.search.toLowerCase();
            const searchFields = getSearchFields(dataType);
            const matches = searchFields.some(field => {
                const value = item[field];
                return value && value.toString().toLowerCase().includes(searchTerm);
            });
            if (!matches) return false;
        }
        
        // 状態フィルター
        if (filters.status && item.status !== filters.status) {
            return false;
        }
        
        // 金額範囲フィルター
        if (filters.amountMin && item.amount < parseFloat(filters.amountMin)) {
            return false;
        }
        if (filters.amountMax && item.amount > parseFloat(filters.amountMax)) {
            return false;
        }
        
        // 日付範囲フィルター
        if (filters.dateFrom || filters.dateTo) {
            const itemDate = new Date(item.paymentDate || item.payment_date);
            if (filters.dateFrom && itemDate < new Date(filters.dateFrom)) {
                return false;
            }
            if (filters.dateTo && itemDate > new Date(filters.dateTo)) {
                return false;
            }
        }
        
        // 緊急度フィルター
        if (filters.urgency && item.urgencyLevel !== filters.urgency) {
            return false;
        }
        
        // 案件状態フィルター
        if (filters.projectStatus && item.projectStatus !== filters.projectStatus) {
            return false;
        }
        
        // 部署フィルター
        if (filters.department) {
            const dept = filters.department.toLowerCase();
            if (!item.department || !item.department.toLowerCase().includes(dept)) {
                return false;
            }
        }
        
        return true;
    });
}

/**
 * 検索対象フィールドを取得
 */
function getSearchFields(dataType) {
    const fieldMaps = {
        payments: ['subject', 'projectName', 'payee', 'payeeCode', 'project_name', 'payee_code'],
        expenses: ['projectName', 'payee', 'payeeCode', 'project_name', 'payee_code'],
        masters: ['projectName', 'payee', 'payeeCode', 'project_name', 'payee_code']
    };
    return fieldMaps[dataType] || [];
}

/**
 * ソート機能
 */
function sortData(data, key, direction = 'asc') {
    return [...data].sort((a, b) => {
        let aVal = a[key];
        let bVal = b[key];
        
        // 数値の場合
        if (!isNaN(aVal) && !isNaN(bVal)) {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
        } else {
            // 文字列の場合
            aVal = (aVal || '').toString().toLowerCase();
            bVal = (bVal || '').toString().toLowerCase();
        }
        
        if (direction === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });
}

/**
 * ページネーション
 */
function paginateData(data, page, itemsPerPage) {
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return {
        data: data.slice(startIndex, endIndex),
        totalPages: Math.ceil(data.length / itemsPerPage),
        totalItems: data.length,
        currentPage: page
    };
}

/**
 * テーブルヘッダーにソート機能を追加
 */
function addSortableHeaders(tableId, dataType) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.classList.add('sortable');
        header.addEventListener('click', () => {
            const sortKey = header.getAttribute('data-sort');
            
            // ソート方向の決定
            let direction = 'asc';
            if (sortConfig.key === sortKey && sortConfig.direction === 'asc') {
                direction = 'desc';
            }
            
            sortConfig = { key: sortKey, direction };
            
            // ヘッダーのスタイル更新
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            header.classList.add(`sort-${direction}`);
            
            // データを再表示
            refreshCurrentTable(dataType);
        });
    });
}

/**
 * 現在のテーブルを更新
 */
function refreshCurrentTable(dataType) {
    const data = currentData[dataType];
    if (!data) return;
    
    let filteredData = applyAdvancedFilters(data, currentFilters, dataType);
    
    if (sortConfig.key) {
        filteredData = sortData(filteredData, sortConfig.key, sortConfig.direction);
    }
    
    const paginatedResult = paginateData(filteredData, currentPage, itemsPerPage);
    
    // テーブル更新
    renderTable(dataType, paginatedResult.data);
    
    // ページネーション更新
    renderPagination(paginatedResult, dataType);
    
    // カウント更新
    updateDataCount(dataType, paginatedResult.totalItems, data.length);
}

/**
 * ページネーション表示
 */
function renderPagination(paginatedResult, dataType) {
    const container = document.getElementById(`${dataType}Pagination`);
    if (!container) return;
    
    const { currentPage, totalPages, totalItems } = paginatedResult;
    
    let paginationHtml = '<div class="pagination">';
    
    // 前へボタン
    paginationHtml += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1}, '${dataType}')">
        <i class="bi bi-chevron-left"></i>
    </button>`;
    
    // ページ番号
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHtml += `<button onclick="goToPage(1, '${dataType}')">1</button>`;
        if (startPage > 2) {
            paginationHtml += '<span>...</span>';
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `<button ${i === currentPage ? 'class="active"' : ''} onclick="goToPage(${i}, '${dataType}')">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += '<span>...</span>';
        }
        paginationHtml += `<button onclick="goToPage(${totalPages}, '${dataType}')">${totalPages}</button>`;
    }
    
    // 次へボタン
    paginationHtml += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1}, '${dataType}')">
        <i class="bi bi-chevron-right"></i>
    </button>`;
    
    paginationHtml += '</div>';
    paginationHtml += `<div class="text-center mt-2"><small class="text-muted">${totalItems}件中 ${((currentPage - 1) * itemsPerPage) + 1}-${Math.min(currentPage * itemsPerPage, totalItems)}件を表示</small></div>`;
    
    container.innerHTML = paginationHtml;
}

/**
 * ページ移動
 */
function goToPage(page, dataType) {
    currentPage = page;
    refreshCurrentTable(dataType);
}

/**
 * データ件数表示の更新
 */
function updateDataCount(dataType, filteredCount, totalCount) {
    const countElement = document.getElementById(`${dataType}Count`);
    if (countElement) {
        if (filteredCount === totalCount) {
            countElement.textContent = `${totalCount}件のデータ`;
        } else {
            countElement.textContent = `${filteredCount}件 (全${totalCount}件中)`;
        }
    }
}

/**
 * 詳細検索フィールドの表示/非表示切り替え
 */
function toggleAdvancedSearch() {
    const advancedFields = document.getElementById('advancedSearchFields');
    const toggleButton = document.getElementById('advancedToggle');
    
    if (advancedFields.style.display === 'none') {
        advancedFields.style.display = 'block';
        toggleButton.innerHTML = '<i class="bi bi-chevron-up"></i> 詳細';
    } else {
        advancedFields.style.display = 'none';
        toggleButton.innerHTML = '<i class="bi bi-chevron-down"></i> 詳細';
    }
}

/**
 * フィルターのリセット
 */
function resetPaymentFilters() {
    // フィルター入力欄をクリア
    document.getElementById('paymentSearch').value = '';
    document.getElementById('paymentStatusFilter').value = '';
    document.getElementById('paymentMonthFilter').value = '';
    
    // 詳細検索フィールドもクリア
    const advancedFields = ['amountMin', 'amountMax', 'paymentDateFrom', 'paymentDateTo', 'urgencyFilter', 'projectStatusFilter', 'departmentFilter'];
    advancedFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) field.value = '';
    });
    
    // フィルター設定をリセット
    currentFilters = {};
    sortConfig = { key: null, direction: 'asc' };
    currentPage = 1;
    
    // テーブルを更新
    refreshCurrentTable('payments');
}

/**
 * フィルター適用
 */
function searchPayments() {
    // フィルター設定を収集
    currentFilters = {
        search: document.getElementById('paymentSearch').value,
        status: document.getElementById('paymentStatusFilter').value,
        month: document.getElementById('paymentMonthFilter').value,
        amountMin: document.getElementById('amountMin')?.value,
        amountMax: document.getElementById('amountMax')?.value,
        dateFrom: document.getElementById('paymentDateFrom')?.value,
        dateTo: document.getElementById('paymentDateTo')?.value,
        urgency: document.getElementById('urgencyFilter')?.value,
        projectStatus: document.getElementById('projectStatusFilter')?.value,
        department: document.getElementById('departmentFilter')?.value
    };
    
    // 空の値を除去
    Object.keys(currentFilters).forEach(key => {
        if (!currentFilters[key]) {
            delete currentFilters[key];
        }
    });
    
    currentPage = 1;
    refreshCurrentTable('payments');
}

/**
 * 照合機能
 */
async function runAutoMatching() {
    try {
        showLoadingModal('照合処理を実行中...');
        
        const response = await google.script.run
            .withSuccessHandler(handleMatchingResult)
            .withFailureHandler(handleError)
            .matchExpensesWithPayments();
            
    } catch (error) {
        handleError(error);
    }
}

function handleMatchingResult(result) {
    hideLoadingModal();
    
    if (result.success) {
        const resultsHtml = `
            <div class="alert alert-success">
                <h6>照合が完了しました</h6>
                <ul>
                    <li>照合済み: ${result.matchedCount}件</li>
                    <li>未照合: ${result.notMatchedCount}件</li>
                </ul>
            </div>
        `;
        
        document.getElementById('matchingResults').innerHTML = resultsHtml;
        
        // データを再読み込み
        refreshAllData();
        
        showAlert('照合処理が完了しました', 'success');
    } else {
        showAlert('照合処理中にエラーが発生しました: ' + result.message, 'danger');
    }
}

/**
 * CSV出力機能
 */
async function exportPaymentsCsv() {
    try {
        showLoadingModal('CSV出力中...');
        
        const response = await google.script.run
            .withSuccessHandler(handleCsvExport)
            .withFailureHandler(handleError)
            .exportPaymentsCsv();
            
    } catch (error) {
        handleError(error);
    }
}

function handleCsvExport(base64Data) {
    hideLoadingModal();
    
    // Base64データをBlobに変換してダウンロード
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'text/csv;charset=utf-8;' });
    
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `支払いデータ_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showAlert('CSVファイルをダウンロードしました', 'success');
}

/**
 * データ移行関連機能
 */
function openDataMigrationModal() {
    const modal = new bootstrap.Modal(document.getElementById('dataMigrationModal'));
    modal.show();
}

async function executeMigration() {
    const files = {
        payments: document.getElementById('paymentsImport').files[0],
        expenses: document.getElementById('expensesImport').files[0],
        masters: document.getElementById('mastersImport').files[0]
    };
    
    const migrationData = {};
    
    // ファイルを読み込み
    for (const [type, file] of Object.entries(files)) {
        if (file) {
            try {
                const csvData = await readFileAsText(file);
                migrationData[type] = { csvData };
            } catch (error) {
                showAlert(`${type}ファイルの読み込みに失敗しました: ${error.message}`, 'danger');
                return;
            }
        }
    }
    
    if (Object.keys(migrationData).length === 0) {
        showAlert('移行するファイルを選択してください', 'warning');
        return;
    }
    
    try {
        showProgressModal('データ移行を実行中...');
        
        const response = await google.script.run
            .withSuccessHandler(handleMigrationResult)
            .withFailureHandler(handleError)
            .executeBulkMigration(migrationData);
            
    } catch (error) {
        handleError(error);
    }
}

function handleMigrationResult(result) {
    hideProgressModal();
    
    if (result.success) {
        const resultsHtml = `
            <div class="alert alert-success">
                <h6>データ移行が完了しました</h6>
                <p>合計 ${result.results.totalImported}件のデータを移行しました</p>
                ${result.results.migrations.map(m => `
                    <div class="mb-2">
                        <strong>${m.dataType}:</strong> ${m.count}件 
                        ${m.errorCount > 0 ? `(エラー: ${m.errorCount}件)` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        document.getElementById('migrationResults').innerHTML = resultsHtml;
        showAlert('データ移行が完了しました', 'success');
        
        // データを再読み込み
        refreshAllData();
    } else {
        showAlert('データ移行中にエラーが発生しました: ' + result.message, 'danger');
    }
}

/**
 * ユーティリティ関数
 */
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = e => reject(e);
        reader.readAsText(file, 'UTF-8');
    });
}

function showLoadingModal(message) {
    document.getElementById('loadingMessage').textContent = message;
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
}

function hideLoadingModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (modal) {
        modal.hide();
    }
}

function showProgressModal(message) {
    document.getElementById('progressMessage').textContent = message;
    const modal = new bootstrap.Modal(document.getElementById('progressModal'));
    modal.show();
}

function hideProgressModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
    if (modal) {
        modal.hide();
    }
}

function showAlert(message, type = 'info') {
    // Bootstrap Alertを動的に作成
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show position-fixed" style="top: 20px; right: 20px; z-index: 9999;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHtml;
    document.body.appendChild(alertElement.firstElementChild);
    
    // 5秒後に自動削除
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function handleError(error) {
    hideLoadingModal();
    hideProgressModal();
    console.error('Error:', error);
    showAlert('エラーが発生しました: ' + error.toString(), 'danger');
}

async function refreshAllData() {
    try {
        // 全データを再読み込み
        const [payments, expenses, masters] = await Promise.all([
            google.script.run.withSuccessHandler(data => data).getPaymentData(),
            google.script.run.withSuccessHandler(data => data).getExpenseData(),
            google.script.run.withSuccessHandler(data => data).getMasterData()
        ]);
        
        currentData.payments = payments.data || [];
        currentData.expenses = expenses.data || [];
        currentData.masters = masters.data || [];
        
        // 現在のタブを更新
        const activeTab = document.querySelector('.nav-link.active').id;
        if (activeTab === 'payment-tab') {
            refreshCurrentTable('payments');
        } else if (activeTab === 'expense-tab') {
            refreshCurrentTable('expenses');
        } else if (activeTab === 'master-tab') {
            refreshCurrentTable('masters');
        }
        
    } catch (error) {
        handleError(error);
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    // ソートヘッダーを設定
    addSortableHeaders('paymentsTable', 'payments');
    addSortableHeaders('expensesTable', 'expenses');
    addSortableHeaders('mastersTable', 'masters');
    
    // データを初期読み込み
    refreshAllData();
});