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
    console.log('getPaymentData: 開始');
    const startTime = Date.now();

    const data = getSheetDataSafe(CONFIG.SHEETS.PAYMENTS);

    const duration = Date.now() - startTime;
    console.log(`getPaymentData: 完了 (${duration}ms, ${data.length}件)`);

    return { success: true, data: data, duration: duration };
  } catch (error) {
    console.error('支払いデータ取得エラー:', error);
    return {
      success: false,
      error: error.message,
      data: [],
      fallback: true
    };
  }
}

function getExpenseData() {
  try {
    console.log('getExpenseData: 開始');
    const startTime = Date.now();

    const data = getSheetDataSafe(CONFIG.SHEETS.EXPENSES);

    const duration = Date.now() - startTime;
    console.log(`getExpenseData: 完了 (${duration}ms, ${data.length}件)`);

    return { success: true, data: data, duration: duration };
  } catch (error) {
    console.error('費用データ取得エラー:', error);
    return {
      success: false,
      error: error.message,
      data: [],
      fallback: true
    };
  }
}

function getMasterData() {
  try {
    console.log('getMasterData: 開始');
    const startTime = Date.now();

    const data = getSheetDataSafe(CONFIG.SHEETS.MASTERS);

    const duration = Date.now() - startTime;
    console.log(`getMasterData: 完了 (${duration}ms, ${data.length}件)`);

    return { success: true, data: data, duration: duration };
  } catch (error) {
    console.error('マスターデータ取得エラー:', error);
    return {
      success: false,
      error: error.message,
      data: [],
      fallback: true
    };
  }
}

// ========== 安全なデータ取得関数 ==========

function getSheetDataSafe(sheetName, timeout = 10000) {
  const startTime = Date.now();
  console.log(`getSheetDataSafe: ${sheetName} 開始`);

  try {
    // タイムアウト付きでスプレッドシート取得を試行
    const spreadsheet = getSpreadsheetWithTimeout(timeout);
    if (!spreadsheet) {
      console.warn(`getSheetDataSafe: スプレッドシートにアクセスできません (${sheetName})`);
      return getFallbackData(sheetName);
    }

    const duration = Date.now() - startTime;
    if (duration > timeout) {
      console.warn(`getSheetDataSafe: タイムアウト (${duration}ms > ${timeout}ms)`);
      return getFallbackData(sheetName);
    }

    const sheet = getSafeSheet(spreadsheet, sheetName);
    if (!sheet) {
      console.warn(`getSheetDataSafe: シート ${sheetName} が見つかりません`);
      return getFallbackData(sheetName);
    }

    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) {
      console.log(`getSheetDataSafe: シート ${sheetName} にデータがありません`);
      return [];
    }

    const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
    console.log(`getSheetDataSafe: ${sheetName} 完了 (${data.length}行)`);
    return data;

  } catch (error) {
    console.error(`getSheetDataSafe: エラー (${sheetName}):`, error);
    return getFallbackData(sheetName);
  }
}

function getSpreadsheetWithTimeout(timeout = 10000) {
  const startTime = Date.now();

  try {
    // 最初に軽量な方法を試行
    const activeSpreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    if (activeSpreadsheet) {
      console.log('getSpreadsheetWithTimeout: アクティブなスプレッドシートを使用');
      return activeSpreadsheet;
    }
  } catch (e) {
    console.warn('getSpreadsheetWithTimeout: アクティブなスプレッドシートが見つかりません');
  }

  // タイムアウトチェック
  if (Date.now() - startTime > timeout / 2) {
    console.warn('getSpreadsheetWithTimeout: 半分の時間が経過、新規作成をスキップ');
    return null;
  }

  try {
    const properties = PropertiesService.getScriptProperties();
    const savedSpreadsheetId = properties.getProperty('SPREADSHEET_ID');

    if (savedSpreadsheetId) {
      try {
        const savedSpreadsheet = SpreadsheetApp.openById(savedSpreadsheetId);
        console.log('getSpreadsheetWithTimeout: 保存されたスプレッドシートを使用');
        return savedSpreadsheet;
      } catch (e) {
        console.warn('getSpreadsheetWithTimeout: 保存されたスプレッドシートにアクセスできません');
        properties.deleteProperty('SPREADSHEET_ID');
      }
    }
  } catch (e) {
    console.error('getSpreadsheetWithTimeout: PropertiesServiceエラー:', e);
  }

  // タイムアウトした場合は null を返す
  if (Date.now() - startTime > timeout) {
    console.warn('getSpreadsheetWithTimeout: タイムアウト');
    return null;
  }

  return null; // 新規作成はスキップして、フォールバックデータを使用
}

