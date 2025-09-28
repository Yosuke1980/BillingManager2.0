/**
 * データ移行ツール - SQLite（Python版）からGoogleスプレッドシートへのデータ移行
 */

/**
 * Python版のSQLiteデータをGASにインポートするためのCSV変換支援
 */
function createSQLiteExportQueries() {
  const queries = {
    // 支払いデータ用のSQLクエリ
    payments: `
      SELECT 
        id,
        subject,
        project_name,
        payee,
        payee_code,
        amount,
        payment_date,
        status,
        type,
        client_name,
        department,
        project_status,
        project_start_date,
        project_end_date,
        budget,
        approver,
        urgency_level
      FROM payments
      ORDER BY id;
    `,
    
    // 費用データ用のSQLクエリ
    expenses: `
      SELECT 
        id,
        project_name,
        payee,
        payee_code,
        amount,
        payment_date,
        status,
        source_type,
        master_id,
        client_name,
        department,
        project_status,
        project_start_date,
        project_end_date,
        budget,
        approver,
        urgency_level
      FROM expenses
      ORDER BY id;
    `,
    
    // 費用マスター用のSQLクエリ
    expense_master: `
      SELECT 
        id,
        project_name,
        payee,
        payee_code,
        amount,
        payment_type,
        start_date,
        end_date,
        broadcast_days,
        client_name,
        department,
        project_status,
        budget,
        approver,
        urgency_level
      FROM expense_master
      ORDER BY id;
    `
  };
  
  return {
    success: true,
    queries: queries,
    instructions: {
      step1: "Python環境でSQLiteデータベースに接続",
      step2: "上記のクエリを実行してCSVファイルにエクスポート",
      step3: "エクスポートされたCSVファイルをGASのimportFromPythonCsv関数でインポート",
      example_python_code: `
        import sqlite3
        import csv
        
        # データベース接続
        conn = sqlite3.connect('billing.db')
        cursor = conn.cursor()
        
        # 支払いデータのエクスポート
        cursor.execute("""${queries.payments}""")
        with open('payments_export.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([col[0] for col in cursor.description])  # ヘッダー
            writer.writerows(cursor.fetchall())
            
        # 他のテーブルも同様にエクスポート...
        conn.close()
      `
    },
    message: "SQLiteからのデータエクスポート用クエリを生成しました"
  };
}

/**
 * Python版からエクスポートされたCSVデータを一括インポート
 */
function importFromPythonCsv(csvData, dataType) {
  try {
    console.log(`=== Python版${dataType}データ一括インポート開始 ===`);
    
    const validTypes = ['payments', 'expenses', 'expense_master'];
    if (!validTypes.includes(dataType)) {
      throw new Error(`不正なデータタイプ: ${dataType}。有効な値: ${validTypes.join(', ')}`);
    }
    
    const lines = csvData.trim().split(/\r?\n/);
    
    if (lines.length < 2) {
      throw new Error('CSVデータが空または不正です');
    }
    
    // データタイプに応じたシート名と期待フィールドを設定
    const sheetConfig = {
      payments: { 
        sheetName: SHEET_NAMES.PAYMENTS, 
        fields: UNIFIED_FIELDS.PAYMENTS 
      },
      expenses: { 
        sheetName: SHEET_NAMES.EXPENSES, 
        fields: UNIFIED_FIELDS.EXPENSES 
      },
      expense_master: { 
        sheetName: SHEET_NAMES.EXPENSE_MASTER, 
        fields: UNIFIED_FIELDS.EXPENSE_MASTER 
      }
    };
    
    const config = sheetConfig[dataType];
    const sheet = getOrCreateSheet(config.sheetName, config.fields);
    
    // CSVヘッダーを解析
    const csvHeaders = parseCSVLine(lines[0]);
    console.log(`CSV ヘッダー (${csvHeaders.length}列):`, csvHeaders);
    console.log(`期待フィールド (${config.fields.length}列):`, config.fields);
    
    // フィールドマッピングを作成
    const fieldMapping = createPythonFieldMapping(csvHeaders, config.fields, dataType);
    console.log('フィールドマッピング:', fieldMapping);
    
    let importedCount = 0;
    let errorCount = 0;
    const errorDetails = [];
    
    // データ行を処理
    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].trim();
        if (!line) continue;
        
        const row = parseCSVLine(line);
        
        if (row.length < 3) {
          const error = `行 ${i+1}: 列数不足 (${row.length}列)`;
          errorDetails.push(error);
          errorCount++;
          continue;
        }
        
        // マッピングに基づいて新しい行データを作成
        const mappedRow = createMappedRow(row, fieldMapping, config.fields, dataType);
        
        if (mappedRow) {
          sheet.appendRow(mappedRow);
          importedCount++;
          
          if (importedCount % 100 === 0) {
            console.log(`${importedCount}件処理完了...`);
          }
        } else {
          const error = `行 ${i+1}: データマッピングに失敗`;
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
    
    return {
      success: true,
      count: importedCount,
      errorCount: errorCount,
      errorDetails: errorDetails.slice(0, 10), // 最大10件のエラー詳細
      message: `${importedCount}件の${dataType}データをインポートしました (エラー: ${errorCount}件)`
    };
    
  } catch (error) {
    console.error(`Python版${dataType}データインポートエラー:`, error);
    return {
      success: false,
      message: `インポートエラー: ${error.toString()}`,
      errorDetails: [error.toString()]
    };
  }
}

