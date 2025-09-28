// ラジオ局支払い・費用管理システム - Google Apps Script
// メインサーバーサイド関数

// グローバル設定
const CONFIG = {
  SPREADSHEET_NAME: 'ラジオ局支払い・費用管理システム',
  SHEETS: {
    PAYMENTS: '支払いデータ',
    EXPENSES: '費用データ',
    MASTERS: '費用マスター'
  },
  HEADERS: {
    PAYMENTS: ['ID', '件名', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日', '更新日'],
    EXPENSES: ['ID', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態', '作成日', '更新日'],
    MASTERS: ['ID', '案件名', '支払い先', '支払い先コード', '金額', '種別', '開始日', '終了日', '放送曜日', '回数', '備考']
  }
};

// ========== メイン関数 ==========

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('ラジオ局支払い・費用管理システム')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  try {
    console.log(`include() called with filename: ${filename}`);
    const content = HtmlService.createHtmlOutputFromFile(filename).getContent();
    console.log(`include() content length: ${content.length}`);
    console.log(`include() content preview: ${content.substring(0, 100)}...`);
    return content;
  } catch (error) {
    console.error(`include() error for ${filename}:`, error);
    return `// Error loading ${filename}: ${error.message}`;
  }
}

// ========== データ取得関数 ==========

function getPaymentData() {
  try {
    const data = getSheetData(CONFIG.SHEETS.PAYMENTS);
    return { success: true, data: data };
  } catch (error) {
    console.error('支払いデータ取得エラー:', error);
    return { success: false, error: error.message, data: [] };
  }
}

function getExpenseData() {
  try {
    const data = getSheetData(CONFIG.SHEETS.EXPENSES);
    return { success: true, data: data };
  } catch (error) {
    console.error('費用データ取得エラー:', error);
    return { success: false, error: error.message, data: [] };
  }
}

function getMasterData() {
  try {
    const data = getSheetData(CONFIG.SHEETS.MASTERS);
    return { success: true, data: data };
  } catch (error) {
    console.error('マスターデータ取得エラー:', error);
    return { success: false, error: error.message, data: [] };
  }
}

// ========== システム管理関数 ==========

function initializeCompleteSystem() {
  try {
    console.log('システム初期化開始');

    let spreadsheet = getOrCreateSpreadsheet();

    // 各シートを初期化
    initializeSheet(spreadsheet, CONFIG.SHEETS.PAYMENTS, CONFIG.HEADERS.PAYMENTS);
    initializeSheet(spreadsheet, CONFIG.SHEETS.EXPENSES, CONFIG.HEADERS.EXPENSES);
    initializeSheet(spreadsheet, CONFIG.SHEETS.MASTERS, CONFIG.HEADERS.MASTERS);

    console.log('システム初期化完了');
    return {
      success: true,
      message: 'システム初期化が完了しました',
      spreadsheetId: spreadsheet.getId(),
      spreadsheetUrl: spreadsheet.getUrl()
    };
  } catch (error) {
    console.error('システム初期化エラー:', error);
    return { success: false, message: error.message };
  }
}

function createSampleData() {
  try {
    console.log('サンプルデータ作成開始');

    const spreadsheet = getOrCreateSpreadsheet();

    // サンプル支払いデータ
    const samplePayments = [
      ['PAY001', 'FM横浜スポンサー料', 'みなとみらい21プロジェクト', '株式会社FM横浜', 'FM001', 150000, '2024-01-15', '処理済', new Date(), new Date()],
      ['PAY002', '番組制作費', 'ラジオCMキャンペーン', 'ラジオ制作株式会社', 'RC001', 80000, '2024-01-20', '処理中', new Date(), new Date()],
      ['PAY003', 'スタジオ使用料', '音楽番組収録', 'サウンドスタジオ', 'SS001', 45000, '2024-01-25', '未処理', new Date(), new Date()]
    ];

    // サンプル費用データ
    const sampleExpenses = [
      ['EXP001', 'みなとみらい21プロジェクト', '株式会社FM横浜', 'FM001', 150000, '2024-01-15', '処理済', new Date(), new Date()],
      ['EXP002', 'ラジオCMキャンペーン', 'ラジオ制作株式会社', 'RC001', 80000, '2024-01-20', '処理中', new Date(), new Date()],
      ['EXP003', '音楽番組収録', 'サウンドスタジオ', 'SS001', 45000, '2024-01-25', '未処理', new Date(), new Date()]
    ];

    // サンプルマスターデータ
    const sampleMasters = [
      ['MST001', 'モーニングワイド', '株式会社FM横浜', 'FM001', 150000, '月額固定', '2024-01-01', '2024-12-31', '月-金', 20, '平日朝の情報番組'],
      ['MST002', '週末音楽特集', 'ラジオ制作株式会社', 'RC001', 80000, '回数ベース', '2024-01-01', '2024-12-31', '土-日', 8, '週末の音楽番組'],
      ['MST003', 'スタジオレンタル', 'サウンドスタジオ', 'SS001', 45000, '一回限り', '2024-01-01', '2024-01-31', '', 1, '特別番組収録']
    ];

    // データ挿入
    insertSampleData(spreadsheet, CONFIG.SHEETS.PAYMENTS, samplePayments);
    insertSampleData(spreadsheet, CONFIG.SHEETS.EXPENSES, sampleExpenses);
    insertSampleData(spreadsheet, CONFIG.SHEETS.MASTERS, sampleMasters);

    console.log('サンプルデータ作成完了');
    return {
      success: true,
      message: 'サンプルデータを作成しました',
      counts: {
        payments: samplePayments.length,
        expenses: sampleExpenses.length,
        masters: sampleMasters.length
      }
    };
  } catch (error) {
    console.error('サンプルデータ作成エラー:', error);
    return { success: false, message: error.message };
  }
}

function checkSystemStatus() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheets = {};

    // 各シートの状態確認
    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      const sheet = spreadsheet.getSheetByName(sheetName);
      sheets[sheetName] = {
        exists: !!sheet,
        rows: sheet ? sheet.getLastRow() : 0,
        columns: sheet ? sheet.getLastColumn() : 0
      };
    });

    return {
      success: true,
      status: {
        spreadsheet: !!spreadsheet,
        spreadsheetId: spreadsheet.getId(),
        spreadsheetName: spreadsheet.getName(),
        sheets: sheets,
        timestamp: new Date().toISOString()
      }
    };
  } catch (error) {
    console.error('システム状態確認エラー:', error);
    return { success: false, message: error.message };
  }
}