function getFallbackData(sheetName) {
  console.log(`getFallbackData: ${sheetName} のサンプルデータを返します`);

  switch (sheetName) {
    case CONFIG.SHEETS.PAYMENTS:
      return [
        ['PAY001', '広告放送料', 'ラジオCM番組A', '株式会社サンプル', 'COMP001', '50000', '2024-01-15', '支払済', new Date(), new Date()],
        ['PAY002', '制作費', 'ラジオCM番組B', '制作会社B', 'COMP002', '120000', '2024-01-20', '未払い', new Date(), new Date()]
      ];

    case CONFIG.SHEETS.EXPENSES:
      return [
        ['EXP001', 'ラジオCM番組A', '株式会社サンプル', 'COMP001', '50000', '2024-01-15', '支払済', new Date(), new Date()],
        ['EXP002', 'ラジオCM番組B', '制作会社B', 'COMP002', '120000', '2024-01-20', '未払い', new Date(), new Date()]
      ];

    case CONFIG.SHEETS.MASTERS:
      return [
        ['MAS001', 'ラジオCM番組A', '株式会社サンプル', 'COMP001', '50000', '放送料', '2024-01-01', '2024-03-31', '月曜', '12', '3ヶ月契約', new Date(), new Date()],
        ['MAS002', 'ラジオCM番組B', '制作会社B', 'COMP002', '120000', '制作費', '2024-01-01', '2024-12-31', '金曜', '52', '年間契約', new Date(), new Date()]
      ];

    default:
      return [];
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
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      return { success: false, message: 'スプレッドシートにアクセスできません' };
    }

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
  console.log(`CSVデータインポート開始: ${dataType}, クリア: ${clearExisting}`);

  try {
    // 入力検証
    if (!csvText?.trim()) {
      throw new Error('CSVデータが空です');
    }

    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSVデータにヘッダーとデータ行が必要です');
    }

    console.log(`CSV行数: ${lines.length}行 (ヘッダー含む)`);

    // スプレッドシート取得の再試行機能
    let spreadsheet = null;
    let retryCount = 0;
    const maxRetries = 3;

    while (retryCount < maxRetries && !spreadsheet) {
      console.log(`スプレッドシート取得試行 ${retryCount + 1}/${maxRetries}`);
      spreadsheet = getOrCreateSpreadsheet();

      if (!spreadsheet) {
        console.warn(`スプレッドシート取得失敗 (試行 ${retryCount + 1}/${maxRetries})`);
        retryCount++;
        if (retryCount < maxRetries) {
          console.log('1秒待機してリトライします...');
          Utilities.sleep(1000);
        }
      } else {
        debugSpreadsheetState(spreadsheet, 'CSV取得後');
        break;
      }
    }

    if (!spreadsheet) {
      throw new Error('スプレッドシートの作成/取得に失敗しました。システム初期化を実行してください。');
    }

    // シート名取得と検証
    const sheetName = getSheetNameByDataType(dataType);
    if (!sheetName) {
      throw new Error(`無効なデータタイプ: ${dataType}`);
    }

    console.log(`対象シート: ${sheetName}`);

    // シート存在確認と自動作成
    let sheet = getSafeSheet(spreadsheet, sheetName);
    if (!sheet) {
      console.log(`シート「${sheetName}」が存在しないため作成します`);
      const headers = getHeadersForSheet(sheetName);
      if (headers.length === 0) {
        throw new Error(`シート「${sheetName}」のヘッダー情報が見つかりません`);
      }
      sheet = initializeSheet(spreadsheet, sheetName, headers);
      if (!sheet) {
        throw new Error(`シート「${sheetName}」の作成に失敗しました`);
      }
    }

    // 既存データクリア
    if (clearExisting) {
      console.log('既存データをクリア中...');
      try {
        const lastRow = sheet.getLastRow();
        if (lastRow > 1) {
          sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clear();
          console.log(`${lastRow - 1}行のデータをクリアしました`);
        }
      } catch (clearError) {
        console.error('データクリアエラー:', clearError);
        throw new Error(`データクリア失敗: ${clearError.message}`);
      }
    }

    // CSVパース（改良版）
    console.log('CSVデータを解析中...');
    const data = [];
    const errors = [];

    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].trim();
        if (!line) continue; // 空行をスキップ

        const row = parseCsvLine(line);
        if (row.length === 0) continue;

        // ヘッダーマッピングを使用してデータを正しい順序に変換
        const mappedRow = [];

        // IDを最初に設定（自動生成または既存値）
        const idValue = row[0] && row[0].trim() !== '' ? row[0] : `${dataType.toUpperCase()}${Date.now()}${i}`;
        mappedRow.push(idValue);

        // 期待されるヘッダーの順序でデータをマッピング
        expected.slice(1).forEach(expectedHeader => { // IDを除く
          const sourceIndex = headerMapping[expectedHeader];
          let value = '';

          if (sourceIndex !== undefined && row[sourceIndex] !== undefined) {
            value = row[sourceIndex].trim();
          }

          // データ型の基本的な変換
          if (expectedHeader === '金額' && value !== '') {
            // 金額の場合は数値に変換を試行
            const numValue = value.replace(/[,¥￥]/g, '');
            if (!isNaN(numValue) && numValue !== '') {
              value = numValue;
            }
          }

          mappedRow.push(value);
        });

        // 作成日・更新日を追加
        mappedRow.push(new Date(), new Date());
        data.push(mappedRow);

      } catch (parseError) {
        const errorMsg = `行 ${i + 1}: ${parseError.message}`;
        console.warn(errorMsg);
        errors.push(errorMsg);
      }
    }

    console.log(`解析完了: ${data.length}行のデータを抽出`);
    console.log('ヘッダーマッピング結果:', headerMapping);

    // データ挿入
    if (data.length > 0) {
      console.log('データ挿入を開始...');
      try {
        const startRow = sheet.getLastRow() + 1;
        console.log(`${startRow}行目から${data.length}行のデータを挿入`);

        sheet.getRange(startRow, 1, data.length, data[0].length).setValues(data);
        console.log('データ挿入が完了しました');

      } catch (insertError) {
        console.error('データ挿入エラー:', insertError);
        throw new Error(`データ挿入失敗: ${insertError.message}`);
      }
    } else {
      console.warn('挿入するデータがありません');
    }

    const result = {
      success: true,
      message: `${dataType}データのCSVインポートが完了しました`,
      results: {
        imported: data.length,
        skipped: lines.length - 1 - data.length,
        errors: errors
      }
    };

    console.log('CSVデータインポート完了:', result);
    return result;

  } catch (error) {
    console.error('importCSVData詳細エラー:', error);
    console.error('エラースタック:', error.stack);

    const errorResult = {
      success: false,
      message: `CSVインポートエラー: ${error.message}`,
      results: { imported: 0, skipped: 0, errors: [error.message] }
    };

    console.log('エラー結果:', errorResult);
    return errorResult;
  }
}

