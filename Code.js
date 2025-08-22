//Code.gsの修正版 - データ表示を統一

/**
 * ラジオ局支払い・費用管理システム - メインファイル
 * Google Apps Script版
 */

// スプレッドシートID（実際のスプレッドシートIDに変更してください）
const SPREADSHEET_ID = '18lmdCjSM8Sf_GUXdJOet1R198OX7NMJAb0QU1hgbsDQ';

// シート名定数
const SHEET_NAMES = {
  PAYMENTS: '支払いデータ',
  EXPENSES: '費用データ',
  EXPENSE_MASTER: '費用マスター',
  CONFIG: '設定'
};

/**
 * Webアプリのメインページを返す
 */
function doGet() {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .setTitle('ラジオ局支払い・費用管理システム');
}

/**
 * HTMLファイルをインクルードする関数
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * スプレッドシートの参照を取得
 */
function getSpreadsheet() {
  try {
    return SpreadsheetApp.openById(SPREADSHEET_ID);
  } catch (error) {
    console.error('スプレッドシートの取得に失敗:', error);
    throw new Error('スプレッドシートにアクセスできません。IDを確認してください。');
  }
}

/**
 * 指定されたシートを取得または作成
 */
function getOrCreateSheet(sheetName, headers = []) {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    if (headers.length > 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    }
  }
  
  return sheet;
}

/**
 * 初期化処理
 */