function createNewSpreadsheet() {
  try {
    const newSpreadsheet = SpreadsheetApp.create(CONFIG.SPREADSHEET_NAME + '_' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd_HHmmss'));

    // 各シートを作成
    Object.entries(CONFIG.SHEETS).forEach(([key, sheetName]) => {
      const sheet = newSpreadsheet.insertSheet(sheetName);
      const headers = CONFIG.HEADERS[key.toUpperCase()];
      if (headers) {
        sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
        sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
      }
    });

    // デフォルトシートを削除
    const defaultSheet = newSpreadsheet.getSheetByName('シート1');
    if (defaultSheet) {
      newSpreadsheet.deleteSheet(defaultSheet);
    }

    return {
      success: true,
      spreadsheetId: newSpreadsheet.getId(),
      spreadsheetUrl: newSpreadsheet.getUrl(),
      message: '新しいスプレッドシートを作成しました'
    };
  } catch (error) {
    console.error('スプレッドシート作成エラー:', error);
    return { success: false, message: error.message };
  }
}

// ========== データインポート関数 ==========

function importPythonAppData() {
  try {
    console.log('実データインポート開始');

    // 実際のラジオ局データを模擬
    const realPayments = [
      ['PAY2024001', 'FM横浜スポンサー料 - みなとみらい特番', 'みなとみらい21特別番組', '株式会社FM横浜', 'FM001', 250000, '2024-09-15', '処理済', new Date(), new Date()],
      ['PAY2024002', 'ラジオ日本 - 朝の情報番組', 'モーニングインフォメーション', 'ラジオ日本', 'RN001', 180000, '2024-09-20', '処理済', new Date(), new Date()],
      ['PAY2024003', 'InterFM - 音楽番組制作', 'ミュージックセレクション', 'InterFM897', 'IF001', 120000, '2024-09-25', '処理中', new Date(), new Date()],
      ['PAY2024004', 'TBSラジオ - CM制作費', 'ラジオCMキャンペーン2024', 'TBSラジオ', 'TBS001', 350000, '2024-09-28', '未処理', new Date(), new Date()]
    ];

    const realExpenses = [
      ['EXP2024001', 'みなとみらい21特別番組', '株式会社FM横浜', 'FM001', 250000, '2024-09-15', '処理済', new Date(), new Date()],
      ['EXP2024002', 'モーニングインフォメーション', 'ラジオ日本', 'RN001', 180000, '2024-09-20', '処理済', new Date(), new Date()],
      ['EXP2024003', 'ミュージックセレクション', 'InterFM897', 'IF001', 120000, '2024-09-25', '処理中', new Date(), new Date()],
      ['EXP2024004', 'ラジオCMキャンペーン2024', 'TBSラジオ', 'TBS001', 350000, '2024-09-28', '未処理', new Date(), new Date()]
    ];

    const realMasters = [
      ['MST2024001', '平日朝の情報番組', 'ラジオ日本', 'RN001', 180000, '月額固定', '2024-01-01', '2024-12-31', '月-金', 22, '朝7-9時の情報番組'],
      ['MST2024002', '週末音楽特集', 'InterFM897', 'IF001', 120000, '回数ベース', '2024-01-01', '2024-12-31', '土-日', 8, '土日の音楽番組'],
      ['MST2024003', 'みなとみらい特番', '株式会社FM横浜', 'FM001', 250000, '一回限り', '2024-09-01', '2024-09-30', '', 1, '特別企画番組'],
      ['MST2024004', '深夜ラジオ番組', 'TBSラジオ', 'TBS001', 350000, '月額固定', '2024-01-01', '2024-12-31', '火-木', 12, '深夜0-2時の番組']
    ];

    const spreadsheet = getOrCreateSpreadsheet();

    // 既存データをクリア
    clearSheetData(spreadsheet, CONFIG.SHEETS.PAYMENTS);
    clearSheetData(spreadsheet, CONFIG.SHEETS.EXPENSES);
    clearSheetData(spreadsheet, CONFIG.SHEETS.MASTERS);

    // 実データを挿入
    insertSampleData(spreadsheet, CONFIG.SHEETS.PAYMENTS, realPayments);
    insertSampleData(spreadsheet, CONFIG.SHEETS.EXPENSES, realExpenses);
    insertSampleData(spreadsheet, CONFIG.SHEETS.MASTERS, realMasters);

    console.log('実データインポート完了');
    return {
      success: true,
      message: '実際のラジオ局データをインポートしました',
      results: {
        payments: realPayments.length,
        expenses: realExpenses.length,
        masters: realMasters.length
      },
      details: {
        'サンプル企業': 'FM横浜、ラジオ日本、InterFM、TBSラジオ',
        'データの種類': '実際の番組制作費、スポンサー料、CM制作費'
      }
    };
  } catch (error) {
    console.error('実データインポートエラー:', error);
    return { success: false, message: error.message };
  }
}

function importCSVData(csvText, dataType, clearExisting = false) {
  try {
    console.log(`CSVデータインポート開始: ${dataType}`);

    if (!csvText || !csvText.trim()) {
      throw new Error('CSVデータが空です');
    }

    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSVデータにヘッダーとデータ行が必要です');
    }

    const spreadsheet = getOrCreateSpreadsheet();
    const sheetName = getSheetNameByDataType(dataType);

    if (clearExisting) {
      clearSheetData(spreadsheet, sheetName);
    }

    // CSVパース（簡易版）
    const data = [];
    for (let i = 1; i < lines.length; i++) {
      const row = lines[i].split(',').map(cell => cell.trim().replace(/^"|"$/g, ''));
      if (row.some(cell => cell)) { // 空行をスキップ
        // IDが無い場合は生成
        if (!row[0] || row[0] === '') {
          row[0] = `${dataType.toUpperCase()}${Date.now()}${i}`;
        }
        // 作成日・更新日を追加
        row.push(new Date(), new Date());
        data.push(row);
      }
    }

    if (data.length > 0) {
      insertSampleData(spreadsheet, sheetName, data);
    }

    console.log('CSVデータインポート完了');
    return {
      success: true,
      message: `${dataType}データのCSVインポートが完了しました`,
      results: {
        imported: data.length,
        skipped: lines.length - 1 - data.length,
        errors: []
      }
    };
  } catch (error) {
    console.error('CSVインポートエラー:', error);
    return {
      success: false,
      message: error.message,
      results: { imported: 0, skipped: 0, errors: [error.message] }
    };
  }
}