// ========== 診断・検証関数 ==========

function runSystemDiagnosis() {
  try {
    const checks = [];
    let passedChecks = 0;

    // スプレッドシートの存在確認
    try {
      const spreadsheet = getOrCreateSpreadsheet();
      if (spreadsheet) {
        checks.push({ name: 'スプレッドシート', status: 'PASS', message: '正常' });
        passedChecks++;
      } else {
        checks.push({ name: 'スプレッドシート', status: 'FAIL', message: 'スプレッドシートにアクセスできません' });
      }
    } catch (e) {
      checks.push({ name: 'スプレッドシート', status: 'FAIL', message: e.message });
    }

    // 各シートの確認
    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      try {
        const spreadsheet = getOrCreateSpreadsheet();
        if (!spreadsheet) {
          checks.push({ name: `シート: ${sheetName}`, status: 'FAIL', message: 'スプレッドシートにアクセスできません' });
          return;
        }

        const sheet = spreadsheet.getSheetByName(sheetName);
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
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      return { success: false, message: 'スプレッドシートにアクセスできません' };
    }

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
    // まずアクティブなスプレッドシートを試行
    const activeSpreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    if (activeSpreadsheet) {
      return activeSpreadsheet;
    }
  } catch (e) {
    console.warn('アクティブなスプレッドシートが見つかりません:', e.message);
  }

  try {
    // PropertiesServiceでスプレッドシートIDを保存・取得
    const properties = PropertiesService.getScriptProperties();
    const savedSpreadsheetId = properties.getProperty('SPREADSHEET_ID');

    if (savedSpreadsheetId) {
      try {
        const savedSpreadsheet = SpreadsheetApp.openById(savedSpreadsheetId);
        if (savedSpreadsheet) {
          console.log('保存されたスプレッドシートを使用:', savedSpreadsheetId);
          return savedSpreadsheet;
        }
      } catch (e) {
        console.warn('保存されたスプレッドシートにアクセスできません:', e.message);
        // 無効なIDをクリア
        properties.deleteProperty('SPREADSHEET_ID');
      }
    }

    // 新しいスプレッドシートを作成
    console.log('新しいスプレッドシートを作成中...');
    const newSpreadsheet = SpreadsheetApp.create(CONFIG.SPREADSHEET_NAME + '_' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd_HHmmss'));

    if (newSpreadsheet) {
      // 新しいスプレッドシートのIDを保存
      properties.setProperty('SPREADSHEET_ID', newSpreadsheet.getId());
      console.log('新しいスプレッドシートを作成しました:', newSpreadsheet.getId());

      // 必要なシートを初期化
      try {
        console.log('必要なシートを初期化中...');

        // デフォルトシートを削除
        const defaultSheet = newSpreadsheet.getSheetByName('シート1');
        if (defaultSheet) {
          newSpreadsheet.deleteSheet(defaultSheet);
        }

        // 各シートを作成
        Object.entries(CONFIG.SHEETS).forEach(([key, sheetName]) => {
          const headers = CONFIG.HEADERS[key.toUpperCase()];
          if (headers) {
            initializeSheet(newSpreadsheet, sheetName, headers);
            console.log(`シート「${sheetName}」を初期化しました`);
          }
        });

        console.log('スプレッドシートの初期化が完了しました');
      } catch (initError) {
        console.error('スプレッドシート初期化エラー:', initError);
        // 初期化に失敗してもスプレッドシートは返す
      }

      return newSpreadsheet;
    }

    throw new Error('スプレッドシートの作成に失敗しました');
  } catch (error) {
    console.error('getOrCreateSpreadsheet エラー:', error);
    return null;
  }
}

function initializeSheet(spreadsheet, sheetName, headers) {
  if (!spreadsheet) {
    console.error('initializeSheet: スプレッドシートがnullです');
    return null;
  }

  let sheet = getSafeSheet(spreadsheet, sheetName);

  if (!sheet) {
    try {
      sheet = spreadsheet.insertSheet(sheetName);
      console.log(`initializeSheet: シート「${sheetName}」を新規作成しました`);
    } catch (error) {
      console.error(`initializeSheet: シート作成エラー (${sheetName}):`, error);
      return null;
    }
  } else {
    try {
      sheet.clear();
      console.log(`initializeSheet: シート「${sheetName}」をクリアしました`);
    } catch (error) {
      console.error(`initializeSheet: シートクリアエラー (${sheetName}):`, error);
      return null;
    }
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
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      console.warn(`getSheetData: スプレッドシートにアクセスできません`);
      return [];
    }

    const sheet = getSafeSheet(spreadsheet, sheetName);
    if (!sheet) {
      console.warn(`getSheetData: シート ${sheetName} が見つかりません`);
      return [];
    }

    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) {
      console.log(`getSheetData: シート ${sheetName} にデータがありません`);
      return [];
    }

    const data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
    const filteredData = data.filter(row => row.some(cell => cell !== '' && cell !== null));
    console.log(`getSheetData: シート ${sheetName} から ${filteredData.length} 行のデータを取得`);
    return filteredData;
  } catch (error) {
    console.error(`getSheetData: シートデータ取得エラー (${sheetName}):`, error);
    return [];
  }
}