/**
 * Python版フィールドとGAS版フィールドのマッピングを作成
 */
function createPythonFieldMapping(csvHeaders, targetFields, dataType) {
  const mapping = {};
  
  // Python版のフィールド名とGAS版のフィールド名の対応表
  const fieldMappings = {
    // 共通フィールド
    'id': 'ID',
    'project_name': '案件名',
    'payee': '支払い先',
    'payee_code': '支払い先コード',
    'amount': '金額',
    'payment_date': '支払日',
    'status': '状態',
    'client_name': 'クライアント名',
    'department': '部署',
    'project_status': '案件状態',
    'project_start_date': '案件開始日',
    'project_end_date': '案件終了日',
    'budget': '予算',
    'approver': '承認者',
    'urgency_level': '緊急度',
    
    // 支払いデータ固有
    'subject': '件名',
    'type': '種別',
    
    // 費用データ固有
    'source_type': 'ソース種別',
    'master_id': 'マスターID',
    
    // 費用マスター固有
    'payment_type': '種別',
    'start_date': '開始日',
    'end_date': '終了日',
    'broadcast_days': '放送曜日'
  };
  
  // CSVヘッダーをマッピング
  csvHeaders.forEach((csvHeader, csvIndex) => {
    const cleanHeader = csvHeader.trim();
    
    if (fieldMappings[cleanHeader]) {
      const gasFieldName = fieldMappings[cleanHeader];
      const targetIndex = targetFields.indexOf(gasFieldName);
      
      if (targetIndex !== -1) {
        mapping[targetIndex] = csvIndex;
        console.log(`マッピング: ${cleanHeader} (CSV列${csvIndex}) -> ${gasFieldName} (GAS列${targetIndex})`);
      }
    }
  });
  
  return mapping;
}

/**
 * マッピングされた行データを作成
 */
function createMappedRow(csvRow, fieldMapping, targetFields, dataType) {
  try {
    const mappedRow = new Array(targetFields.length).fill('');
    
    // フィールドマッピングに基づいてデータを設定
    Object.keys(fieldMapping).forEach(targetIndex => {
      const csvIndex = fieldMapping[targetIndex];
      if (csvIndex < csvRow.length) {
        mappedRow[parseInt(targetIndex)] = csvRow[csvIndex];
      }
    });
    
    // 必須フィールドの確認とデフォルト値設定
    validateAndSetDefaults(mappedRow, targetFields, dataType);
    
    // IDの生成（空の場合）
    if (!mappedRow[0]) {  // IDフィールド
      mappedRow[0] = generateId();
    }
    
    // 作成日時の設定
    const createdAtIndex = targetFields.indexOf('作成日時');
    if (createdAtIndex !== -1 && !mappedRow[createdAtIndex]) {
      mappedRow[createdAtIndex] = new Date();
    }
    
    return mappedRow;
    
  } catch (error) {
    console.error('行データマッピングエラー:', error);
    return null;
  }
}