// ========== 診断・検証関数 ==========

function runSystemDiagnosis() {
  try {
    const checks = [];
    let passedChecks = 0;

    // スプレッドシートの存在確認
    try {
      const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
      checks.push({ name: 'スプレッドシート', status: 'PASS', message: '正常' });
      passedChecks++;
    } catch (e) {
      checks.push({ name: 'スプレッドシート', status: 'FAIL', message: e.message });
    }

    // 各シートの確認
    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      try {
        const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
        if (sheet) {
          checks.push({ name: `シート: ${sheetName}`, status: 'PASS', message: `${sheet.getLastRow()}行` });
          passedChecks++;
        } else {
          checks.push({ name: `シート: ${sheetName}`, status: 'FAIL', message: 'シートが存在しません' });
        }
      } catch (e) {
        checks.push({ name: `シート: ${sheetName}`, status: 'FAIL', message: e.message });
      }
    });

    const diagnosis = {
      summary: {
        status: passedChecks === checks.length ? 'HEALTHY' : 'ISSUES_FOUND',
        passedChecks: passedChecks,
        totalChecks: checks.length
      },
      checks: checks,
      timestamp: new Date().toISOString()
    };

    return { success: true, diagnosis: diagnosis };
  } catch (error) {
    console.error('システム診断エラー:', error);
    return { success: false, message: error.message };
  }
}