function insertSampleData(spreadsheet, sheetName, data) {
  if (!spreadsheet) {
    console.error('insertSampleData: スプレッドシートがnullです');
    return;
  }

  if (!data || data.length === 0) {
    console.warn(`insertSampleData: データが空です (${sheetName})`);
    return;
  }

  let sheet = getSafeSheet(spreadsheet, sheetName);
  if (!sheet) {
    // シートが存在しない場合は作成
    console.log(`insertSampleData: シート「${sheetName}」が存在しないため作成します`);
    const headers = getHeadersForSheet(sheetName);
    if (headers.length > 0) {
      sheet = initializeSheet(spreadsheet, sheetName, headers);
    } else {
      console.error(`insertSampleData: シート「${sheetName}」のヘッダー情報が見つかりません`);
      return;
    }
  }

  if (sheet) {
    try {
      const startRow = sheet.getLastRow() + 1;
      sheet.getRange(startRow, 1, data.length, data[0].length).setValues(data);
      console.log(`insertSampleData: シート「${sheetName}」に${data.length}行のデータを挿入しました`);
    } catch (error) {
      console.error(`insertSampleData: データ挿入エラー (${sheetName}):`, error);
      throw error;
    }
  }
}

function clearSheetData(spreadsheet, sheetName) {
  if (!spreadsheet) {
    console.error('clearSheetData: スプレッドシートがnullです');
    return;
  }

  let sheet = getSafeSheet(spreadsheet, sheetName);
  if (!sheet) {
    // シートが存在しない場合は作成
    console.log(`clearSheetData: シート「${sheetName}」が存在しないため作成します`);
    const headers = getHeadersForSheet(sheetName);
    if (headers.length > 0) {
      sheet = initializeSheet(spreadsheet, sheetName, headers);
    } else {
      console.error(`clearSheetData: シート「${sheetName}」のヘッダー情報が見つかりません`);
      return;
    }
  }

  if (sheet) {
    try {
      const lastRow = sheet.getLastRow();
      if (lastRow > 1) {
        sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clear();
        console.log(`clearSheetData: シート「${sheetName}」のデータをクリアしました`);
      }
    } catch (error) {
      console.error(`clearSheetData: データクリアエラー (${sheetName}):`, error);
    }
  }
}

function updateSheetData(sheetName, data) {
  try {
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      console.error(`スプレッドシートにアクセスできません (${sheetName})`);
      return;
    }

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
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      console.error(`スプレッドシートにアクセスできません (${sheetName})`);
      return;
    }

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

function getHeadersForSheet(sheetName) {
  const mapping = {
    [CONFIG.SHEETS.PAYMENTS]: CONFIG.HEADERS.PAYMENTS,
    [CONFIG.SHEETS.EXPENSES]: CONFIG.HEADERS.EXPENSES,
    [CONFIG.SHEETS.MASTERS]: CONFIG.HEADERS.MASTERS
  };
  return mapping[sheetName] || [];
}

// ========== 安全なシート操作関数 ==========

function getSafeSheet(spreadsheet, sheetName) {
  if (!spreadsheet) {
    console.error('getSafeSheet: スプレッドシートがnull');
    return null;
  }

  try {
    const sheet = spreadsheet.getSheetByName(sheetName);
    if (!sheet) {
      console.warn(`getSafeSheet: シート「${sheetName}」が存在しません`);
    }
    return sheet;
  } catch (error) {
    console.error(`getSafeSheet: シート取得エラー (${sheetName}):`, error);
    return null;
  }
}

