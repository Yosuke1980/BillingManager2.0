//Additional.gs

/**
 * 追加のGAS関数 - CSVエクスポート/インポートや統計など
 */

/**
 * 統計データをまとめて取得
 */
function loadAllStats() {
  try {
    const payments = getPaymentData();
    const expenses = getExpenseData();
    const master = getMasterData();
    
    return {
      payments: payments,
      expenses: expenses,
      master: master
    };
  } catch (error) {
    console.error('統計データ取得エラー:', error);
    throw new Error('統計データの取得に失敗しました');
  }
}

/**
 * 複数の支払いデータのステータスを一括更新
 */
function updateMultiplePaymentStatus(updates) {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    const lastRow = sheet.getLastRow();
    let updatedCount = 0;
    
    updates.forEach(update => {
      for (let i = 2; i <= lastRow; i++) {
        if (sheet.getRange(i, 1).getValue() == update.id) {
          sheet.getRange(i, 8).setValue(update.status);
          updatedCount++;
          break;
        }
      }
    });
    
    return { 
      success: true, 
      count: updatedCount,
      message: `${updatedCount}件のステータスを更新しました` 
    };
  } catch (error) {
    console.error('複数ステータス更新エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 費用データをCSV形式でエクスポート
 */
function exportExpensesToCsv() {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const lastRow = sheet.getLastRow();
    
    if (lastRow <= 1) {
      const headers = 'ID,案件名,支払い先,支払い先コード,金額,支払日,状態\n';
      return convertToBase64(headers);
    }
    
    const data = sheet.getRange(1, 1, lastRow, 7).getValues();
    
    // CSVデータを生成
    let csvContent = '';
    data.forEach(row => {
      const csvRow = row.map(cell => {
        // 日付の場合は文字列に変換
        if (cell instanceof Date) {
          return Utilities.formatDate(cell, Session.getScriptTimeZone(), 'yyyy-MM-dd');
        }
        // 文字列の場合はダブルクォートでエスケープ
        if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"') || cell.includes('\n'))) {
          return '"' + cell.replace(/"/g, '""') + '"';
        }
        return cell;
      }).join(',');
      
      csvContent += csvRow + '\n';
    });
    
    return convertToBase64(csvContent);
  } catch (error) {
    console.error('CSVエクスポートエラー:', error);
    throw new Error('CSVエクスポートに失敗しました');
  }
}

/**
 * 費用マスターデータをCSV形式でエクスポート
 */
function exportMasterToCsv() {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    const lastRow = sheet.getLastRow();
    
    if (lastRow <= 1) {
      const headers = 'ID,案件名,支払い先,支払い先コード,金額,種別,開始日,終了日,放送曜日\n';
      return convertToBase64(headers);
    }
    
    const data = sheet.getRange(1, 1, lastRow, 9).getValues();
    
    // CSVデータを生成
    let csvContent = '';
    data.forEach(row => {
      const csvRow = row.map(cell => {
        // 日付の場合は文字列に変換
        if (cell instanceof Date) {
          return Utilities.formatDate(cell, Session.getScriptTimeZone(), 'yyyy-MM-dd');
        }
        // 文字列の場合はダブルクォートでエスケープ
        if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"') || cell.includes('\n'))) {
          return '"' + cell.replace(/"/g, '""') + '"';
        }
        return cell;
      }).join(',');
      
      csvContent += csvRow + '\n';
    });
    
    return convertToBase64(csvContent);
  } catch (error) {
    console.error('CSVエクスポートエラー:', error);
    throw new Error('CSVエクスポートに失敗しました');
  }
}

/**
 * 文字列をBase64エンコード
 */
function convertToBase64(csvContent) {
  try {
    const blob = Utilities.newBlob(csvContent, 'text/csv; charset=UTF-8');
    const base64Content = Utilities.base64Encode(blob.getBytes());
    return base64Content;
  } catch (error) {
    console.error('Base64変換エラー:', error);
    throw new Error('CSVファイルの生成に失敗しました');
  }
}

/**
 * 費用データのCSVインポート
 */