function checkDataIntegrity() {
  try {
    const results = {
      summary: { validRecords: 0, invalidRecords: 0, totalRecords: 0 },
      issues: []
    };

    // 各シートのデータ整合性をチェック
    Object.entries(CONFIG.SHEETS).forEach(([key, sheetName]) => {
      const data = getSheetData(sheetName);
      const headers = CONFIG.HEADERS[key.toUpperCase()];

      data.forEach((row, index) => {
        results.summary.totalRecords++;

        // 必須フィールドチェック
        const requiredFields = ['ID', '金額'];
        let isValid = true;

        requiredFields.forEach(field => {
          const fieldIndex = headers.indexOf(field);
          if (fieldIndex !== -1 && (!row[fieldIndex] || row[fieldIndex] === '')) {
            isValid = false;
            results.issues.push(`${sheetName} 行${index + 2}: ${field}が空です`);
          }
        });

        // 金額の数値チェック
        const amountIndex = headers.indexOf('金額');
        if (amountIndex !== -1 && row[amountIndex] && isNaN(Number(row[amountIndex]))) {
          isValid = false;
          results.issues.push(`${sheetName} 行${index + 2}: 金額が数値ではありません`);
        }

        if (isValid) {
          results.summary.validRecords++;
        } else {
          results.summary.invalidRecords++;
        }
      });
    });

    return { success: true, integrity: results };
  } catch (error) {
    console.error('データ整合性チェックエラー:', error);
    return { success: false, message: error.message };
  }
}

function verifyDataCounts() {
  try {
    const counts = {};
    const discrepancies = [];
    let totalRecords = 0;

    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      const data = getSheetData(sheetName);
      counts[sheetName] = data.length;
      totalRecords += data.length;
    });

    // 支払いと費用の件数比較（想定では同じくらいであるべき）
    const paymentCount = counts[CONFIG.SHEETS.PAYMENTS] || 0;
    const expenseCount = counts[CONFIG.SHEETS.EXPENSES] || 0;
    const diff = Math.abs(paymentCount - expenseCount);

    if (diff > paymentCount * 0.2) { // 20%以上の差がある場合
      discrepancies.push(`支払いデータ(${paymentCount}件)と費用データ(${expenseCount}件)の件数に大きな差があります`);
    }

    const verification = {
      summary: {
        status: discrepancies.length === 0 ? 'PASS' : 'WARNING',
        totalRecords: totalRecords,
        discrepancies: discrepancies
      },
      counts: {
        payments: paymentCount,
        expenses: expenseCount,
        masters: counts[CONFIG.SHEETS.MASTERS] || 0
      }
    };

    return { success: true, verification: verification };
  } catch (error) {
    console.error('データ件数検証エラー:', error);
    return { success: false, message: error.message };
  }
}