function initializeSheets() {
  try {
    // 支払いデータシート
    getOrCreateSheet(SHEET_NAMES.PAYMENTS, [
      'ID', '件名', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日時'
    ]);
    
    // 費用データシート
    getOrCreateSheet(SHEET_NAMES.EXPENSES, [
      'ID', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日時'
    ]);
    
    // 費用マスターシート
    getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER, [
      'ID', '案件名', '支払い先', '支払い先コード', '金額', '種別', '開始日', '終了日', '放送曜日', '作成日時'
    ]);
    
    // 設定シート
    getOrCreateSheet(SHEET_NAMES.CONFIG, [
      'キー', '値', '説明'
    ]);
    
    return { success: true, message: 'シートの初期化が完了しました' };
  } catch (error) {
    console.error('初期化エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 統一版 支払いデータ取得関数
 */
function getPaymentData(searchTerm = '') {
  try {
    console.log('=== 統一版 支払いデータ取得開始 ===');
    console.log('検索条件:', searchTerm);
    
    const sheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS, [
      'ID', '件名', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日時'
    ]);
    
    const lastRow = sheet.getLastRow();
    console.log('最終行数:', lastRow);
    
    if (lastRow <= 1) {
      console.log('データが存在しません（ヘッダーのみ）');
      return { 
        data: [], 
        matchedCount: 0,
        totalRows: 0,
        filteredRows: 0,
        success: true
      };
    }
    
    // データ範囲を取得
    const dataRange = sheet.getRange(2, 1, lastRow - 1, 9);
    const data = dataRange.getValues();
    console.log('取得した生データ行数:', data.length);
    
    // 空行を除外し、データを検証
    let filteredData = data.filter((row, index) => {
      const hasData = row.some(cell => cell !== null && cell !== undefined && cell !== '');
      if (!hasData) {
        console.log(`行 ${index + 2}: 空行をスキップ`);
      }
      return hasData;
    });
    
    console.log('空行除外後の行数:', filteredData.length);
    
    // 検索フィルター適用
    if (searchTerm && searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      const beforeFilterCount = filteredData.length;
      filteredData = filteredData.filter(row => 
        row.some(cell => {
          if (cell === null || cell === undefined) return false;
          return cell.toString().toLowerCase().includes(term);
        })
      );
      console.log(`検索フィルター適用: ${beforeFilterCount} → ${filteredData.length} 行`);
    }
    
    // 照合済み件数を計算
    const matchedCount = filteredData.filter(row => {
      const status = row[7];
      return status === '照合済' || status === '処理済';
    }).length;
    console.log('照合済み件数:', matchedCount);
    
    // データを整形（マスター費用と同じ方式で）
    const formattedData = filteredData.map((row, index) => {
      try {
        return {
          id: row[0] || generateId(),
          subject: convertToSafeString(row[1]),
          projectName: convertToSafeString(row[2]),
          payee: convertToSafeString(row[3]),
          payeeCode: convertToSafeString(row[4]),
          amount: convertToSafeNumber(row[5]),
          paymentDate: convertToDateString(row[6]),
          status: convertToSafeString(row[7]) || '未処理',
          createdAt: convertToDateString(row[8])
        };
      } catch (formatError) {
        console.error(`支払いデータ行 ${index + 2} のフォーマット中にエラー:`, formatError);
        
        // エラー時のフォールバック
        return {
          id: row[0] || `payment_error_${index}`,
          subject: `エラー件名${index}`,
          projectName: `エラー案件${index}`,
          payee: 'エラー',
          payeeCode: '',
          amount: 0,
          paymentDate: '',
          status: '未処理',
          createdAt: ''
        };
      }
    });
    
    console.log('最終的なフォーマット済み支払いデータ行数:', formattedData.length);
    
    if (formattedData.length > 0) {
      console.log('サンプルフォーマット済み支払いデータ:', formattedData[0]);
    }
    
    console.log('=== 統一版 支払いデータ取得完了 ===');
    
    return { 
      data: formattedData, 
      matchedCount: matchedCount,
      totalRows: lastRow - 1,
      filteredRows: formattedData.length,
      success: true,
      message: `${formattedData.length}件のデータを取得しました`
    };
    
  } catch (error) {
    console.error('支払いデータ取得全体エラー:', error);
    console.error('エラースタック:', error.stack);
    
    return {
      data: [],
      matchedCount: 0,
      totalRows: 0,
      filteredRows: 0,
      success: false,
      error: error.toString(),
      message: `支払いデータの取得に失敗しました: ${error.toString()}`
    };
  }
}

/**
 * 統一版 費用データ取得関数
 */
function getExpenseData(searchTerm = '', filterMonth = '') {
  try {
    console.log('=== 統一版 費用データ取得開始 ===');
    console.log('検索条件:', searchTerm, '月フィルター:', filterMonth);
    
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSES, [
      'ID', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日時'
    ]);
    
    const lastRow = sheet.getLastRow();
    console.log('最終行数:', lastRow);
    
    if (lastRow <= 1) {
      console.log('データが存在しません（ヘッダーのみ）');
      return { 
        data: [], 
        matchedCount: 0,
        totalRows: 0,
        filteredRows: 0,
        success: true
      };
    }
    
    // データ範囲を取得
    const dataRange = sheet.getRange(2, 1, lastRow - 1, 8);
    const data = dataRange.getValues();
    console.log('取得した生データ行数:', data.length);
    
    // 空行を除外
    let filteredData = data.filter((row, index) => {
      const hasData = row.some(cell => cell !== null && cell !== undefined && cell !== '');
      if (!hasData) {
        console.log(`行 ${index + 2}: 空行をスキップ`);
      }
      return hasData;
    });
    
    console.log('空行除外後の行数:', filteredData.length);
    
    // 検索フィルター適用
    if (searchTerm && searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      const beforeFilterCount = filteredData.length;
      filteredData = filteredData.filter(row => 
        row.some(cell => {
          if (cell === null || cell === undefined) return false;
          return cell.toString().toLowerCase().includes(term);
        })
      );
      console.log(`検索フィルター適用: ${beforeFilterCount} → ${filteredData.length} 行`);
    }
    
    // 月フィルター適用
    if (filterMonth && filterMonth.trim() !== '') {
      const beforeFilterCount = filteredData.length;
      filteredData = filteredData.filter(row => {
        try {
          const paymentDate = row[5];
          if (!paymentDate) return false;
          
          const dateStr = convertToDateString(paymentDate);
          return dateStr.includes(filterMonth);
        } catch (dateError) {
          console.error('日付フィルターエラー:', dateError);
          return false;
        }
      });
      console.log(`月フィルター適用: ${beforeFilterCount} → ${filteredData.length} 行`);
    }
    
    // 照合済み件数を計算
    const matchedCount = filteredData.filter(row => {
      const status = row[6];
      return status === '照合済';
    }).length;
    
    // データを整形（統一された方式で）
    const formattedData = filteredData.map((row, index) => {
      try {
        return {
          id: row[0] || generateId(),
          projectName: convertToSafeString(row[1]),
          payee: convertToSafeString(row[2]),
          payeeCode: convertToSafeString(row[3]),
          amount: convertToSafeNumber(row[4]),
          paymentDate: convertToDateString(row[5]),
          status: convertToSafeString(row[6]) || '未処理',
          createdAt: convertToDateString(row[7])
        };
      } catch (formatError) {
        console.error(`費用データ行 ${index + 2} のフォーマット中にエラー:`, formatError);
        
        // エラー時のフォールバック
        return {
          id: row[0] || `expense_error_${index}`,
          projectName: `エラー行${index}`,
          payee: 'エラー',
          payeeCode: '',
          amount: 0,
          paymentDate: '',
          status: '未処理',
          createdAt: ''
        };
      }
    });
    
    console.log('最終的なフォーマット済み費用データ行数:', formattedData.length);
    
    if (formattedData.length > 0) {
      console.log('サンプルフォーマット済み費用データ:', formattedData[0]);
    }
    
    console.log('=== 統一版 費用データ取得完了 ===');
    
    return { 
      data: formattedData, 
      matchedCount: matchedCount,
      totalRows: lastRow - 1,
      filteredRows: formattedData.length,
      success: true,
      message: `${formattedData.length}件のデータを取得しました`
    };
    
  } catch (error) {
    console.error('費用データ取得全体エラー:', error);
    console.error('エラースタック:', error.stack);
    
    return {
      data: [],
      matchedCount: 0,
      totalRows: 0,
      filteredRows: 0,
      success: false,
      error: error.toString(),
      message: `費用データの取得に失敗しました: ${error.toString()}`
    };
  }
}