/**
 * データの妥当性確認とデフォルト値設定
 */
function validateAndSetDefaults(row, fields, dataType) {
  // 基本的な必須フィールドチェック
  const projectNameIndex = fields.indexOf('案件名');
  const payeeIndex = fields.indexOf('支払い先');
  const amountIndex = fields.indexOf('金額');
  
  if (projectNameIndex !== -1 && !row[projectNameIndex]) {
    row[projectNameIndex] = `インポート案件_${new Date().getTime()}`;
  }
  
  if (payeeIndex !== -1 && !row[payeeIndex]) {
    row[payeeIndex] = '未設定';
  }
  
  if (amountIndex !== -1 && !row[amountIndex]) {
    row[amountIndex] = 0;
  }
  
  // 金額の数値変換
  if (amountIndex !== -1 && row[amountIndex] && typeof row[amountIndex] === 'string') {
    const numericAmount = parseFloat(row[amountIndex].replace(/[^\d.-]/g, ''));
    if (!isNaN(numericAmount)) {
      row[amountIndex] = numericAmount;
    }
  }
  
  // デフォルト値設定
  setDefaultValues(row, fields, getSheetNameByDataType(dataType));
}

/**
 * データタイプからシート名を取得
 */
function getSheetNameByDataType(dataType) {
  const mapping = {
    'payments': SHEET_NAMES.PAYMENTS,
    'expenses': SHEET_NAMES.EXPENSES,
    'expense_master': SHEET_NAMES.EXPENSE_MASTER
  };
  return mapping[dataType];
}

/**
 * 一括データ移行の実行（複数のCSVファイルを順番に処理）
 */
function executeBulkMigration(migrationData) {
  try {
    console.log('=== 一括データ移行開始 ===');
    
    const results = {
      timestamp: new Date(),
      migrations: [],
      totalImported: 0,
      totalErrors: 0,
      success: true
    };
    
    // データタイプ別に順次実行
    const dataTypes = ['payments', 'expenses', 'expense_master'];
    
    dataTypes.forEach(dataType => {
      if (migrationData[dataType] && migrationData[dataType].csvData) {
        try {
          console.log(`${dataType}データの移行を開始...`);
          
          const result = importFromPythonCsv(migrationData[dataType].csvData, dataType);
          
          results.migrations.push({
            dataType: dataType,
            success: result.success,
            count: result.count || 0,
            errorCount: result.errorCount || 0,
            message: result.message
          });
          
          if (result.success) {
            results.totalImported += result.count || 0;
            results.totalErrors += result.errorCount || 0;
          } else {
            results.success = false;
          }
          
          console.log(`${dataType}移行完了:`, result.message);
          
        } catch (error) {
          console.error(`${dataType}移行エラー:`, error);
          results.migrations.push({
            dataType: dataType,
            success: false,
            error: error.toString(),
            message: `${dataType}の移行に失敗しました`
          });
          results.success = false;
        }
      }
    });
    
    console.log('=== 一括データ移行完了 ===');
    console.log('移行サマリー:', results);
    
    const message = results.success 
      ? `一括移行完了: 合計${results.totalImported}件のデータを移行 (エラー: ${results.totalErrors}件)`
      : `一括移行中にエラーが発生しました`;
      
    return {
      success: results.success,
      results: results,
      message: message
    };
    
  } catch (error) {
    console.error('一括データ移行全体エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '一括データ移行の実行中にエラーが発生しました'
    };
  }
}

/**
 * 移行データの妥当性確認
 */