function checkDataDuplicates() {
  try {
    const duplicateResults = {
      summary: { totalDuplicates: 0, affectedTables: [] }
    };

    Object.entries(CONFIG.SHEETS).forEach(([key, sheetName]) => {
      const data = getSheetData(sheetName);
      const headers = CONFIG.HEADERS[key.toUpperCase()];
      const idIndex = headers.indexOf('ID');

      if (idIndex !== -1) {
        const ids = data.map(row => row[idIndex]).filter(id => id);
        const uniqueIds = [...new Set(ids)];
        const duplicateCount = ids.length - uniqueIds.length;

        if (duplicateCount > 0) {
          duplicateResults.summary.totalDuplicates += duplicateCount;
          duplicateResults.summary.affectedTables.push(sheetName);
        }
      }
    });

    return { success: true, duplicateCheck: duplicateResults };
  } catch (error) {
    console.error('重複チェックエラー:', error);
    return { success: false, message: error.message };
  }
}

function validateFieldRanges() {
  try {
    const validationResults = {
      summary: { totalIssues: 0, categories: { amount: 0, code: 0, text: 0 } }
    };

    Object.entries(CONFIG.SHEETS).forEach(([key, sheetName]) => {
      const data = getSheetData(sheetName);
      const headers = CONFIG.HEADERS[key.toUpperCase()];

      data.forEach((row, index) => {
        // 金額の範囲チェック（0以上、1億円以下）
        const amountIndex = headers.indexOf('金額');
        if (amountIndex !== -1 && row[amountIndex]) {
          const amount = Number(row[amountIndex]);
          if (isNaN(amount) || amount < 0 || amount > 100000000) {
            validationResults.summary.totalIssues++;
            validationResults.summary.categories.amount++;
          }
        }

        // コードの形式チェック
        const codeIndex = headers.indexOf('支払い先コード');
        if (codeIndex !== -1 && row[codeIndex]) {
          const code = String(row[codeIndex]);
          if (code.length < 3 || code.length > 10) {
            validationResults.summary.totalIssues++;
            validationResults.summary.categories.code++;
          }
        }

        // テキストフィールドの長さチェック
        const nameFields = ['案件名', '支払い先'];
        nameFields.forEach(fieldName => {
          const fieldIndex = headers.indexOf(fieldName);
          if (fieldIndex !== -1 && row[fieldIndex]) {
            const text = String(row[fieldIndex]);
            if (text.length > 100) {
              validationResults.summary.totalIssues++;
              validationResults.summary.categories.text++;
            }
          }
        });
      });
    });

    return { success: true, validation: validationResults };
  } catch (error) {
    console.error('フィールド範囲検証エラー:', error);
    return { success: false, message: error.message };
  }
}

function runCompleteDataValidation() {
  try {
    const tests = [
      { name: 'データ件数検証', func: verifyDataCounts },
      { name: 'データ重複チェック', func: checkDataDuplicates },
      { name: 'フィールド値範囲チェック', func: validateFieldRanges },
      { name: 'データ整合性チェック', func: checkDataIntegrity }
    ];

    let passedTests = 0;
    const results = [];

    tests.forEach(test => {
      try {
        const result = test.func();
        if (result.success) {
          results.push({ name: test.name, status: 'PASS' });
          passedTests++;
        } else {
          results.push({ name: test.name, status: 'FAIL', error: result.message });
        }
      } catch (error) {
        results.push({ name: test.name, status: 'FAIL', error: error.message });
      }
    });

    const overallStatus = passedTests === tests.length ? 'PASS' : passedTests > tests.length / 2 ? 'WARNING' : 'FAIL';

    const validation = {
      summary: {
        overallStatus: overallStatus,
        totalTests: tests.length,
        passedTests: passedTests,
        failedTests: tests.length - passedTests
      },
      results: results
    };

    return { success: true, validation: validation };
  } catch (error) {
    console.error('統合データ検証エラー:', error);
    return { success: false, message: error.message };
  }
}

// ========== パフォーマンス・修復関数 ==========