/**
 * 既に修正済みの費用マスターデータ取得関数（参考用）
 */
function getMasterData(searchTerm = '') {
  try {
    console.log('=== 統一版 費用マスターデータ取得開始 ===');
    console.log('検索条件:', searchTerm);
    
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER, [
      'ID', '案件名', '支払い先', '支払い先コード', '金額', '種別', '開始日', '終了日', '放送曜日', '作成日時'
    ]);
    
    const lastRow = sheet.getLastRow();
    console.log('最終行数:', lastRow);
    
    if (lastRow <= 1) {
      console.log('データが存在しません（ヘッダーのみ）');
      return { 
        data: [],
        totalRows: 0,
        filteredRows: 0,
        success: true
      };
    }
    
    // データ範囲を取得
    const dataRange = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn());
    const data = dataRange.getValues();
    console.log('取得した生データ行数:', data.length);
    
    // 空行を除外
    let filteredData = data.filter((row, index) => {
      const hasData = row.some(cell => cell !== null && cell !== undefined && cell !== '');
      return hasData;
    });
    
    console.log('空行除外後の行数:', filteredData.length);
    
    // 検索フィルター適用
    if (searchTerm && searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      const beforeFilterCount = filteredData.length;
      filteredData = filteredData.filter(row => 
        row.some(cell => {
          if (cell === null || cell === undefined) return false;
          return cell.toString().toLowerCase().includes(term);
        })
      );
      console.log(`検索フィルター適用: ${beforeFilterCount} → ${filteredData.length} 行`);
    }
    
    // データを整形（統一された方式で）
    const formattedData = filteredData.map((row, index) => {
      try {
        return {
          id: row[0] || generateId(),
          projectName: convertToSafeString(row[1]),
          payee: convertToSafeString(row[2]),
          payeeCode: convertToSafeString(row[3]),
          amount: convertToSafeNumber(row[4]),
          paymentType: convertToSafeString(row[5]) || '月額固定',
          startDate: convertToDateString(row[6]),
          endDate: convertToDateString(row[7]),
          broadcastDays: convertToSafeString(row[8]),
          createdAt: convertToDateString(row[9])
        };
      } catch (formatError) {
        console.error(`費用マスター行 ${index + 2} のフォーマット中にエラー:`, formatError);
        
        // エラー時のフォールバック
        return {
          id: row[0] || `master_error_${index}`,
          projectName: `エラー行${index}`,
          payee: 'エラー',
          payeeCode: '',
          amount: 0,
          paymentType: '月額固定',
          startDate: '',
          endDate: '',
          broadcastDays: '',
          createdAt: ''
        };
      }
    });
    
    console.log('最終的なフォーマット済み費用マスターデータ行数:', formattedData.length);
    
    if (formattedData.length > 0) {
      console.log('サンプルフォーマット済みデータ:', formattedData[0]);
    }
    
    console.log('=== 統一版 費用マスターデータ取得完了 ===');
    
    return { 
      data: formattedData,
      totalRows: lastRow - 1,
      filteredRows: formattedData.length,
      success: true,
      message: `${formattedData.length}件のデータを取得しました`
    };
    
  } catch (error) {
    console.error('費用マスターデータ取得全体エラー:', error);
    console.error('エラースタック:', error.stack);
    
    return {
      data: [],
      totalRows: 0,
      filteredRows: 0,
      success: false,
      error: error.toString(),
      message: `データ取得エラー: ${error.toString()}`
    };
  }
}