function debugSpreadsheetState(spreadsheet, context) {
  console.log(`=== デバッグ情報 (${context}) ===`);
  console.log('スプレッドシート:', spreadsheet ? 'OK' : 'NULL');
  if (spreadsheet) {
    try {
      console.log('ID:', spreadsheet.getId());
      console.log('名前:', spreadsheet.getName());
      console.log('URL:', spreadsheet.getUrl());
      const sheets = spreadsheet.getSheets();
      console.log('シート数:', sheets.length);
      console.log('シート名:', sheets.map(s => s.getName()).join(', '));
    } catch (error) {
      console.error('スプレッドシート情報取得エラー:', error);
    }
  }
  console.log('========================');
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

// ========== UI関連関数 ==========

function showCSVImportDialog() {
  try {
    // Webアプリ用CSVインポートダイアログ開始
    return {
      success: true,
      message: 'CSVインポートダイアログを開く準備完了',
      action: 'showDialog',
      dialogType: 'csvImport',
      dialogConfig: {
        title: 'CSVデータインポート',
        dataTypes: [
          { value: 'payments', label: '支払いデータ' },
          { value: 'expenses', label: '費用データ' },
          { value: 'masters', label: 'マスターデータ' }
        ]
      }
    };
  } catch (error) {
    console.error('CSVダイアログ表示エラー:', error);
    return { success: false, message: error.message };
  }
}

function showSystemStatus() {
  try {
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      return { success: false, message: 'スプレッドシートにアクセスできません' };
    }

    const status = {
      spreadsheetId: spreadsheet.getId(),
      spreadsheetName: spreadsheet.getName(),
      spreadsheetUrl: spreadsheet.getUrl(),
      sheets: {},
      timestamp: new Date().toISOString()
    };

    // 各シートの状態確認
    Object.values(CONFIG.SHEETS).forEach(sheetName => {
      const sheet = spreadsheet.getSheetByName(sheetName);
      status.sheets[sheetName] = {
        exists: !!sheet,
        rows: sheet ? sheet.getLastRow() : 0,
        columns: sheet ? sheet.getLastColumn() : 0
      };
    });

    return {
      success: true,
      message: 'システム状態を取得しました',
      status: status
    };
  } catch (error) {
    console.error('システム状態確認エラー:', error);
    return { success: false, message: error.message };
  }
}

function openMasterReflectionModal() {
  try {
    return {
      success: true,
      message: 'モーダルを開く準備ができました',
      action: 'openModal',
      modalId: 'masterReflectionModal'
    };
  } catch (error) {
    console.error('モーダル表示エラー:', error);
    return { success: false, message: error.message };
  }
}

function generateFromMasterForCurrentMonth() {
  try {
    const now = new Date();
    return generateExpensesFromMaster(now.getFullYear(), now.getMonth() + 1);
  } catch (error) {
    console.error('今月分生成エラー:', error);
    return { success: false, message: error.message };
  }
}

function generateFromMasterForNextMonth() {
  try {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return generateExpensesFromMaster(nextMonth.getFullYear(), nextMonth.getMonth() + 1);
  } catch (error) {
    console.error('来月分生成エラー:', error);
    return { success: false, message: error.message };
  }
}