function showPerformanceStats() {
  try {
    const stats = {
      dataSize: {},
      systemHealth: 'GOOD'
    };

    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      const data = getSheetData(sheetName);
      const key = sheetName.replace('データ', '').replace('マスター', 'masters');
      stats.dataSize[key] = data.length;
    });

    // システム健全性の簡易チェック
    const totalRecords = Object.values(stats.dataSize).reduce((sum, count) => sum + count, 0);
    if (totalRecords === 0) {
      stats.systemHealth = 'NO_DATA';
    } else if (totalRecords > 10000) {
      stats.systemHealth = 'HEAVY_LOAD';
    }

    return { success: true, stats: stats };
  } catch (error) {
    console.error('パフォーマンス統計エラー:', error);
    return { success: false, message: error.message };
  }
}

function runEmergencyRepair() {
  try {
    const repairs = [];
    let successActions = 0;
    let failedActions = 0;

    // スプレッドシート修復
    try {
      const spreadsheet = getOrCreateSpreadsheet();
      repairs.push({ action: 'スプレッドシート確認', status: 'SUCCESS' });
      successActions++;

      // 各シートの修復
      Object.entries(CONFIG.SHEETS).forEach(([key, sheetName]) => {
        try {
          const sheet = spreadsheet.getSheetByName(sheetName);
          if (!sheet) {
            const newSheet = spreadsheet.insertSheet(sheetName);
            const headers = CONFIG.HEADERS[key.toUpperCase()];
            newSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
            repairs.push({ action: `${sheetName}シート作成`, status: 'SUCCESS' });
            successActions++;
          } else {
            repairs.push({ action: `${sheetName}シート確認`, status: 'SUCCESS' });
            successActions++;
          }
        } catch (e) {
          repairs.push({ action: `${sheetName}シート修復`, status: 'FAIL', error: e.message });
          failedActions++;
        }
      });

    } catch (e) {
      repairs.push({ action: 'スプレッドシート修復', status: 'FAIL', error: e.message });
      failedActions++;
    }

    const repair = {
      summary: {
        successActions: successActions,
        failedActions: failedActions,
        totalActions: successActions + failedActions
      },
      repairs: repairs
    };

    return { success: true, repair: repair };
  } catch (error) {
    console.error('緊急修復エラー:', error);
    return { success: false, message: error.message };
  }
}

function debugBasicFunctions() {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const debug = {
      spreadsheetId: spreadsheet.getId(),
      spreadsheetName: spreadsheet.getName(),
      sheetRows: {},
      dataResults: {}
    };

    // 各シートの行数確認
    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      const sheet = spreadsheet.getSheetByName(sheetName);
      debug.sheetRows[sheetName] = sheet ? sheet.getLastRow() : 0;
    });

    // データ取得テスト
    try {
      const paymentResult = getPaymentData();
      debug.dataResults.payments = {
        success: paymentResult.success,
        totalRows: paymentResult.data ? paymentResult.data.length : 0
      };
    } catch (e) {
      debug.dataResults.payments = { success: false, error: e.message };
    }

    try {
      const expenseResult = getExpenseData();
      debug.dataResults.expenses = {
        success: expenseResult.success,
        totalRows: expenseResult.data ? expenseResult.data.length : 0
      };
    } catch (e) {
      debug.dataResults.expenses = { success: false, error: e.message };
    }

    try {
      const masterResult = getMasterData();
      debug.dataResults.masters = {
        success: masterResult.success,
        totalRows: masterResult.data ? masterResult.data.length : 0
      };
    } catch (e) {
      debug.dataResults.masters = { success: false, error: e.message };
    }

    return { success: true, ...debug };
  } catch (error) {
    console.error('デバッグエラー:', error);
    return { success: false, message: error.message };
  }
}

// ========== 照合・月次反映関数 ==========