function validateMigrationData() {
  try {
    console.log('=== 移行データ妥当性確認開始 ===');
    
    const validation = {
      timestamp: new Date(),
      sheets: [],
      totalRecords: 0,
      issues: [],
      recommendations: []
    };
    
    const sheetConfigs = [
      { name: SHEET_NAMES.PAYMENTS, fields: UNIFIED_FIELDS.PAYMENTS },
      { name: SHEET_NAMES.EXPENSES, fields: UNIFIED_FIELDS.EXPENSES },
      { name: SHEET_NAMES.EXPENSE_MASTER, fields: UNIFIED_FIELDS.EXPENSE_MASTER }
    ];
    
    sheetConfigs.forEach(config => {
      try {
        const sheet = getOrCreateSheet(config.name, config.fields);
        const lastRow = sheet.getLastRow();
        const recordCount = Math.max(0, lastRow - 1); // ヘッダー行を除く
        
        const sheetValidation = {
          name: config.name,
          recordCount: recordCount,
          expectedFields: config.fields.length,
          issues: []
        };
        
        if (recordCount > 0) {
          // サンプルデータをチェック
          const sampleSize = Math.min(10, recordCount);
          const sampleData = sheet.getRange(2, 1, sampleSize, config.fields.length).getValues();
          
          sampleData.forEach((row, rowIndex) => {
            // 必須フィールドの空白チェック
            if (!row[0]) { // ID
              sheetValidation.issues.push(`行 ${rowIndex + 2}: IDが空白`);
            }
            
            // 案件名のチェック
            const projectNameIndex = config.fields.indexOf('案件名');
            if (projectNameIndex !== -1 && !row[projectNameIndex]) {
              sheetValidation.issues.push(`行 ${rowIndex + 2}: 案件名が空白`);
            }
            
            // 金額のチェック
            const amountIndex = config.fields.indexOf('金額');
            if (amountIndex !== -1 && row[amountIndex] && isNaN(parseFloat(row[amountIndex]))) {
              sheetValidation.issues.push(`行 ${rowIndex + 2}: 金額が数値ではありません`);
            }
          });
        }
        
        validation.sheets.push(sheetValidation);
        validation.totalRecords += recordCount;
        validation.issues = validation.issues.concat(sheetValidation.issues);
        
      } catch (error) {
        validation.issues.push(`${config.name}: シート確認エラー - ${error.toString()}`);
      }
    });
    
    // 推奨事項の生成
    if (validation.totalRecords === 0) {
      validation.recommendations.push('データがありません。移行を実行してください。');
    }
    
    if (validation.issues.length > 0) {
      validation.recommendations.push('データに問題があります。クリーンアップを検討してください。');
    }
    
    if (validation.totalRecords > 1000) {
      validation.recommendations.push('データが大量です。パフォーマンスに注意してください。');
    }
    
    console.log('=== 移行データ妥当性確認完了 ===');
    console.log('確認結果:', validation);
    
    return {
      success: true,
      validation: validation,
      message: `確認完了: 合計${validation.totalRecords}件のデータ、${validation.issues.length}件の問題`
    };
    
  } catch (error) {
    console.error('移行データ妥当性確認エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '移行データの妥当性確認中にエラーが発生しました'
    };
  }
}

/**
 * 移行前のバックアップ作成
 */
function createMigrationBackup() {
  try {
    console.log('=== 移行前バックアップ作成開始 ===');
    
    const sourceSpreadsheet = getSpreadsheet();
    const backupName = `移行前バックアップ_${Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd_HHmmss')}`;
    
    const backupSpreadsheet = sourceSpreadsheet.copy(backupName);
    
    console.log('移行前バックアップ作成完了:', backupName);
    
    return {
      success: true,
      backupId: backupSpreadsheet.getId(),
      backupUrl: backupSpreadsheet.getUrl(),
      backupName: backupName,
      message: '移行前バックアップを作成しました'
    };
    
  } catch (error) {
    console.error('移行前バックアップ作成エラー:', error);
    return {
      success: false,
      error: error.toString(),
      message: '移行前バックアップの作成に失敗しました'
    };
  }
}