function importExpensesFromCsv(csvContent) {
  try {
    console.log('=== 費用データCSVインポート開始 ===');
    const lines = csvContent.trim().split(/\r?\n/);
    
    if (lines.length < 2) {
      throw new Error('CSVファイルが空または不正です');
    }
    
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const headers = parseCSVLine(lines[0]);
    let importedCount = 0;
    let errorCount = 0;
    const errorDetails = [];
    
    console.log('費用データヘッダー:', headers);
    
    // ヘッダー行をスキップして処理
    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].trim();
        if (!line) continue;
        
        const row = parseCSVLine(line);
        console.log(`費用データ行 ${i+1}:`, row);
        
        if (row.length < 6) {
          const error = `行 ${i+1}: 列数不足 (${row.length}列)`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const newId = generateId();
        const projectName = cleanString(row[1]);
        const payee = cleanString(row[2]);
        const payeeCode = cleanString(row[3]);
        
        // 金額の変換
        let amount = 0;
        try {
          const amountStr = cleanString(row[4]);
          if (amountStr) {
            amount = parseFloat(amountStr.replace(/[^\d.-]/g, ''));
            if (isNaN(amount)) {
              throw new Error(`金額が数値ではありません: "${amountStr}"`);
            }
          }
        } catch (amountError) {
          const error = `行 ${i+1}: 金額エラー - ${amountError.message}`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const paymentDate = cleanString(row[5]);
        const status = cleanString(row[6]) || '未処理';
        
        // 必須フィールドチェック
        if (!projectName || !payee) {
          const error = `行 ${i+1}: 必須項目が不足`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const newRow = [
          newId,
          projectName,
          payee,
          payeeCode,
          amount,
          paymentDate,
          status,
          new Date()
        ];
        
        sheet.appendRow(newRow);
        importedCount++;
        
      } catch (parseError) {
        const error = `行 ${i+1}: 解析エラー - ${parseError.message}`;
        errorDetails.push(error);
        errorCount++;
      }
    }
    
    let message = `${importedCount}件の費用データをインポートしました`;
    if (errorCount > 0) {
      message += ` (エラー: ${errorCount}件)`;
    }
    
    return { 
      success: true, 
      count: importedCount, 
      errorCount: errorCount,
      errorDetails: errorDetails.slice(0, 10),
      message: message
    };
  } catch (error) {
    console.error('費用データCSVインポートエラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 費用マスターCSVインポート
 */
function importMasterCsvText(csvContent) {
  try {
    console.log('=== 費用マスターCSVインポート開始 ===');
    console.log('受信したコンテンツの最初の200文字:', csvContent.substring(0, 200));
    
    let processedContent = csvContent;
    
    // UTF-8 BOMを除去
    if (processedContent.charCodeAt(0) === 0xFEFF) {
      processedContent = processedContent.slice(1);
      console.log('UTF-8 BOMを除去');
    }
    
    const lines = processedContent.trim().split(/\r?\n/);
    console.log(`総行数: ${lines.length}`);
    
    if (lines.length < 2) {
      throw new Error('CSVファイルが空または不正です');
    }
    
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    let importedCount = 0;
    let errorCount = 0;
    const errorDetails = [];
    
    // ヘッダー行を確認
    const headers = parseCSVLine(lines[0]);
    console.log('ヘッダー行:', headers);
    
    // ヘッダー行をスキップして処理
    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].trim();
        if (!line) {
          console.log(`行 ${i+1}: 空行をスキップ`);
          continue;
        }
        
        const row = parseCSVLine(line);
        console.log(`行 ${i+1} 解析結果:`, row);
        
        if (row.length < 5) {
          const error = `行 ${i+1}: 列数不足 (${row.length}列) - 最低5列必要`;
          console.error(error);
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const newId = generateId();
        const projectName = cleanString(row[1]);
        const payee = cleanString(row[2]);
        const payeeCode = cleanString(row[3]);
        
        // 金額の検証
        let amount = 0;
        try {
          const amountStr = cleanString(row[4]);
          if (amountStr) {
            amount = parseFloat(amountStr.replace(/[^\d.-]/g, ''));
            if (isNaN(amount)) {
              throw new Error(`金額が数値ではありません: "${amountStr}"`);
            }
          }
        } catch (amountError) {
          const error = `行 ${i+1}: 金額エラー - ${amountError.message}`;
          console.error(error);
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const paymentType = cleanString(row[5]) || '月額固定';
        const startDate = formatDateForSheet(row[6]);
        const endDate = formatDateForSheet(row[7]);
        const broadcastDays = cleanString(row[8]);
        
        // 必須フィールドのチェック
        if (!projectName) {
          const error = `行 ${i+1}: 案件名が空です`;
          console.error(error);
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        if (!payee) {
          const error = `行 ${i+1}: 支払い先が空です`;
          console.error(error);
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const newRow = [
          newId,              // 新しいID
          projectName,        // 案件名
          payee,              // 支払い先
          payeeCode,          // 支払い先コード
          amount,             // 金額
          paymentType,        // 種別
          startDate,          // 開始日
          endDate,            // 終了日
          broadcastDays,      // 放送曜日
          new Date()          // 作成日時
        ];
        
        console.log(`挿入予定データ:`, newRow);
        
        try {
          sheet.appendRow(newRow);
          importedCount++;
          console.log(`行 ${i+1}: 正常にインポート完了`);
        } catch (insertError) {
          const error = `行 ${i+1}: スプレッドシートへの挿入に失敗 - ${insertError.message}`;
          console.error(error);
          errorDetails.push(error);
          errorCount++;
        }
        
      } catch (parseError) {
        const error = `行 ${i+1}: 解析エラー - ${parseError.message}`;
        console.error(error);
        errorDetails.push(error);
        errorCount++;
      }
    }
    
    console.log('=== インポート結果 ===');
    console.log(`成功: ${importedCount}件`);
    console.log(`エラー: ${errorCount}件`);
    
    let message = `${importedCount}件の費用マスターデータをインポートしました`;
    if (errorCount > 0) {
      message += ` (エラー: ${errorCount}件)`;
    }
    
    return { 
      success: true, 
      count: importedCount, 
      errorCount: errorCount,
      errorDetails: errorDetails.slice(0, 10),
      message: message
    };
  } catch (error) {
    console.error('CSVインポート全体エラー:', error);
    return { 
      success: false, 
      message: `インポートエラー: ${error.toString()}`,
      errorDetails: [error.toString()]
    };
  }
}

/**
 * CSV行を正しく解析する関数
 */
function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      if (inQuotes && i + 1 < line.length && line[i + 1] === '"') {
        // エスケープされたダブルクォート
        current += '"';
        i++; // 次の文字をスキップ
      } else {
        // クォートの開始または終了
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      // フィールドの区切り
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  // 最後のフィールドを追加
  result.push(current.trim());
  
  return result;
}

/**
 * 文字列をクリーンアップする関数
 */
function cleanString(str) {
  if (str === null || str === undefined) return '';
  
  let cleaned = str.toString().trim();
  
  // ダブルクォートで囲まれている場合は除去
  if (cleaned.startsWith('"') && cleaned.endsWith('"') && cleaned.length > 1) {
    cleaned = cleaned.slice(1, -1);
  }
  
  // エスケープされたダブルクォートを復元
  cleaned = cleaned.replace(/""/g, '"');
  
  // 特殊な空白文字を除去
  cleaned = cleaned.replace(/[\u00A0\u2000-\u200B\u2028\u2029]/g, ' ').trim();
  
  return cleaned;
}

/**
 * 日付フォーマットをスプレッドシート用に変換
 */
function formatDateForSheet(dateStr) {
  if (!dateStr || dateStr.trim() === '') return '';
  
  try {
    let cleaned = cleanString(dateStr);
    if (!cleaned) return '';
    
    // 既にYYYY-MM-DD形式の場合
    if (/^\d{4}-\d{2}-\d{2}$/.test(cleaned)) {
      return cleaned;
    }
    
    // YYYY/MM/DD形式をYYYY-MM-DD形式に変換
    if (cleaned.includes('/')) {
      const parts = cleaned.split('/');
      if (parts.length === 3) {
        let year = parts[0].trim();
        let month = parts[1].trim();
        let day = parts[2].trim();
        
        // 年の補完（2桁の場合）
        if (year.length === 2) {
          const currentYear = new Date().getFullYear();
          const century = Math.floor(currentYear / 100) * 100;
          year = (parseInt(year) + century).toString();
        }
        
        year = year.padStart(4, '0');
        month = month.padStart(2, '0');
        day = day.padStart(2, '0');
        
        const monthNum = parseInt(month);
        const dayNum = parseInt(day);
        const yearNum = parseInt(year);
        
        if (monthNum >= 1 && monthNum <= 12 && dayNum >= 1 && dayNum <= 31 && yearNum >= 1900 && yearNum <= 2100) {
          return `${year}-${month}-${day}`;
        }
      }
    }
    
    // JavaScriptのDate()による解析を試行
    try {
      const parsedDate = new Date(cleaned);
      if (!isNaN(parsedDate.getTime()) && parsedDate.getFullYear() >= 1900 && parsedDate.getFullYear() <= 2100) {
        return Utilities.formatDate(parsedDate, Session.getScriptTimeZone(), 'yyyy-MM-dd');
      }
    } catch (jsDateError) {
      console.log('JavaScript Date解析失敗:', jsDateError.message);
    }
    
    return '';
  } catch (error) {
    console.error('日付フォーマットエラー:', error);
    return '';
  }
}

/**
 * データベースの整合性チェック
 */
function checkDataIntegrity() {
  try {
    const expenseSheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const paymentSheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    const masterSheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    
    const issues = [];
    
    // 重複IDのチェック
    const checkDuplicateIds = (sheet, sheetName) => {
      const lastRow = sheet.getLastRow();
      if (lastRow <= 1) return;
      
      const ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues().flat();
      const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index && id !== '');
      
      if (duplicates.length > 0) {
        issues.push(`${sheetName}に重複ID: ${duplicates.join(', ')}`);
      }
    };
    
    checkDuplicateIds(expenseSheet, '費用データ');
    checkDuplicateIds(paymentSheet, '支払いデータ');
    checkDuplicateIds(masterSheet, '費用マスター');
    
    // 必須フィールドの空白チェック
    const checkRequiredFields = (sheet, sheetName, requiredColumns) => {
      const lastRow = sheet.getLastRow();
      if (lastRow <= 1) return;
      
      const data = sheet.getRange(2, 1, lastRow - 1, Math.max(...requiredColumns) + 1).getValues();
      
      data.forEach((row, rowIndex) => {
        if (row[0] === '') return; // IDが空の行はスキップ
        
        requiredColumns.forEach(colIndex => {
          if (!row[colIndex] || row[colIndex].toString().trim() === '') {
            const columnName = sheet.getRange(1, colIndex + 1).getValue();
            issues.push(`${sheetName} 行${rowIndex + 2}: ${columnName}が空白`);
          }
        });
      });
    };
    
    checkRequiredFields(expenseSheet, '費用データ', [1, 2, 4, 5]); // 案件名、支払い先、金額、支払日
    checkRequiredFields(paymentSheet, '支払いデータ', [2, 3, 5, 6]); // 案件名、支払い先、金額、支払日
    checkRequiredFields(masterSheet, '費用マスター', [1, 2, 4]); // 案件名、支払い先、金額
    
    return { 
      success: true, 
      issues: issues,
      message: issues.length === 0 ? 'データに問題はありません' : `${issues.length}件の問題が見つかりました`
    };
  } catch (error) {
    console.error('整合性チェックエラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * バックアップ作成
 */
function createBackup() {
  try {
    const sourceSpreadsheet = getSpreadsheet();
    const backupName = `バックアップ_${Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd_HHmmss')}`;
    
    const backupSpreadsheet = sourceSpreadsheet.copy(backupName);
    
    return { 
      success: true, 
      backupId: backupSpreadsheet.getId(),
      backupUrl: backupSpreadsheet.getUrl(),
      message: 'バックアップを作成しました' 
    };
  } catch (error) {
    console.error('バックアップ作成エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * データクリーンアップ（重複データの削除など）
 */
function cleanupData() {
  try {
    const expenseSheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const paymentSheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    const masterSheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    
    let cleanedCount = 0;
    
    // 重複行の削除
    const removeDuplicates = (sheet, sheetName) => {
      const lastRow = sheet.getLastRow();
      if (lastRow <= 1) return 0;
      
      const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
      const uniqueData = [];
      const seenRows = new Set();
      
      data.forEach(row => {
        const rowKey = row.slice(1).join('|'); // IDを除いた内容でキーを作成
        if (!seenRows.has(rowKey) && row[0] !== '') {
          seenRows.add(rowKey);
          uniqueData.push(row);
        } else if (seenRows.has(rowKey)) {
          cleanedCount++;
        }
      });
      
      // データをクリアして再設定
      if (uniqueData.length !== data.length) {
        sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clear();
        if (uniqueData.length > 0) {
          sheet.getRange(2, 1, uniqueData.length, sheet.getLastColumn()).setValues(uniqueData);
        }
      }
      
      return cleanedCount;
    };
    
    removeDuplicates(expenseSheet, '費用データ');
    removeDuplicates(paymentSheet, '支払いデータ');
    removeDuplicates(masterSheet, '費用マスター');
    
    return { 
      success: true, 
      cleanedCount,
      message: `${cleanedCount}件の重複データを削除しました` 
    };
  } catch (error) {
    console.error('データクリーンアップエラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * デバッグ用：スプレッドシートの内容を確認
 */
function debugSpreadsheetContent() {
  try {
    const sheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    const lastRow = sheet.getLastRow();
    
    if (lastRow <= 1) {
      return { message: 'データが存在しません' };
    }
    
    const data = sheet.getRange(1, 1, Math.min(lastRow, 5), sheet.getLastColumn()).getValues();
    
    console.log('スプレッドシートの内容（最初の5行）:');
    data.forEach((row, index) => {
      console.log(`行 ${index + 1}:`, row);
    });
    
    return { 
      success: true, 
      data: data,
      totalRows: lastRow,
      message: `スプレッドシートに${lastRow}行のデータがあります` 
    };
  } catch (error) {
    console.error('スプレッドシート内容確認エラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * データを強制再読み込み
 */
function forceRefreshData() {
  try {
    // 各シートからデータを取得して返す
    const payments = getPaymentData();
    const expenses = getExpenseData();
    const master = getMasterData();
    
    return {
      success: true,
      payments: payments,
      expenses: expenses,
      master: master,
      message: 'データを強制再読み込みしました'
    };
  } catch (error) {
    console.error('強制再読み込みエラー:', error);
    return { success: false, message: error.toString() };
  }
}

/**
 * 診断システム - 表示問題の原因究明
 * Additional.gsに追加するコード
 */

/**
 * 総合診断 - 全ての問題を段階的にチェック
 */
function comprehensiveDiagnosis() {
  const diagnosis = {
    timestamp: new Date(),
    steps: [],
    summary: {
      spreadsheetAccess: false,
      dataExists: false,
      dataStructure: false,
      frontendReady: false,
      overallStatus: 'UNKNOWN'
    },
    recommendations: []
  };

  try {
    console.log('=== 総合診断開始 ===');
    
    // ステップ1: スプレッドシートアクセス診断
    const step1 = diagnoseSpreadsheetAccess();
    diagnosis.steps.push(step1);
    diagnosis.summary.spreadsheetAccess = step1.success;
    
    if (!step1.success) {
      diagnosis.summary.overallStatus = 'SPREADSHEET_ACCESS_ERROR';
      diagnosis.recommendations.push('スプレッドシートIDを確認し、アクセス権限を確認してください');
      return diagnosis;
    }
    
    // ステップ2: データ存在診断
    const step2 = diagnoseDataExistence();
    diagnosis.steps.push(step2);
    diagnosis.summary.dataExists = step2.hasData;
    
    // ステップ3: データ構造診断
    const step3 = diagnoseDataStructure();
    diagnosis.steps.push(step3);
    diagnosis.summary.dataStructure = step3.success;
    
    // ステップ4: データ取得機能診断
    const step4 = diagnoseDataRetrieval();
    diagnosis.steps.push(step4);
    
    // ステップ5: フロントエンド準備状況診断
    const step5 = diagnoseFrontendReadiness();
    diagnosis.steps.push(step5);
    diagnosis.summary.frontendReady = step5.success;
    
    // 総合判定
    if (diagnosis.summary.spreadsheetAccess && diagnosis.summary.dataStructure) {
      if (diagnosis.summary.dataExists) {
        diagnosis.summary.overallStatus = 'DATA_READY';
      } else {
        diagnosis.summary.overallStatus = 'NO_DATA';
        diagnosis.recommendations.push('データが存在しません。テストデータを作成するか、データをインポートしてください');
      }
    } else {
      diagnosis.summary.overallStatus = 'STRUCTURE_ERROR';
      diagnosis.recommendations.push('データ構造に問題があります。初期化を実行してください');
    }
    
    console.log('=== 総合診断完了 ===');
    console.log('診断結果:', diagnosis.summary);
    
    return {
      success: true,
      diagnosis: diagnosis,
      message: `診断完了: ${diagnosis.summary.overallStatus}`
    };
    
  } catch (error) {
    console.error('総合診断エラー:', error);
    diagnosis.summary.overallStatus = 'DIAGNOSIS_ERROR';
    diagnosis.recommendations.push(`診断中にエラーが発生しました: ${error.toString()}`);
    
    return {
      success: false,
      diagnosis: diagnosis,
      message: `診断エラー: ${error.toString()}`
    };
  }
}

/**
 * ステップ1: スプレッドシートアクセス診断
 */
function diagnoseSpreadsheetAccess() {
  const step = {
    name: 'スプレッドシートアクセス診断',
    success: false,
    details: {},
    errors: []
  };
  
  try {
    console.log('--- スプレッドシートアクセス診断 ---');
    
    // スプレッドシートIDチェック
    step.details.spreadsheetId = SPREADSHEET_ID;
    if (!SPREADSHEET_ID || SPREADSHEET_ID === 'YOUR_SPREADSHEET_ID_HERE') {
      step.errors.push('スプレッドシートIDが設定されていません');
      return step;
    }
    
    // スプレッドシートアクセス試行
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    step.details.spreadsheetName = ss.getName();
    step.details.spreadsheetUrl = ss.getUrl();
    
    // シート一覧取得
    const sheets = ss.getSheets();
    step.details.sheetCount = sheets.length;
    step.details.sheetNames = sheets.map(sheet => sheet.getName());
    
    step.success = true;
    console.log('スプレッドシートアクセス成功:', step.details);
    
  } catch (error) {
    step.errors.push(`スプレッドシートアクセスエラー: ${error.toString()}`);
    console.error('スプレッドシートアクセス失敗:', error);
  }
  
  return step;
}

/**
 * ステップ2: データ存在診断
 */
function diagnoseDataExistence() {
  const step = {
    name: 'データ存在診断',
    hasData: false,
    details: {
      payments: { rows: 0, hasData: false },
      expenses: { rows: 0, hasData: false },
      master: { rows: 0, hasData: false }
    },
    errors: []
  };
  
  try {
    console.log('--- データ存在診断 ---');
    
    const sheetConfigs = [
      { key: 'payments', name: SHEET_NAMES.PAYMENTS },
      { key: 'expenses', name: SHEET_NAMES.EXPENSES },
      { key: 'master', name: SHEET_NAMES.EXPENSE_MASTER }
    ];
    
    sheetConfigs.forEach(config => {
      try {
        const sheet = getOrCreateSheet(config.name);
        const lastRow = sheet.getLastRow();
        step.details[config.key].rows = lastRow;
        step.details[config.key].hasData = lastRow > 1; // ヘッダー行以外にデータがあるか
        
        if (lastRow > 1) {
          // 実際のデータ行数を確認
          const data = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
          const nonEmptyRows = data.filter(row => row[0] && row[0] !== '').length;
          step.details[config.key].nonEmptyRows = nonEmptyRows;
          step.details[config.key].hasData = nonEmptyRows > 0;
        }
        
        console.log(`${config.name}: ${step.details[config.key].rows}行, データ有無: ${step.details[config.key].hasData}`);
        
      } catch (error) {
        step.errors.push(`${config.name}の確認エラー: ${error.toString()}`);
      }
    });
    
    // 全体のデータ存在判定
    step.hasData = Object.values(step.details).some(detail => detail.hasData);
    
  } catch (error) {
    step.errors.push(`データ存在診断エラー: ${error.toString()}`);
    console.error('データ存在診断失敗:', error);
  }
  
  return step;
}

/**
 * ステップ3: データ構造診断
 */
function diagnoseDataStructure() {
  const step = {
    name: 'データ構造診断',
    success: false,
    details: {},
    errors: []
  };
  
  try {
    console.log('--- データ構造診断 ---');
    
    const expectedStructures = {
      [SHEET_NAMES.PAYMENTS]: ['ID', '件名', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日時'],
      [SHEET_NAMES.EXPENSES]: ['ID', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日時'],
      [SHEET_NAMES.EXPENSE_MASTER]: ['ID', '案件名', '支払い先', '支払い先コード', '金額', '種別', '開始日', '終了日', '放送曜日', '作成日時']
    };
    
    let allStructuresValid = true;
    
    Object.entries(expectedStructures).forEach(([sheetName, expectedHeaders]) => {
      try {
        const sheet = getOrCreateSheet(sheetName);
        const actualHeaders = sheet.getRange(1, 1, 1, expectedHeaders.length).getValues()[0];
        
        const structureCheck = {
          expectedColumns: expectedHeaders.length,
          actualColumns: actualHeaders.length,
          headersMatch: true,
          missingHeaders: [],
          extraHeaders: []
        };
        
        // ヘッダーの一致確認
        expectedHeaders.forEach((expected, index) => {
          if (actualHeaders[index] !== expected) {
            structureCheck.headersMatch = false;
            structureCheck.missingHeaders.push(expected);
          }
        });
        
        step.details[sheetName] = structureCheck;
        
        if (!structureCheck.headersMatch) {
          allStructuresValid = false;
          step.errors.push(`${sheetName}のヘッダー構造が不正です`);
        }
        
        console.log(`${sheetName}構造チェック:`, structureCheck);
        
      } catch (error) {
        allStructuresValid = false;
        step.errors.push(`${sheetName}の構造確認エラー: ${error.toString()}`);
      }
    });
    
    step.success = allStructuresValid;
    
  } catch (error) {
    step.errors.push(`データ構造診断エラー: ${error.toString()}`);
    console.error('データ構造診断失敗:', error);
  }
  
  return step;
}

/**
 * ステップ4: データ取得機能診断
 */
function diagnoseDataRetrieval() {
  const step = {
    name: 'データ取得機能診断',
    success: false,
    details: {},
    errors: []
  };
  
  try {
    console.log('--- データ取得機能診断 ---');
    
    // 各データ取得関数をテスト
    const retrievalTests = [
      { name: 'getPaymentData', func: getPaymentData },
      { name: 'getExpenseData', func: getExpenseData },
      { name: 'getMasterData', func: getMasterData }
    ];
    
    let allRetrievalsSuccessful = true;
    
    retrievalTests.forEach(test => {
      try {
        const startTime = new Date();
        const result = test.func('');
        const endTime = new Date();
        
        const testResult = {
          success: true,
          executionTime: endTime - startTime,
          dataCount: result.data ? result.data.length : 0,
          hasData: result.data && result.data.length > 0,
          resultStructure: {
            hasDataProperty: result.hasOwnProperty('data'),
            dataIsArray: Array.isArray(result.data),
            sampleRecord: result.data && result.data.length > 0 ? Object.keys(result.data[0]) : []
          }
        };
        
        step.details[test.name] = testResult;
        console.log(`${test.name}テスト結果:`, testResult);
        
      } catch (error) {
        allRetrievalsSuccessful = false;
        const testResult = {
          success: false,
          error: error.toString()
        };
        step.details[test.name] = testResult;
        step.errors.push(`${test.name}実行エラー: ${error.toString()}`);
        console.error(`${test.name}テスト失敗:`, error);
      }
    });
    
    step.success = allRetrievalsSuccessful;
    
  } catch (error) {
    step.errors.push(`データ取得機能診断エラー: ${error.toString()}`);
    console.error('データ取得機能診断失敗:', error);
  }
  
  return step;
}

/**
 * ステップ5: フロントエンド準備状況診断
 */
function diagnoseFrontendReadiness() {
  const step = {
    name: 'フロントエンド準備状況診断',
    success: false,
    details: {
      htmlStructure: 'HTML構造の確認はクライアント側で実行してください',
      recommendedChecks: [
        'document.getElementById("masterTableBody")が存在するか',
        'document.getElementById("expenseTableBody")が存在するか',
        'document.getElementById("paymentTableBody")が存在するか',
        'Bootstrap CSSが読み込まれているか',
        'JavaScriptエラーがコンソールに出ていないか'
      ]
    },
    errors: []
  };
  
  try {
    console.log('--- フロントエンド準備状況診断 ---');
    
    // GAS側でできる基本的なチェック
    step.details.gasConfiguration = {
      includeFunction: typeof include === 'function',
      doGetFunction: typeof doGet === 'function',
      webAppReady: true
    };
    
    step.success = true; // フロントエンドの詳細チェックはクライアント側で実行
    
  } catch (error) {
    step.errors.push(`フロントエンド診断エラー: ${error.toString()}`);
    console.error('フロントエンド診断失敗:', error);
  }
  
  return step;
}

/**
 * 簡易テストデータ作成
 */
function createTestData() {
  try {
    console.log('=== テストデータ作成開始 ===');
    
    const results = {
      payments: 0,
      expenses: 0,
      master: 0
    };
    
    // 費用マスターテストデータ
    const masterSheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    const masterTestData = [
      [generateId(), 'テスト案件A', 'テスト会社A', 'TEST001', 50000, '月額固定', '2024-01-01', '2024-12-31', '月,水,金', new Date()],
      [generateId(), 'テスト案件B', 'テスト会社B', 'TEST002', 30000, '回数ベース', '2024-02-01', '2024-11-30', '火,木', new Date()]
    ];
    
    masterTestData.forEach(row => {
      masterSheet.appendRow(row);
      results.master++;
    });
    
    // 費用データテストデータ
    const expenseSheet = getOrCreateSheet(SHEET_NAMES.EXPENSES);
    const expenseTestData = [
      [generateId(), 'テスト案件A', 'テスト会社A', 'TEST001', 50000, '2024-01-15', '未処理', new Date()],
      [generateId(), 'テスト案件B', 'テスト会社B', 'TEST002', 30000, '2024-02-15', '未処理', new Date()]
    ];
    
    expenseTestData.forEach(row => {
      expenseSheet.appendRow(row);
      results.expenses++;
    });
    
    // 支払いデータテストデータ
    const paymentSheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    const paymentTestData = [
      [generateId(), 'テスト件名A', 'テスト案件A', 'テスト会社A', 'TEST001', 50000, '2024-01-15', '未処理', new Date()],
      [generateId(), 'テスト件名B', 'テスト案件B', 'テスト会社B', 'TEST002', 30000, '2024-02-15', '未処理', new Date()]
    ];
    
    paymentTestData.forEach(row => {
      paymentSheet.appendRow(row);
      results.payments++;
    });
    
    console.log('=== テストデータ作成完了 ===');
    console.log('作成されたデータ:', results);
    
    return {
      success: true,
      message: `テストデータを作成しました（支払い:${results.payments}件、費用:${results.expenses}件、マスター:${results.master}件）`,
      results: results
    };
    
  } catch (error) {
    console.error('テストデータ作成エラー:', error);
    return {
      success: false,
      message: `テストデータの作成に失敗しました: ${error.toString()}`
    };
  }
}

/**
 * 全データクリア（診断用）
 */
function clearAllDataForDiagnosis() {
  try {
    console.log('=== 全データクリア開始 ===');
    
    const results = {
      payments: 0,
      expenses: 0,
      master: 0
    };
    
    const sheetNames = [SHEET_NAMES.PAYMENTS, SHEET_NAMES.EXPENSES, SHEET_NAMES.EXPENSE_MASTER];
    
    sheetNames.forEach(sheetName => {
      try {
        const sheet = getOrCreateSheet(sheetName);
        const lastRow = sheet.getLastRow();
        
        if (lastRow > 1) {
          const dataRows = lastRow - 1;
          sheet.deleteRows(2, dataRows);
          
          if (sheetName === SHEET_NAMES.PAYMENTS) results.payments = dataRows;
          else if (sheetName === SHEET_NAMES.EXPENSES) results.expenses = dataRows;
          else if (sheetName === SHEET_NAMES.EXPENSE_MASTER) results.master = dataRows;
          
          console.log(`${sheetName}: ${dataRows}行削除`);
        }
      } catch (error) {
        console.error(`${sheetName}のクリアエラー:`, error);
      }
    });
    
    console.log('=== 全データクリア完了 ===');
    
    return {
      success: true,
      message: `全データをクリアしました（支払い:${results.payments}行、費用:${results.expenses}行、マスター:${results.master}行）`,
      results: results
    };
    
  } catch (error) {
    console.error('全データクリアエラー:', error);
    return {
      success: false,
      message: `全データクリアに失敗しました: ${error.toString()}`
    };
  }
}

/**
 * 簡単なスプレッドシート状態確認（修正版）
 */
function debugSpreadsheetStatus() {
  try {
    console.log('=== 簡単なスプレッドシート状態確認開始 ===');
    
    // スプレッドシートIDの確認
    if (!SPREADSHEET_ID || SPREADSHEET_ID === 'YOUR_SPREADSHEET_ID_HERE') {
      return {
        success: false,
        error: 'スプレッドシートIDが設定されていません',
        solution: 'Code.gsのSPREADSHEET_IDを実際のスプレッドシートIDに変更してください'
      };
    }
    
    // スプレッドシートへのアクセス試行
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const spreadsheetName = ss.getName();
    const spreadsheetUrl = ss.getUrl();
    
    // シート一覧取得
    const sheets = ss.getSheets();
    const sheetInfo = sheets.map(sheet => ({
      name: sheet.getName(),
      rows: sheet.getLastRow(),
      columns: sheet.getLastColumn()
    }));
    
    console.log('スプレッドシート情報取得成功:', {
      name: spreadsheetName,
      sheetCount: sheets.length,
      sheets: sheetInfo
    });
    
    return {
      success: true,
      spreadsheetName: spreadsheetName,
      spreadsheetUrl: spreadsheetUrl,
      sheetCount: sheets.length,
      sheets: sheetInfo,
      message: 'スプレッドシートへのアクセスに成功しました'
    };
    
  } catch (error) {
    console.error('スプレッドシート状態確認エラー:', error);
    
    let errorMessage = error.toString();
    let solution = '不明なエラーです。技術サポートにお問い合わせください。';
    
    if (errorMessage.includes('No item with the given ID could be found')) {
      solution = 'スプレッドシートIDが無効です。正しいIDを確認してください。';
    } else if (errorMessage.includes('Permission denied')) {
      solution = 'スプレッドシートへのアクセス権限がありません。共有設定を確認してください。';
    } else if (errorMessage.includes('Service unavailable')) {
      solution = 'Googleサービスが一時的に利用できません。しばらく待ってから再試行してください。';
    }
    
    return {
      success: false,
      error: errorMessage,
      solution: solution,
      spreadsheetId: SPREADSHEET_ID
    };
  }
}

/**
 * スプレッドシートアクセス専用診断
 */
function diagnoseSpreadsheetAccess() {
  try {
    console.log('=== スプレッドシートアクセス診断開始 ===');
    
    const result = {
      step: 'スプレッドシートアクセス診断',
      checks: [],
      success: false,
      details: {}
    };
    
    // チェック1: スプレッドシートID設定確認
    result.checks.push({
      name: 'スプレッドシートID設定確認',
      success: SPREADSHEET_ID && SPREADSHEET_ID !== 'YOUR_SPREADSHEET_ID_HERE',
      value: SPREADSHEET_ID
    });
    
    if (!SPREADSHEET_ID || SPREADSHEET_ID === 'YOUR_SPREADSHEET_ID_HERE') {
      result.details.error = 'スプレッドシートIDが設定されていません';
      return result;
    }
    
    // チェック2: スプレッドシートアクセス
    try {
      const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
      result.checks.push({
        name: 'スプレッドシートアクセス',
        success: true,
        value: ss.getName()
      });
      result.details.spreadsheetName = ss.getName();
    } catch (accessError) {
      result.checks.push({
        name: 'スプレッドシートアクセス',
        success: false,
        error: accessError.toString()
      });
      result.details.error = accessError.toString();
      return result;
    }
    
    // チェック3: 必要なシートの存在確認
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const expectedSheets = Object.values(SHEET_NAMES);
    const actualSheets = ss.getSheets().map(sheet => sheet.getName());
    
    const missingSheets = expectedSheets.filter(sheetName => !actualSheets.includes(sheetName));
    
    result.checks.push({
      name: '必要なシートの存在確認',
      success: missingSheets.length === 0,
      expected: expectedSheets,
      actual: actualSheets,
      missing: missingSheets
    });
    
    result.details.sheetInfo = {
      expected: expectedSheets,
      actual: actualSheets,
      missing: missingSheets
    };
    
    // 総合判定
    result.success = result.checks.every(check => check.success);
    
    if (result.success) {
      result.details.message = 'スプレッドシートアクセスは正常です';
    } else {
      const failedChecks = result.checks.filter(check => !check.success);
      result.details.message = `${failedChecks.length}個のチェックが失敗しました`;
    }
    
    console.log('スプレッドシートアクセス診断結果:', result);
    return result;
    
  } catch (error) {
    console.error('スプレッドシートアクセス診断エラー:', error);
    return {
      success: false,
      error: error.toString(),
      step: 'スプレッドシートアクセス診断',
      details: {
        message: 'スプレッドシートアクセス診断中にエラーが発生しました'
      }
    };
  }
}

/**
 * データ取得テスト（軽量版）
 */
function testDataRetrieval() {
  try {
    console.log('=== データ取得テスト開始 ===');
    
    const results = {
      payments: null,
      expenses: null,
      master: null,
      overall: false
    };
    
    // 各データ取得をテスト
    try {
      const paymentResult = getPaymentData('');
      results.payments = {
        success: true,
        dataCount: paymentResult.data ? paymentResult.data.length : 0,
        hasData: paymentResult.data && paymentResult.data.length > 0
      };
    } catch (paymentError) {
      results.payments = {
        success: false,
        error: paymentError.toString()
      };
    }
    
    try {
      const expenseResult = getExpenseData('', '');
      results.expenses = {
        success: true,
        dataCount: expenseResult.data ? expenseResult.data.length : 0,
        hasData: expenseResult.data && expenseResult.data.length > 0
      };
    } catch (expenseError) {
      results.expenses = {
        success: false,
        error: expenseError.toString()
      };
    }
    
    try {
      const masterResult = getMasterData('');
      results.master = {
        success: true,
        dataCount: masterResult.data ? masterResult.data.length : 0,
        hasData: masterResult.data && masterResult.data.length > 0
      };
    } catch (masterError) {
      results.master = {
        success: false,
        error: masterError.toString()
      };
    }
    
    // 総合判定
    results.overall = results.payments.success && results.expenses.success && results.master.success;
    
    console.log('データ取得テスト結果:', results);
    
    return {
      success: results.overall,
      results: results,
      message: results.overall ? 'データ取得は正常です' : '一部のデータ取得に問題があります'
    };
    
  } catch (error) {
    console.error('データ取得テストエラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: 'データ取得テスト中にエラーが発生しました'
    };
  }
}

/**
 * システム基本情報取得
 */
function getSystemInfo() {
  try {
    const info = {
      timestamp: new Date(),
      spreadsheetId: SPREADSHEET_ID,
      sheetNames: Object.values(SHEET_NAMES),
      gasConfiguration: {
        timeZone: Session.getScriptTimeZone(),
        userEmail: Session.getActiveUser().getEmail(),
        locale: Session.getActiveUserLocale()
      }
    };
    
    // スプレッドシート情報（可能な場合）
    try {
      const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
      info.spreadsheet = {
        name: ss.getName(),
        url: ss.getUrl(),
        sheetCount: ss.getSheets().length,
        actualSheets: ss.getSheets().map(sheet => sheet.getName())
      };
    } catch (ssError) {
      info.spreadsheet = {
        accessible: false,
        error: ssError.toString()
      };
    }
    
    return {
      success: true,
      info: info,
      message: 'システム情報を取得しました'
    };
    
  } catch (error) {
    console.error('システム情報取得エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: 'システム情報の取得に失敗しました'
    };
  }
}

/**
 * 最小限のテストデータ作成（診断用）
 */
function createMinimalTestData() {
  try {
    console.log('=== 最小限のテストデータ作成開始 ===');
    
    // 費用マスターに1件のテストデータを作成
    const masterSheet = getOrCreateSheet(SHEET_NAMES.EXPENSE_MASTER);
    const testId = generateId();
    const testRow = [
      testId,
      '診断テスト案件',
      '診断テスト会社',
      'DIAG001',
      10000,
      '月額固定',
      '2024-01-01',
      '2024-12-31',
      '月',
      new Date()
    ];
    
    masterSheet.appendRow(testRow);
    
    return {
      success: true,
      testId: testId,
      message: '診断用テストデータを1件作成しました',
      data: {
        id: testId,
        projectName: '診断テスト案件',
        payee: '診断テスト会社'
      }
    };
    
  } catch (error) {
    console.error('最小限のテストデータ作成エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '診断用テストデータの作成に失敗しました'
    };
  }
}

/**
 * 診断用テストデータの削除
 */
function removeDiagnosticTestData() {
  try {
    console.log('=== 診断用テストデータ削除開始 ===');
    
    let deletedCount = 0;
    const sheetNames = [SHEET_NAMES.PAYMENTS, SHEET_NAMES.EXPENSES, SHEET_NAMES.EXPENSE_MASTER];
    
    sheetNames.forEach(sheetName => {
      try {
        const sheet = getOrCreateSheet(sheetName);
        const lastRow = sheet.getLastRow();
        
        if (lastRow > 1) {
          const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
          
          // 後ろから削除（行番号のずれを防ぐため）
          for (let i = data.length - 1; i >= 0; i--) {
            const row = data[i];
            const projectName = row[1] ? row[1].toString() : '';
            const payee = row[2] ? row[2].toString() : '';
            
            // 診断テストデータを識別
            if (projectName.includes('診断テスト') || payee.includes('診断テスト')) {
              sheet.deleteRow(i + 2); // +2は1行目がヘッダー、配列が0から始まるため
              deletedCount++;
              console.log(`診断テストデータを削除: ${projectName}`);
            }
          }
        }
      } catch (sheetError) {
        console.error(`${sheetName}の診断テストデータ削除エラー:`, sheetError);
      }
    });
    
    console.log('診断用テストデータ削除完了');
    
    return {
      success: true,
      deletedCount: deletedCount,
      message: `${deletedCount}件の診断用テストデータを削除しました`
    };
    
  } catch (error) {
    console.error('診断用テストデータ削除エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '診断用テストデータの削除に失敗しました'
    };
  }
}

/**
 * 完全診断（全項目チェック）
 */
function runCompleteDiagnostic() {
  try {
    console.log('=== 完全診断開始 ===');
    
    const diagnostic = {
      timestamp: new Date(),
      steps: [],
      summary: {
        totalSteps: 0,
        passedSteps: 0,
        failedSteps: 0,
        overallStatus: 'UNKNOWN'
      },
      recommendations: []
    };
    
    // ステップ1: システム情報取得
    console.log('ステップ1: システム情報取得');
    const systemInfo = getSystemInfo();
    diagnostic.steps.push({
      name: 'システム情報取得',
      success: systemInfo.success,
      result: systemInfo
    });
    
    // ステップ2: スプレッドシートアクセス診断
    console.log('ステップ2: スプレッドシートアクセス診断');
    const accessDiagnosis = diagnoseSpreadsheetAccess();
    diagnostic.steps.push({
      name: 'スプレッドシートアクセス',
      success: accessDiagnosis.success,
      result: accessDiagnosis
    });
    
    if (!accessDiagnosis.success) {
      diagnostic.recommendations.push('スプレッドシートIDと権限設定を確認してください');
      diagnostic.summary.overallStatus = 'SPREADSHEET_ACCESS_ERROR';
    }
    
    // ステップ3: データ取得テスト
    console.log('ステップ3: データ取得テスト');
    const dataTest = testDataRetrieval();
    diagnostic.steps.push({
      name: 'データ取得テスト',
      success: dataTest.success,
      result: dataTest
    });
    
    if (!dataTest.success) {
      diagnostic.recommendations.push('データ構造を確認し、初期化を実行してください');
    }
    
    // ステップ4: データ存在確認
    console.log('ステップ4: データ存在確認');
    const hasAnyData = dataTest.success && (
      (dataTest.results.payments && dataTest.results.payments.hasData) ||
      (dataTest.results.expenses && dataTest.results.expenses.hasData) ||
      (dataTest.results.master && dataTest.results.master.hasData)
    );
    
    diagnostic.steps.push({
      name: 'データ存在確認',
      success: hasAnyData,
      result: {
        hasData: hasAnyData,
        details: dataTest.success ? dataTest.results : null
      }
    });
    
    if (!hasAnyData) {
      diagnostic.recommendations.push('テストデータを作成するか、データをインポートしてください');
    }
    
    // サマリー計算
    diagnostic.summary.totalSteps = diagnostic.steps.length;
    diagnostic.summary.passedSteps = diagnostic.steps.filter(step => step.success).length;
    diagnostic.summary.failedSteps = diagnostic.summary.totalSteps - diagnostic.summary.passedSteps;
    
    // 総合ステータス判定
    if (diagnostic.summary.passedSteps === diagnostic.summary.totalSteps) {
      diagnostic.summary.overallStatus = hasAnyData ? 'ALL_SYSTEMS_GO' : 'READY_NO_DATA';
    } else if (accessDiagnosis.success) {
      diagnostic.summary.overallStatus = 'PARTIAL_SUCCESS';
    } else {
      diagnostic.summary.overallStatus = 'CRITICAL_ERROR';
    }
    
    console.log('完全診断結果:', diagnostic);
    
    return {
      success: true,
      diagnostic: diagnostic,
      message: `診断完了: ${diagnostic.summary.overallStatus}`
    };
    
  } catch (error) {
    console.error('完全診断エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '完全診断の実行中にエラーが発生しました'
    };
  }
}

/**
 * 緊急修復（自動的な問題解決を試行）
 */
function emergencyRepair() {
  try {
    console.log('=== 緊急修復開始 ===');
    
    const repairResults = {
      timestamp: new Date(),
      actions: [],
      success: false
    };
    
    // アクション1: シート構造の修復
    console.log('アクション1: シート構造の修復');
    try {
      const initResult = initializeSheets();
      repairResults.actions.push({
        name: 'シート構造修復',
        success: initResult.success,
        message: initResult.message
      });
    } catch (initError) {
      repairResults.actions.push({
        name: 'シート構造修復',
        success: false,
        error: initError.toString()
      });
    }
    
    // アクション2: テストデータ作成
    console.log('アクション2: テストデータ作成');
    try {
      const testDataResult = createMinimalTestData();
      repairResults.actions.push({
        name: 'テストデータ作成',
        success: testDataResult.success,
        message: testDataResult.message
      });
    } catch (testDataError) {
      repairResults.actions.push({
        name: 'テストデータ作成',
        success: false,
        error: testDataError.toString()
      });
    }
    
    // アクション3: データ取得確認
    console.log('アクション3: データ取得確認');
    try {
      const verifyResult = testDataRetrieval();
      repairResults.actions.push({
        name: 'データ取得確認',
        success: verifyResult.success,
        message: verifyResult.message
      });
    } catch (verifyError) {
      repairResults.actions.push({
        name: 'データ取得確認',
        success: false,
        error: verifyError.toString()
      });
    }
    
    // 総合判定
    const successfulActions = repairResults.actions.filter(action => action.success).length;
    repairResults.success = successfulActions >= 2; // 2つ以上のアクションが成功すれば修復成功
    
    console.log('緊急修復結果:', repairResults);
    
    return {
      success: repairResults.success,
      results: repairResults,
      message: repairResults.success ? 
        `緊急修復完了: ${successfulActions}/${repairResults.actions.length}個のアクションが成功` :
        `緊急修復失敗: ${successfulActions}/${repairResults.actions.length}個のアクションのみ成功`
    };
    
  } catch (error) {
    console.error('緊急修復エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '緊急修復の実行中にエラーが発生しました'
    };
  }
}

//Additional.gs に追加する支払いデータCSVインポート機能

/**
 * 支払いデータのCSVインポート（ヘッダーマッピング対応）
 */
function importPaymentsFromCsv(csvContent) {
  try {
    console.log('=== 支払いデータCSVインポート開始 ===');
    
    // ヘッダーマッピング設定
    const headerMapping = {
      // CSVヘッダー: システムヘッダー（インデックス）
      // 様々な表記に対応
      'ID': 0,
      'id': 0,
      '識別子': 0,
      '番号': 0,
      
      '件名': 1,
      'タイトル': 1,
      '題名': 1,
      'subject': 1,
      'Subject': 1,
      '内容': 1,
      
      '案件名': 2,
      'プロジェクト名': 2,
      'プロジェクト': 2,
      'project': 2,
      'Project': 2,
      '案件': 2,
      
      '支払い先': 3,
      '支払先': 3,
      '取引先': 3,
      '会社名': 3,
      '相手先': 3,
      'payee': 3,
      'Payee': 3,
      'company': 3,
      'Company': 3,
      '業者': 3,
      
      '支払い先コード': 4,
      '支払先コード': 4,
      '取引先コード': 4,
      '会社コード': 4,
      'code': 4,
      'Code': 4,
      'payee_code': 4,
      'PayeeCode': 4,
      'コード': 4,
      
      '金額': 5,
      '料金': 5,
      '価格': 5,
      '費用': 5,
      'amount': 5,
      'Amount': 5,
      'price': 5,
      'Price': 5,
      'cost': 5,
      'Cost': 5,
      
      '支払日': 6,
      '支払い日': 6,
      '決済日': 6,
      '日付': 6,
      'date': 6,
      'Date': 6,
      'payment_date': 6,
      'PaymentDate': 6,
      '実行日': 6,
      
      '状態': 7,
      'ステータス': 7,
      '処理状況': 7,
      'status': 7,
      'Status': 7,
      'state': 7,
      'State': 7
    };
    
    const lines = csvContent.trim().split(/\r?\n/);
    
    if (lines.length < 2) {
      throw new Error('CSVファイルが空または不正です');
    }
    
    const sheet = getOrCreateSheet(SHEET_NAMES.PAYMENTS);
    const csvHeaders = parseCSVLine(lines[0]);
    let importedCount = 0;
    let errorCount = 0;
    const errorDetails = [];
    
    console.log('CSVヘッダー:', csvHeaders);
    
    // ヘッダーマッピングを作成
    const columnMapping = createColumnMapping(csvHeaders, headerMapping);
    console.log('列マッピング:', columnMapping);
    
    // マッピングできなかった重要な列をチェック
    const requiredMappings = ['件名', '案件名', '支払い先', '金額', '支払日'];
    const missingMappings = [];
    
    requiredMappings.forEach(field => {
      const found = Object.keys(headerMapping).some(csvHeader => {
        if (headerMapping[csvHeader] === getSystemColumnIndex(field)) {
          return csvHeaders.some(h => h.toLowerCase().includes(csvHeader.toLowerCase()) || csvHeader.toLowerCase().includes(h.toLowerCase()));
        }
        return false;
      });
      if (!found) {
        missingMappings.push(field);
      }
    });
    
    if (missingMappings.length > 0) {
      console.warn('マッピングできない重要な列:', missingMappings);
    }
    
    // データ行を処理
    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].trim();
        if (!line) continue;
        
        const row = parseCSVLine(line);
        console.log(`支払いデータ行 ${i+1}:`, row);
        
        if (row.length < 3) {
          const error = `行 ${i+1}: 列数不足 (${row.length}列)`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        // マッピングに基づいてデータを抽出
        const mappedData = extractMappedData(row, columnMapping, csvHeaders);
        
        const newId = generateId();
        const subject = cleanString(mappedData.subject || `インポート件名${i}`);
        const projectName = cleanString(mappedData.projectName || `インポート案件${i}`);
        const payee = cleanString(mappedData.payee);
        const payeeCode = cleanString(mappedData.payeeCode);
        
        // 金額の変換
        let amount = 0;
        try {
          const amountStr = cleanString(mappedData.amount);
          if (amountStr) {
            amount = parseFloat(amountStr.replace(/[^\d.-]/g, ''));
            if (isNaN(amount)) {
              throw new Error(`金額が数値ではありません: "${amountStr}"`);
            }
          }
        } catch (amountError) {
          const error = `行 ${i+1}: 金額エラー - ${amountError.message}`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const paymentDate = cleanString(mappedData.paymentDate);
        const status = cleanString(mappedData.status) || '未処理';
        
        // 必須フィールドチェック
        if (!subject && !projectName) {
          const error = `行 ${i+1}: 件名または案件名が必要です`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        if (!payee) {
          const error = `行 ${i+1}: 支払い先が空です`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        const newRow = [
          newId,
          subject,
          projectName,
          payee,
          payeeCode,
          amount,
          paymentDate,
          status,
          new Date()
        ];
        
        console.log(`挿入予定データ:`, newRow);
        
        try {
          sheet.appendRow(newRow);
          importedCount++;
          console.log(`行 ${i+1}: 正常にインポート完了`);
        } catch (insertError) {
          const error = `行 ${i+1}: スプレッドシートへの挿入に失敗 - ${insertError.message}`;
          console.error(error);
          errorDetails.push(error);
          errorCount++;
        }
        
      } catch (parseError) {
        const error = `行 ${i+1}: 解析エラー - ${parseError.message}`;
        console.error(error);
        errorDetails.push(error);
        errorCount++;
      }
    }
    
    console.log('=== インポート結果 ===');
    console.log(`成功: ${importedCount}件`);
    console.log(`エラー: ${errorCount}件`);
    
    let message = `${importedCount}件の支払いデータをインポートしました`;
    if (errorCount > 0) {
      message += ` (エラー: ${errorCount}件)`;
    }
    
    if (missingMappings.length > 0) {
      message += `\n注意: 一部の列がマッピングできませんでした (${missingMappings.join(', ')})`;
    }
    
    return { 
      success: true, 
      count: importedCount, 
      errorCount: errorCount,
      errorDetails: errorDetails.slice(0, 10),
      missingMappings: missingMappings,
      message: message
    };
  } catch (error) {
    console.error('支払いデータCSVインポートエラー:', error);
    return { 
      success: false, 
      message: `インポートエラー: ${error.toString()}`,
      errorDetails: [error.toString()]
    };
  }
}

/**
 * 列マッピングを作成
 */
function createColumnMapping(csvHeaders, headerMapping) {
  const mapping = {};
  
  csvHeaders.forEach((csvHeader, index) => {
    const cleanHeader = csvHeader.trim();
    
    // 完全一致を優先
    if (headerMapping.hasOwnProperty(cleanHeader)) {
      const systemIndex = headerMapping[cleanHeader];
      const systemField = getSystemFieldName(systemIndex);
      mapping[systemField] = index;
      console.log(`完全一致: "${cleanHeader}" -> ${systemField} (CSV列${index})`);
      return;
    }
    
    // 部分一致をチェック
    for (const [mappingKey, systemIndex] of Object.entries(headerMapping)) {
      if (cleanHeader.toLowerCase().includes(mappingKey.toLowerCase()) || 
          mappingKey.toLowerCase().includes(cleanHeader.toLowerCase())) {
        const systemField = getSystemFieldName(systemIndex);
        if (!mapping[systemField]) { // 既にマッピングされていない場合のみ
          mapping[systemField] = index;
          console.log(`部分一致: "${cleanHeader}" -> ${systemField} (CSV列${index})`);
          break;
        }
      }
    }
  });
  
  return mapping;
}

/**
 * システムフィールド名を取得
 */
function getSystemFieldName(index) {
  const fieldNames = ['id', 'subject', 'projectName', 'payee', 'payeeCode', 'amount', 'paymentDate', 'status'];
  return fieldNames[index] || `field${index}`;
}

/**
 * システム列インデックスを取得
 */
function getSystemColumnIndex(fieldName) {
  const indexMap = {
    'ID': 0,
    '件名': 1,
    '案件名': 2,
    '支払い先': 3,
    '支払い先コード': 4,
    '金額': 5,
    '支払日': 6,
    '状態': 7
  };
  return indexMap[fieldName] || -1;
}

/**
 * マッピングされたデータを抽出
 */
function extractMappedData(row, columnMapping, csvHeaders) {
  const data = {};
  
  // マッピングに基づいてデータを抽出
  Object.keys(columnMapping).forEach(systemField => {
    const csvColumnIndex = columnMapping[systemField];
    if (csvColumnIndex < row.length) {
      data[systemField] = row[csvColumnIndex];
      console.log(`マッピング: ${systemField} = "${row[csvColumnIndex]}" (CSV列${csvColumnIndex}: "${csvHeaders[csvColumnIndex]}")`);
    }
  });
  
  // マッピングされなかったフィールドのデフォルト処理
  if (!data.subject && !data.projectName) {
    // 件名も案件名もない場合、最初の文字列列を使用
    for (let i = 0; i < row.length; i++) {
      if (row[i] && typeof row[i] === 'string' && row[i].trim()) {
        data.subject = row[i];
        console.log(`デフォルト件名設定: "${row[i]}" (CSV列${i})`);
        break;
      }
    }
  }
  
  if (!data.payee) {
    // 支払い先がない場合、会社名らしき列を探す
    for (let i = 0; i < row.length; i++) {
      const value = row[i];
      if (value && typeof value === 'string' && 
          (value.includes('株式会社') || value.includes('有限会社') || value.includes('合同会社') || 
           value.includes('Corp') || value.includes('Ltd') || value.includes('Inc'))) {
        data.payee = value;
        console.log(`推測支払い先設定: "${value}" (CSV列${i})`);
        break;
      }
    }
  }
  
  if (!data.amount) {
    // 金額がない場合、数値らしき列を探す
    for (let i = 0; i < row.length; i++) {
      const value = row[i];
      if (value && !isNaN(parseFloat(value.toString().replace(/[^\d.-]/g, '')))) {
        const numValue = parseFloat(value.toString().replace(/[^\d.-]/g, ''));
        if (numValue > 0) {
          data.amount = value;
          console.log(`推測金額設定: "${value}" (CSV列${i})`);
          break;
        }
      }
    }
  }
  
  return data;
}

/**
 * カスタムヘッダーマッピング設定（必要に応じてカスタマイズ）
 */
function setCustomPaymentHeaderMapping(customMapping) {
  // この関数を使って、特定のCSVファイル用のマッピングを設定可能
  // 例: setCustomPaymentHeaderMapping({'請求書番号': 0, '会社': 3, '請求額': 5});
  
  if (typeof customMapping === 'object') {
    // グローバル変数やPropertiesServiceに保存してimportPaymentsFromCsvで使用
    PropertiesService.getScriptProperties().setProperty('customPaymentMapping', JSON.stringify(customMapping));
    return { success: true, message: 'カスタムマッピングを設定しました' };
  }
  
  return { success: false, message: 'マッピング設定が不正です' };
}

/**
 * ヘッダーマッピング状況を診断
 */
function diagnosePaymentCsvMapping(csvContent) {
  try {
    const lines = csvContent.trim().split(/\r?\n/);
    if (lines.length < 1) {
      return { success: false, message: 'CSVファイルが空です' };
    }
    
    const csvHeaders = parseCSVLine(lines[0]);
    console.log('CSVヘッダー分析:', csvHeaders);
    
    // デフォルトマッピングをテスト
    const headerMapping = {
      '件名': 1, 'タイトル': 1, 'subject': 1,
      '案件名': 2, 'プロジェクト': 2, 'project': 2,
      '支払い先': 3, '会社名': 3, 'payee': 3, 'company': 3,
      '支払い先コード': 4, 'コード': 4, 'code': 4,
      '金額': 5, '料金': 5, 'amount': 5, 'price': 5,
      '支払日': 6, '日付': 6, 'date': 6,
      '状態': 7, 'ステータス': 7, 'status': 7
    };
    
    const mapping = createColumnMapping(csvHeaders, headerMapping);
    
    const diagnosis = {
      csvHeaders: csvHeaders,
      detectedMapping: mapping,
      recommendedMapping: {},
      unmappedColumns: [],
      suggestions: []
    };
    
    // マッピングされなかった列を特定
    csvHeaders.forEach((header, index) => {
      const isMapped = Object.values(mapping).includes(index);
      if (!isMapped) {
        diagnosis.unmappedColumns.push({ index: index, header: header });
      }
    });
    
    // 推奨マッピングを生成
    diagnosis.recommendedMapping = generateRecommendedMapping(csvHeaders);
    
    // 改善提案を生成
    if (diagnosis.unmappedColumns.length > 0) {
      diagnosis.suggestions.push('一部の列がマッピングされていません。手動でマッピングを確認してください。');
    }
    
    if (Object.keys(mapping).length < 4) {
      diagnosis.suggestions.push('重要な列（件名、案件名、支払い先、金額）が不足している可能性があります。');
    }
    
    return {
      success: true,
      diagnosis: diagnosis,
      message: `ヘッダー分析完了: ${csvHeaders.length}列中${Object.keys(mapping).length}列をマッピング`
    };
    
  } catch (error) {
    return {
      success: false,
      message: `ヘッダー分析エラー: ${error.toString()}`
    };
  }
}

/**
 * 推奨マッピングを生成
 */
function generateRecommendedMapping(csvHeaders) {
  const recommendations = {};
  
  csvHeaders.forEach((header, index) => {
    const lowerHeader = header.toLowerCase();
    
    if (lowerHeader.includes('件名') || lowerHeader.includes('title') || lowerHeader.includes('subject')) {
      recommendations['件名'] = index;
    } else if (lowerHeader.includes('案件') || lowerHeader.includes('project') || lowerHeader.includes('プロジェクト')) {
      recommendations['案件名'] = index;
    } else if (lowerHeader.includes('支払') || lowerHeader.includes('会社') || lowerHeader.includes('payee') || lowerHeader.includes('company')) {
      recommendations['支払い先'] = index;
    } else if (lowerHeader.includes('コード') || lowerHeader.includes('code')) {
      recommendations['支払い先コード'] = index;
    } else if (lowerHeader.includes('金額') || lowerHeader.includes('料金') || lowerHeader.includes('amount') || lowerHeader.includes('price')) {
      recommendations['金額'] = index;
    } else if (lowerHeader.includes('日付') || lowerHeader.includes('date') || lowerHeader.includes('日')) {
      recommendations['支払日'] = index;
    } else if (lowerHeader.includes('状態') || lowerHeader.includes('status') || lowerHeader.includes('ステータス')) {
      recommendations['状態'] = index;
    }
  });
  
  return recommendations;
}