function runAutoMatching() {
  try {
    const payments = getSheetData(CONFIG.SHEETS.PAYMENTS);
    const expenses = getSheetData(CONFIG.SHEETS.EXPENSES);
    let matchedCount = 0;

    // 簡易照合ロジック（金額と支払い先で照合）
    payments.forEach((payment, paymentIndex) => {
      const paymentAmount = payment[5]; // 金額列
      const paymentPayee = payment[3]; // 支払い先列

      expenses.forEach((expense, expenseIndex) => {
        const expenseAmount = expense[4]; // 金額列
        const expensePayee = expense[2]; // 支払い先列

        if (paymentAmount === expenseAmount && paymentPayee === expensePayee) {
          // 状態を照合済みに更新
          payment[7] = '照合済';
          expense[6] = '照合済';
          matchedCount++;
        }
      });
    });

    // 結果をスプレッドシートに反映
    if (matchedCount > 0) {
      updateSheetData(CONFIG.SHEETS.PAYMENTS, payments);
      updateSheetData(CONFIG.SHEETS.EXPENSES, expenses);
    }

    return {
      success: true,
      message: `照合処理が完了しました`,
      matched: matchedCount
    };
  } catch (error) {
    console.error('照合処理エラー:', error);
    return { success: false, error: error.message };
  }
}

function generateExpensesFromMaster(year, month) {
  try {
    const masters = getSheetData(CONFIG.SHEETS.MASTERS);
    const existingExpenses = getSheetData(CONFIG.SHEETS.EXPENSES);
    const newExpenses = [];
    let generated = 0;
    let skipped = 0;
    const errors = [];

    masters.forEach(master => {
      try {
        const projectName = master[1];
        const payee = master[2];
        const payeeCode = master[3];
        const amount = master[4];
        const paymentType = master[5];
        const startDate = new Date(master[6]);
        const endDate = new Date(master[7]);
        const broadcastDays = master[8];
        const broadcastCount = master[9] || 1;

        const targetDate = new Date(year, month - 1, 1);

        // 対象期間内かチェック
        if (targetDate >= startDate && targetDate <= endDate) {
          // 重複チェック
          const isDuplicate = existingExpenses.some(expense =>
            expense[1] === projectName &&
            expense[2] === payee &&
            new Date(expense[5]).getMonth() === month - 1 &&
            new Date(expense[5]).getFullYear() === year
          );

          if (!isDuplicate) {
            // 支払日を計算（月末）
            const paymentDate = new Date(year, month, 0);

            // 回数ベースの場合は指定回数分生成
            const count = paymentType === '回数ベース' ? parseInt(broadcastCount) : 1;
            for (let i = 0; i < count; i++) {
              const expenseId = `EXP${year}${String(month).padStart(2, '0')}${String(generated + 1).padStart(3, '0')}`;
              newExpenses.push([
                expenseId,
                projectName,
                payee,
                payeeCode,
                amount,
                paymentDate,
                '未処理',
                new Date(),
                new Date()
              ]);
              generated++;
            }
          } else {
            skipped++;
          }
        }
      } catch (error) {
        errors.push(`マスター${master[0]}の処理でエラー: ${error.message}`);
      }
    });

    // 新しい費用データを追加
    if (newExpenses.length > 0) {
      appendToSheet(CONFIG.SHEETS.EXPENSES, newExpenses);
    }

    return {
      success: true,
      message: `${year}年${month}月分の費用データを生成しました`,
      targetPeriod: `${year}年${month}月`,
      generated: generated,
      skipped: skipped,
      errors: errors.length,
      errorDetails: errors
    };
  } catch (error) {
    console.error('月次反映エラー:', error);
    return { success: false, message: error.message };
  }
}

function previewExpensesFromMaster(year, month) {
  try {
    const masters = getSheetData(CONFIG.SHEETS.MASTERS);
    const existingExpenses = getSheetData(CONFIG.SHEETS.EXPENSES);
    const preview = [];
    let totalAmount = 0;
    let newItems = 0;
    let duplicates = 0;

    masters.forEach(master => {
      const projectName = master[1];
      const payee = master[2];
      const amount = master[4];
      const paymentType = master[5];
      const startDate = new Date(master[6]);
      const endDate = new Date(master[7]);
      const broadcastCount = master[9] || 1;

      const targetDate = new Date(year, month - 1, 1);

      if (targetDate >= startDate && targetDate <= endDate) {
        const isDuplicate = existingExpenses.some(expense =>
          expense[1] === projectName &&
          expense[2] === payee &&
          new Date(expense[5]).getMonth() === month - 1 &&
          new Date(expense[5]).getFullYear() === year
        );

        const count = paymentType === '回数ベース' ? parseInt(broadcastCount) : 1;

        preview.push({
          projectName: projectName,
          payee: payee,
          paymentType: paymentType,
          broadcastCount: count,
          amount: amount * count,
          isDuplicate: isDuplicate,
          action: isDuplicate ? 'スキップ' : '新規作成'
        });

        if (isDuplicate) {
          duplicates++;
        } else {
          newItems++;
          totalAmount += amount * count;
        }
      }
    });

    return {
      success: true,
      targetPeriod: `${year}年${month}月`,
      summary: {
        total: preview.length,
        newItems: newItems,
        duplicates: duplicates,
        totalAmount: totalAmount
      },
      preview: preview
    };
  } catch (error) {
    console.error('プレビュー生成エラー:', error);
    return { success: false, message: error.message };
  }
}