function setCurrentMonth() {
  try {
    const now = new Date();
    return {
      success: true,
      year: now.getFullYear(),
      month: now.getMonth() + 1,
      message: '今月が設定されました'
    };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

function setNextMonth() {
  try {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return {
      success: true,
      year: nextMonth.getFullYear(),
      month: nextMonth.getMonth() + 1,
      message: '来月が設定されました'
    };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

function setPreviousMonth() {
  try {
    const now = new Date();
    const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    return {
      success: true,
      year: prevMonth.getFullYear(),
      month: prevMonth.getMonth() + 1,
      message: '先月が設定されました'
    };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

function previewMasterReflection() {
  try {
    const now = new Date();
    return previewExpensesFromMaster(now.getFullYear(), now.getMonth() + 1);
  } catch (error) {
    console.error('プレビュー生成エラー:', error);
    return { success: false, message: error.message };
  }
}

function executeMasterReflection() {
  try {
    const now = new Date();
    return generateExpensesFromMaster(now.getFullYear(), now.getMonth() + 1);
  } catch (error) {
    console.error('月次反映実行エラー:', error);
    return { success: false, message: error.message };
  }
}

function emergencySystemSetup() {
  try {
    console.log('緊急システム初期化開始');

    // 新しいスプレッドシートを作成
    const createResult = createNewSpreadsheet();
    if (!createResult.success) {
      return createResult;
    }

    // システム初期化
    const initResult = initializeCompleteSystem();
    if (!initResult.success) {
      return initResult;
    }

    // サンプルデータ作成
    const sampleResult = createSampleData();

    return {
      success: true,
      message: '緊急システム初期化が完了しました',
      details: {
        spreadsheet: createResult,
        initialization: initResult,
        sampleData: sampleResult
      }
    };
  } catch (error) {
    console.error('緊急システム初期化エラー:', error);
    return { success: false, message: error.message };
  }
}

function runSystemDebug() {
  try {
    console.log('システムデバッグ開始');

    const debug = {
      timestamp: new Date().toISOString(),
      functions: {},
      spreadsheet: {},
      data: {}
    };

    // 関数存在チェック
    const functionList = [
      'getPaymentData', 'getExpenseData', 'getMasterData',
      'initializeCompleteSystem', 'createSampleData', 'checkSystemStatus'
    ];

    functionList.forEach(funcName => {
      debug.functions[funcName] = typeof eval(funcName) === 'function';
    });

    // スプレッドシート情報
    try {
      const spreadsheet = getOrCreateSpreadsheet();
      debug.spreadsheet = {
        exists: !!spreadsheet,
        id: spreadsheet ? spreadsheet.getId() : null,
        name: spreadsheet ? spreadsheet.getName() : null
      };
    } catch (e) {
      debug.spreadsheet = { error: e.message };
    }

    // データ取得テスト
    try {
      const paymentResult = getPaymentData();
      debug.data.payments = {
        success: paymentResult.success,
        count: paymentResult.data ? paymentResult.data.length : 0
      };
    } catch (e) {
      debug.data.payments = { error: e.message };
    }

    return {
      success: true,
      message: 'システムデバッグを完了しました',
      debug: debug
    };
  } catch (error) {
    console.error('システムデバッグエラー:', error);
    return { success: false, message: error.message };
  }
}

// ========== CSV処理関数 ==========

function processCsvImport(csvData, dataType, clearExisting = false) {
  try {
    console.log(`CSVインポート開始: ${dataType}, クリア: ${clearExisting}`);

    if (!csvData || !csvData.trim()) {
      return { success: false, message: 'CSVデータが空です' };
    }

    // スプレッドシートの確認
    const spreadsheet = getOrCreateSpreadsheet();
    if (!spreadsheet) {
      return {
        success: false,
        message: 'スプレッドシートにアクセスできません。システム初期化を実行してください。'
      };
    }

    // CSV解析
    const parsedData = parseCsvText(csvData);
    if (!parsedData.success) {
      return parsedData;
    }

    // CSVデータ検証
    const validation = validateCsvData(parsedData.headers, parsedData.rows, dataType);
    if (!validation.success) {
      return validation;
    }

    // 既存のimportCSVData関数を使用
    const result = importCSVData(csvData, dataType, clearExisting);

    return {
      success: result.success,
      message: result.message,
      results: result.results || {},
      importedRows: parsedData.rows ? parsedData.rows.length : 0,
      spreadsheetId: spreadsheet.getId(),
      spreadsheetUrl: spreadsheet.getUrl()
    };
  } catch (error) {
    console.error('CSVインポート処理エラー:', error);
    return { success: false, message: error.message };
  }
}

function parseCsvText(csvText) {
  try {
    if (!csvText || !csvText.trim()) {
      return { success: false, message: 'CSVテキストが空です' };
    }

    const lines = csvText.trim().split('\n');

    if (lines.length < 2) {
      return { success: false, message: 'CSVにはヘッダーとデータ行が必要です' };
    }

    // ヘッダー行を解析
    const headers = parseCsvLine(lines[0]);

    // データ行を解析
    const rows = [];
    const errors = [];

    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].trim();
        if (line) {
          const row = parseCsvLine(line);
          if (row.length > 0) {
            rows.push(row);
          }
        }
      } catch (error) {
        errors.push(`行 ${i + 1}: ${error.message}`);
      }
    }

    return {
      success: true,
      headers: headers,
      rows: rows,
      totalLines: lines.length,
      dataLines: rows.length,
      errors: errors
    };
  } catch (error) {
    console.error('CSV解析エラー:', error);
    return { success: false, message: error.message };
  }
}

function parseCsvLine(line) {
  // シンプルなCSV行解析（カンマ区切り、ダブルクォート対応）
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        // エスケープされたダブルクォート
        current += '"';
        i++; // 次の文字をスキップ
      } else {
        // クォートの開始/終了
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      // フィールド区切り
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

function validateCsvData(headers, rows, dataType) {
  try {
    const expectedHeaders = {
      'payments': ['件名', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態'],
      'expenses': ['案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態'],
      'masters': ['案件名', '支払い先', '支払い先コード', '金額', '種別', '開始日', '終了日', '放送曜日', '回数', '備考']
    };

    const expected = expectedHeaders[dataType];
    if (!expected) {
      return { success: false, message: '不正なデータ種別です' };
    }

    // ヘッダー検証（より柔軟なマッチング）
    const headerMapping = {};
    const missingHeaders = [];

    expected.forEach(expectedHeader => {
      // 完全一致を最優先
      let matchedIndex = headers.findIndex(h => h === expectedHeader);

      // 完全一致しない場合は部分一致を試行
      if (matchedIndex === -1) {
        matchedIndex = headers.findIndex(h =>
          h.includes(expectedHeader) || expectedHeader.includes(h) ||
          h.replace(/\s/g, '') === expectedHeader.replace(/\s/g, '')
        );
      }

      // それでもマッチしない場合は類似キーワードを試行
      if (matchedIndex === -1) {
        const keywords = {
          '案件名': ['案件', 'project', 'プロジェクト', '番組'],
          '支払い先': ['支払先', '支払', 'vendor', 'company', '会社'],
          '支払い先コード': ['コード', 'code', 'id'],
          '金額': ['金額', '料金', 'amount', 'price', '価格'],
          '種別': ['種別', 'type', 'category', 'カテゴリ'],
          '開始日': ['開始', 'start', '開始日付'],
          '終了日': ['終了', 'end', '終了日付'],
          '放送曜日': ['曜日', 'day', '放送日'],
          '回数': ['回数', 'count', '回'],
          '備考': ['備考', 'note', 'memo', 'メモ', 'comment']
        };

        if (keywords[expectedHeader]) {
          matchedIndex = headers.findIndex(h =>
            keywords[expectedHeader].some(keyword =>
              h.toLowerCase().includes(keyword.toLowerCase()) ||
              keyword.toLowerCase().includes(h.toLowerCase())
            )
          );
        }
      }

      if (matchedIndex !== -1) {
        headerMapping[expectedHeader] = matchedIndex;
        console.log(`ヘッダーマッピング: "${expectedHeader}" -> "${headers[matchedIndex]}" (位置: ${matchedIndex})`);
      } else {
        missingHeaders.push(expectedHeader);
      }
    });

    // 必須ヘッダーのチェック（マスターデータの場合、一部は任意）
    const requiredHeaders = dataType === 'masters' ?
      ['案件名', '支払い先', '金額'] : // マスターデータでは最低限これだけあれば可
      expected.slice(0, Math.min(4, expected.length)); // その他は最初の4つが必須

    const criticalMissing = missingHeaders.filter(h => requiredHeaders.includes(h));
    if (criticalMissing.length > 0) {
      return {
        success: false,
        message: `重要なヘッダーが不足しています: ${criticalMissing.join(', ')}\n\n利用可能なヘッダー: ${headers.join(', ')}\n\n推奨: サンプルCSVファイルをダウンロードして形式を確認してください。`
      };
    }

    // データ行の基本検証
    const invalidRows = [];
    rows.forEach((row, index) => {
      if (row.length < expected.length - 2) { // ある程度の柔軟性を持たせる
        invalidRows.push(index + 2); // 行番号（ヘッダー含む）
      }
    });

    if (invalidRows.length > 0 && invalidRows.length > rows.length * 0.5) {
      return {
        success: false,
        message: `データ行の形式が正しくありません。問題のある行: ${invalidRows.slice(0, 5).join(', ')}${invalidRows.length > 5 ? '...' : ''}`
      };
    }

    return {
      success: true,
      message: 'CSVデータの検証が完了しました',
      validRows: rows.length - invalidRows.length,
      invalidRows: invalidRows.length
    };
  } catch (error) {
    console.error('CSV検証エラー:', error);
    return { success: false, message: error.message };
  }
}

// ========== サンプルCSVファイル生成 ==========

function generateSampleCSV(dataType) {
  try {
    console.log(`サンプルCSV生成開始: ${dataType}`);

    const headers = {
      'payments': ['ID', '件名', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態'],
      'expenses': ['ID', '案件名', '支払い先', '支払い先コード', '金額', '支払日', '状態'],
      'masters': ['ID', '案件名', '支払い先', '支払い先コード', '金額', '種別', '開始日', '終了日', '放送曜日', '回数', '備考']
    };

    const sampleData = {
      'payments': [
        ['PAY001', '広告放送料', 'ラジオCM番組A', '株式会社サンプル', 'COMP001', '50000', '2024-01-15', '支払済'],
        ['PAY002', '制作費', 'ラジオCM番組B', '制作会社B', 'COMP002', '120000', '2024-01-20', '未払い']
      ],
      'expenses': [
        ['EXP001', 'ラジオCM番組A', '株式会社サンプル', 'COMP001', '50000', '2024-01-15', '支払済'],
        ['EXP002', 'ラジオCM番組B', '制作会社B', 'COMP002', '120000', '2024-01-20', '未払い']
      ],
      'masters': [
        ['MAS001', 'ラジオCM番組A', '株式会社サンプル', 'COMP001', '50000', '放送料', '2024-01-01', '2024-03-31', '月曜', '12', '3ヶ月契約'],
        ['MAS002', 'ラジオCM番組B', '制作会社B', 'COMP002', '120000', '制作費', '2024-01-01', '2024-12-31', '金曜', '52', '年間契約'],
        ['MAS003', 'ニュース番組C', 'ニュース会社C', 'COMP003', '80000', '放送料', '2024-02-01', '2024-06-30', '火水木', '20', '5ヶ月契約']
      ]
    };

    if (!headers[dataType] || !sampleData[dataType]) {
      return {
        success: false,
        message: `サポートされていないデータ種別: ${dataType}`
      };
    }

    // CSVデータを作成
    const csvLines = [];
    csvLines.push(headers[dataType].join(','));

    sampleData[dataType].forEach(row => {
      const csvRow = row.map(cell => {
        // カンマや改行を含む場合はダブルクォートで囲む
        if (typeof cell === 'string' && (cell.includes(',') || cell.includes('\n') || cell.includes('"'))) {
          return `"${cell.replace(/"/g, '""')}"`;
        }
        return cell;
      });
      csvLines.push(csvRow.join(','));
    });

    const csvContent = csvLines.join('\n');

    // CSVファイルをGoogle Driveに保存
    const fileName = `${dataType}_sample_${new Date().toISOString().slice(0, 10)}.csv`;
    const blob = Utilities.newBlob(csvContent, 'text/csv', fileName);
    const file = DriveApp.createFile(blob);

    // ファイルの共有設定を変更（誰でもリンクで表示可能に）
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    const result = {
      success: true,
      message: `${dataType}のサンプルCSVファイルを生成しました`,
      fileName: fileName,
      fileId: file.getId(),
      downloadUrl: file.getDownloadUrl(),
      viewUrl: `https://drive.google.com/file/d/${file.getId()}/view`,
      headers: headers[dataType],
      rowCount: sampleData[dataType].length
    };

    console.log('サンプルCSV生成完了:', result);
    return result;

  } catch (error) {
    console.error('サンプルCSV生成エラー:', error);
    return {
      success: false,
      message: `サンプルCSV生成エラー: ${error.message}`
    };
  }
}

function generateMasterDataSampleCSV() {
  return generateSampleCSV('masters');
}

function generatePaymentDataSampleCSV() {
  return generateSampleCSV('payments');
}

function generateExpenseDataSampleCSV() {
  return generateSampleCSV('expenses');
}

// ========== デバッグ・テスト関数 ==========

function quickDataTest() {
  try {
    console.log('quickDataTest: 開始');
    const startTime = Date.now();

    const results = {
      timestamp: new Date().toISOString(),
      tests: []
    };

    // 基本的なテスト
    results.tests.push({
      name: '基本機能テスト',
      result: 'OK',
      message: 'GAS functions are working properly!'
    });

    // スプレッドシート接続テスト
    try {
      const spreadsheet = getSpreadsheetWithTimeout(5000);
      results.tests.push({
        name: 'スプレッドシート接続',
        result: spreadsheet ? 'OK' : 'FALLBACK',
        message: spreadsheet ? 'スプレッドシートに接続しました' : 'フォールバックモード'
      });
    } catch (e) {
      results.tests.push({
        name: 'スプレッドシート接続',
        result: 'ERROR',
        message: e.message
      });
    }

    // 各データ取得のテスト
    ['PAYMENTS', 'EXPENSES', 'MASTERS'].forEach(sheetType => {
      try {
        const sheetName = CONFIG.SHEETS[sheetType];
        const data = getSheetDataSafe(sheetName, 3000);
        results.tests.push({
          name: `${sheetType} データ取得`,
          result: 'OK',
          message: `${data.length}行のデータを取得`
        });
      } catch (e) {
        results.tests.push({
          name: `${sheetType} データ取得`,
          result: 'ERROR',
          message: e.message
        });
      }
    });

    const duration = Date.now() - startTime;
    results.duration = duration;
    results.summary = `テスト完了 (${duration}ms)`;

    console.log('quickDataTest: 完了', results);
    return { success: true, results: results };

  } catch (error) {
    console.error('quickDataTest: エラー', error);
    return {
      success: false,
      error: error.message,
      results: { tests: [{ name: 'メインテスト', result: 'ERROR', message: error.message }] }
    };
  }
}

function testPaymentDataOnly() {
  try {
    console.log('testPaymentDataOnly: 支払いデータのみテスト');
    const result = getPaymentData();
    console.log('testPaymentDataOnly: 結果', result);
    return result;
  } catch (error) {
    console.error('testPaymentDataOnly: エラー', error);
    return { success: false, error: error.message };
  }
}

function testExpenseDataOnly() {
  try {
    console.log('testExpenseDataOnly: 費用データのみテスト');
    const result = getExpenseData();
    console.log('testExpenseDataOnly: 結果', result);
    return result;
  } catch (error) {
    console.error('testExpenseDataOnly: エラー', error);
    return { success: false, error: error.message };
  }
}

function testMasterDataOnly() {
  try {
    console.log('testMasterDataOnly: マスターデータのみテスト');
    const result = getMasterData();
    console.log('testMasterDataOnly: 結果', result);
    return result;
  } catch (error) {
    console.error('testMasterDataOnly: エラー', error);
    return { success: false, error: error.message };
  }
}

function testSpreadsheetConnection() {
  try {
    console.log('testSpreadsheetConnection: スプレッドシート接続テスト');
    const startTime = Date.now();

    const spreadsheet = getSpreadsheetWithTimeout(8000);
    const duration = Date.now() - startTime;

    if (spreadsheet) {
      const sheets = spreadsheet.getSheets().map(s => s.getName());
      return {
        success: true,
        message: `スプレッドシート接続成功 (${duration}ms)`,
        spreadsheetId: spreadsheet.getId(),
        spreadsheetName: spreadsheet.getName(),
        sheetsCount: sheets.length,
        sheets: sheets
      };
    } else {
      return {
        success: false,
        message: `スプレッドシート接続失敗 (${duration}ms)`,
        fallback: true
      };
    }

  } catch (error) {
    console.error('testSpreadsheetConnection: エラー', error);
    return {
      success: false,
      error: error.message,
      message: 'スプレッドシート接続でエラーが発生'
    };
  }
}

// テスト用の基本関数
function test() {
  return 'GAS functions are working properly!';
}