// === 共通ヘルパー関数（統一された処理） ===

/**
 * 文字列を安全に変換する関数
 */
function convertToSafeString(value) {
  try {
    if (value === null || value === undefined) return '';
    
    const str = value.toString().trim();
    
    // 特殊な空白文字を除去
    return str.replace(/[\u00A0\u2000-\u200B\u2028\u2029]/g, ' ').trim();
  } catch (error) {
    console.error('文字列変換エラー:', error, 'for value:', value);
    return '';
  }
}

/**
 * 数値を安全に変換する関数
 */
function convertToSafeNumber(value) {
  try {
    if (value === null || value === undefined || value === '') return 0;
    
    // 既に数値の場合
    if (typeof value === 'number') {
      return isNaN(value) ? 0 : value;
    }
    
    // 文字列から数値を抽出
    const str = value.toString().replace(/[^\d.-]/g, '');
    const num = parseFloat(str);
    
    return isNaN(num) ? 0 : num;
  } catch (error) {
    console.error('数値変換エラー:', error, 'for value:', value);
    return 0;
  }
}

/**
 * 日付を安全に文字列に変換する関数（既存のものを維持）
 */
function convertToDateString(dateValue) {
  try {
    // 既に文字列の場合
    if (typeof dateValue === 'string') {
      if (dateValue.trim() === '') return '';
      // 日付として有効かチェック
      const testDate = new Date(dateValue);
      if (isNaN(testDate.getTime())) {
        return dateValue; // 日付でない場合はそのまま返す
      }
      return dateValue;
    }
    
    // Dateオブジェクトの場合
    if (dateValue instanceof Date) {
      if (isNaN(dateValue.getTime())) return '';
      
      // YYYY-MM-DD形式で返す
      const year = dateValue.getFullYear();
      const month = (dateValue.getMonth() + 1).toString().padStart(2, '0');
      const day = dateValue.getDate().toString().padStart(2, '0');
      
      return `${year}-${month}-${day}`;
    }
    
    // 数値の場合（シリアル値など）
    if (typeof dateValue === 'number') {
      try {
        const date = new Date(dateValue);
        if (isNaN(date.getTime())) return '';
        
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        
        return `${year}-${month}-${day}`;
      } catch (numError) {
        return '';
      }
    }
    
    // null、undefined、その他
    if (dateValue === null || dateValue === undefined) {
      return '';
    }
    
    // 最後の手段：文字列変換を試行
    try {
      const str = dateValue.toString();
      if (str === 'null' || str === 'undefined' || str === '') {
        return '';
      }
      return str;
    } catch (strError) {
      return '';
    }
    
  } catch (error) {
    console.error('日付変換エラー:', error, 'for value:', dateValue);
    return '';
  }
}