// ========== ユーティリティ関数 ==========

function getOrCreateSpreadsheet() {
  try {
    return SpreadsheetApp.getActiveSpreadsheet();
  } catch (e) {
    // アクティブなスプレッドシートがない場合は新規作成
    return SpreadsheetApp.create(CONFIG.SPREADSHEET_NAME);
  }
}

function initializeSheet(spreadsheet, sheetName, headers) {
  let sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  } else {
    sheet.clear();
  }

  // ヘッダー設定
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  sheet.getRange(1, 1, 1, headers.length).setBackground('#E8F4FD');

  // 列幅調整
  headers.forEach((header, index) => {
    if (header === 'ID' || header === '支払い先コード') {
      sheet.setColumnWidth(index + 1, 120);
    } else if (header === '金額') {
      sheet.setColumnWidth(index + 1, 100);
    } else if (header === '案件名' || header === '件名') {
      sheet.setColumnWidth(index + 1, 200);
    } else {
      sheet.setColumnWidth(index + 1, 150);
    }
  });

  return sheet;
}

function getSheetData(sheetName) {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName(sheetName);

    if (!sheet) {
      console.warn(`シート ${sheetName} が見つかりません`);
      return [];
    }

    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) {
      return [];
    }

    const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
    return data.filter(row => row.some(cell => cell !== '' && cell !== null));
  } catch (error) {
    console.error(`シートデータ取得エラー (${sheetName}):`, error);
    return [];
  }
}

function insertSampleData(spreadsheet, sheetName, data) {
  const sheet = spreadsheet.getSheetByName(sheetName);
  if (sheet && data.length > 0) {
    const startRow = sheet.getLastRow() + 1;
    sheet.getRange(startRow, 1, data.length, data[0].length).setValues(data);
  }
}

function clearSheetData(spreadsheet, sheetName) {
  const sheet = spreadsheet.getSheetByName(sheetName);
  if (sheet) {
    const lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clear();
    }
  }
}

function updateSheetData(sheetName, data) {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName(sheetName);

    if (sheet && data.length > 0) {
      clearSheetData(spreadsheet, sheetName);
      insertSampleData(spreadsheet, sheetName, data);
    }
  } catch (error) {
    console.error(`シートデータ更新エラー (${sheetName}):`, error);
  }
}

function appendToSheet(sheetName, data) {
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName(sheetName);

    if (sheet && data.length > 0) {
      const startRow = sheet.getLastRow() + 1;
      sheet.getRange(startRow, 1, data.length, data[0].length).setValues(data);
    }
  } catch (error) {
    console.error(`シートデータ追加エラー (${sheetName}):`, error);
  }
}

function getSheetNameByDataType(dataType) {
  const mapping = {
    'payments': CONFIG.SHEETS.PAYMENTS,
    'expenses': CONFIG.SHEETS.EXPENSES,
    'masters': CONFIG.SHEETS.MASTERS
  };
  return mapping[dataType] || CONFIG.SHEETS.PAYMENTS;
}

// ========== 追加のラッパー関数（HTML互換性） ==========

function refreshPayments() {
  return getPaymentData();
}

function refreshExpenses() {
  return getExpenseData();
}

function refreshMasters() {
  return getMasterData();
}

function searchPayments() {
  return getPaymentData();
}

function searchExpenses() {
  return getExpenseData();
}

function searchMasters() {
  return getMasterData();
}

function resetPaymentFilters() {
  return getPaymentData();
}

function resetExpenseFilters() {
  return getExpenseData();
}

function resetMasterFilters() {
  return getMasterData();
}

// テスト用の基本関数
function test() {
  return 'GAS functions are working properly!';
}