/**
 * 同様に改善された formatDateForDisplay 関数
 */
function formatDateForDisplay(dateValue) {
  return convertToDateString(dateValue);
}

// === 以下、既存の関数群（修正なし） ===

/**
 * 費用データを保存
 */
function saveExpense(expenseData, isNew = false) {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const now = new Date();
    
    if (isNew) {
      // 新規作成
      const newId = generateId();
      const newRow = [
        newId,
        expenseData.projectName,
        expenseData.payee,
        expenseData.payeeCode,
        expenseData.amount,
        expenseData.paymentDate,
        expenseData.status || '未処理',
        now
      ];
      
      sheet.appendRow(newRow);
      return { success: true, id: newId, message: '費用データを作成しました' };
    } else {
      // 更新
      const id = expenseData.id;
      const lastRow = sheet.getLastRow();
      
      for (let i = 2; i <= lastRow; i++) {
        if (sheet.getRange(i, 1).getValue() == id) {
          sheet.getRange(i, 2, 1, 6).setValues([[
            expenseData.projectName,
            expenseData.payee,
            expenseData.payeeCode,
            expenseData.amount,
            expenseData.paymentDate,
            expenseData.status || '未処理'
          ]]);
          return { success: true, id: id, message: '費用データを更新しました' };
        }
      }
      
      throw new Error('更新対象のデータが見つかりません');
    }
  } catch (error) {
    console.error('費用データ保存エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 費用マスターデータを保存
 */
function saveMaster(masterData, isNew = false) {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    const now = new Date();
    
    if (isNew) {
      // 新規作成
      const newId = generateId();
      const newRow = [
        newId,
        masterData.projectName,
        masterData.payee,
        masterData.payeeCode,
        masterData.amount,
        masterData.paymentType || '月額固定',
        masterData.startDate,
        masterData.endDate,
        masterData.broadcastDays,
        now
      ];
      
      sheet.appendRow(newRow);
      return { success: true, id: newId, message: '費用マスターデータを作成しました' };
    } else {
      // 更新
      const id = masterData.id;
      const lastRow = sheet.getLastRow();
      
      for (let i = 2; i <= lastRow; i++) {
        if (sheet.getRange(i, 1).getValue() == id) {
          sheet.getRange(i, 2, 1, 8).setValues([[
            masterData.projectName,
            masterData.payee,
            masterData.payeeCode,
            masterData.amount,
            masterData.paymentType || '月額固定',
            masterData.startDate,
            masterData.endDate,
            masterData.broadcastDays
          ]]);
          return { success: true, id: id, message: '費用マスターデータを更新しました' };
        }
      }
      
      throw new Error('更新対象のデータが見つかりません');
    }
  } catch (error) {
    console.error('費用マスターデータ保存エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * データを削除
 */
function deleteData(sheetName, id) {
  try {
    const sheet = getOrCreateSheet(sheetName);
    const lastRow = sheet.getLastRow();
    
    for (let i = 2; i <= lastRow; i++) {
      if (sheet.getRange(i, 1).getValue() == id) {
        sheet.deleteRow(i);
        return { success: true, message: 'データを削除しました' };
      }
    }
    
    throw new Error('削除対象のデータが見つかりません');
  } catch (error) {
    console.error('データ削除エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * データを複製
 */
function duplicateData(sheetName, id) {
  try {
    const sheet = getOrCreateSheet(sheetName);
    const lastRow = sheet.getLastRow();
    
    for (let i = 2; i <= lastRow; i++) {
      if (sheet.getRange(i, 1).getValue() == id) {
        const rowData = sheet.getRange(i, 1, 1, sheet.getLastColumn()).getValues()[0];
        const newId = generateId();
        const newRow = [...rowData];
        newRow[0] = newId; // 新しいID
        newRow[1] = newRow[1] + ' (複製)'; // 名前に「(複製)」を追加
        newRow[newRow.length - 1] = new Date(); // 作成日時を更新
        
        sheet.appendRow(newRow);
        return { success: true, id: newId, message: 'データを複製しました' };
      }
    }
    
    throw new Error('複製対象のデータが見つかりません');
  } catch (error) {
    console.error('データ複製エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 支払いデータのステータスを更新
 */
function updatePaymentStatus(id, status) {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    const lastRow = sheet.getLastRow();
    
    for (let i = 2; i <= lastRow; i++) {
      if (sheet.getRange(i, 1).getValue() == id) {
        sheet.getRange(i, 8).setValue(status);
        return { success: true, message: 'ステータスを更新しました' };
      }
    }
    
    throw new Error('更新対象のデータが見つかりません');
  } catch (error) {
    console.error('ステータス更新エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 費用データと支払いデータを照合
 */
function matchExpensesWithPayments() {
  try {
    const expenseSheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const paymentSheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    
    const expenseData = expenseSheet.getRange(2, 1, expenseSheet.getLastRow() - 1, 8).getValues();
    const paymentData = paymentSheet.getRange(2, 1, paymentSheet.getLastRow() - 1, 9).getValues();
    
    let matchedCount = 0;
    let notMatchedCount = 0;
    
    // 費用データと支払いデータを照合
    expenseData.forEach((expenseRow, expenseIndex) => {
      if (expenseRow[0] === '') return; // 空行をスキップ
      
      const expenseAmount = parseFloat(expenseRow[4]) || 0;
      const expensePayee = (expenseRow[2] || '').toString().toLowerCase().trim();
      const expenseDate = extractYearMonth(expenseRow[5]);
      
      let isMatched = false;
      
      paymentData.forEach((paymentRow, paymentIndex) => {
        if (paymentRow[0] === '' || paymentRow[7] === '照合済') return; // 空行または既に照合済みをスキップ
        
        const paymentAmount = parseFloat(paymentRow[5]) || 0;
        const paymentPayee = (paymentRow[3] || '').toString().toLowerCase().trim();
        const paymentDate = extractYearMonth(paymentRow[6]);
        
        // 照合条件: 金額、支払い先、年月が一致
        if (Math.abs(expenseAmount - paymentAmount) < 0.01 && 
            expensePayee === paymentPayee && 
            expenseDate === paymentDate) {
          
          // 両方のステータスを「照合済」に更新
          expenseSheet.getRange(expenseIndex + 2, 7).setValue('照合済');
          paymentSheet.getRange(paymentIndex + 2, 8).setValue('照合済');
          
          isMatched = true;
          matchedCount++;
        }
      });
      
      if (!isMatched && expenseRow[6] !== '照合済') {
        notMatchedCount++;
      }
    });
    
    return { 
      success: true, 
      matchedCount, 
      notMatchedCount, 
      message: `照合完了: ${matchedCount}件一致、${notMatchedCount}件不一致` 
    };
  } catch (error) {
    console.error('照合処理エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 日付から年月を抽出
 */
function extractYearMonth(dateValue) {
  if (!dateValue) return null;
  
  try {
    let dateStr = dateValue.toString();
    if (dateValue instanceof Date) {
      dateStr = Utilities.formatDate(dateValue, Session.getScriptTimeZone(), 'yyyy-MM');
    } else {
      // 文字列の場合、年月部分を抽出
      const matches = dateStr.match(/(\d{4})[\/\-](\d{1,2})/);
      if (matches) {
        const year = matches[1];
        const month = matches[2].padStart(2, '0');
        dateStr = `${year}-${month}`;
      }
    }
    return dateStr.substring(0, 7); // YYYY-MM形式
  } catch (error) {
    console.error('日付抽出エラー:', error);
    return null;
  }
}

/**
 * ユニークIDを生成
 */
function generateId() {
  return 'ID_' + Utilities.getUuid().substring(0, 8) + '_' + new Date().getTime();
}