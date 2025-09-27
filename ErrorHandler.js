/**
 * 包括的なエラーハンドリング・パフォーマンス監視システム
 */

// エラーログ設定
const ERROR_CONFIG = {
  maxLogEntries: 1000,
  retainDays: 30,
  alertThresholds: {
    errorRate: 0.1, // 10%のエラー率で警告
    responseTime: 5000, // 5秒以上で警告
    memoryUsage: 80 // 80%以上で警告
  }
};

/**
 * 統一エラーハンドラー
 */
function handleError(error, context = {}) {
  const errorInfo = {
    timestamp: new Date(),
    message: error.message || error.toString(),
    stack: error.stack,
    context: context,
    type: error.name || 'UnknownError',
    severity: determineSeverity(error),
    sessionId: getSessionId(),
    userId: getUserId()
  };
  
  // エラーログに記録
  logError(errorInfo);
  
  // 重要度に応じた処理
  switch (errorInfo.severity) {
    case 'CRITICAL':
      handleCriticalError(errorInfo);
      break;
    case 'HIGH':
      handleHighError(errorInfo);
      break;
    case 'MEDIUM':
      handleMediumError(errorInfo);
      break;
    case 'LOW':
      handleLowError(errorInfo);
      break;
  }
  
  // クライアント向けエラーレスポンスを生成
  return generateErrorResponse(errorInfo);
}

/**
 * エラーの重要度を判定
 */
function determineSeverity(error) {
  const message = (error.message || '').toLowerCase();
  
  // クリティカルエラー
  if (message.includes('permission denied') || 
      message.includes('quota exceeded') ||
      message.includes('service unavailable')) {
    return 'CRITICAL';
  }
  
  // 高重要度エラー
  if (message.includes('no item with the given id') ||
      message.includes('invalid spreadsheet') ||
      message.includes('database') ||
      message.includes('connection')) {
    return 'HIGH';
  }
  
  // 中重要度エラー
  if (message.includes('invalid parameter') ||
      message.includes('validation failed') ||
      message.includes('format error')) {
    return 'MEDIUM';
  }
  
  // 低重要度エラー（デフォルト）
  return 'LOW';
}

/**
 * エラーログの記録
 */
function logError(errorInfo) {
  try {
    const errorSheet = getOrCreateErrorLogSheet();
    
    const row = [
      errorInfo.timestamp,
      errorInfo.type,
      errorInfo.severity,
      errorInfo.message,
      JSON.stringify(errorInfo.context),
      errorInfo.sessionId,
      errorInfo.userId,
      errorInfo.stack || ''
    ];
    
    errorSheet.appendRow(row);
    
    // 古いログエントリをクリーンアップ
    cleanupOldErrors(errorSheet);
    
  } catch (logError) {
    console.error('エラーログ記録失敗:', logError);
    // フォールバック: コンソールログのみ
    console.error('Original error:', errorInfo);
  }
}

/**
 * エラーログシートの取得・作成
 */
function getOrCreateErrorLogSheet() {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName('エラーログ');
  
  if (!sheet) {
    sheet = ss.insertSheet('エラーログ');
    const headers = [
      '発生日時', 'エラータイプ', '重要度', 'メッセージ', 
      'コンテキスト', 'セッションID', 'ユーザーID', 'スタックトレース'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  
  return sheet;
}

/**
 * 古いエラーログのクリーンアップ
 */
function cleanupOldErrors(sheet) {
  try {
    const lastRow = sheet.getLastRow();
    if (lastRow <= ERROR_CONFIG.maxLogEntries + 1) return;
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - ERROR_CONFIG.retainDays);
    
    const data = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    let deleteCount = 0;
    
    for (let i = 0; i < data.length; i++) {
      const logDate = new Date(data[i][0]);
      if (logDate < cutoffDate) {
        deleteCount++;
      } else {
        break;
      }
    }
    
    if (deleteCount > 0) {
      sheet.deleteRows(2, deleteCount);
      console.log(`${deleteCount}件の古いエラーログを削除しました`);
    }
    
  } catch (cleanupError) {
    console.error('エラーログクリーンアップ失敗:', cleanupError);
  }
}

/**
 * 重要度別エラー処理
 */
function handleCriticalError(errorInfo) {
  console.error('CRITICAL ERROR:', errorInfo);
  
  // 管理者に通知
  sendErrorNotification(errorInfo);
  
  // システム状態をチェック
  checkSystemHealth();
}

function handleHighError(errorInfo) {
  console.error('HIGH ERROR:', errorInfo);
  
  // リトライ可能な場合は自動回復を試行
  if (isRetryableError(errorInfo)) {
    scheduleRetry(errorInfo.context);
  }
}

function handleMediumError(errorInfo) {
  console.warn('MEDIUM ERROR:', errorInfo);
  
  // 統計に記録
  updateErrorStatistics(errorInfo);
}

function handleLowError(errorInfo) {
  console.log('LOW ERROR:', errorInfo);
}

/**
 * エラー通知の送信
 */
function sendErrorNotification(errorInfo) {
  try {
    // GmailまたはSlack通知を送信
    const subject = `[CRITICAL] システムエラー発生 - ${errorInfo.type}`;
    const body = `
重要度: ${errorInfo.severity}
発生日時: ${errorInfo.timestamp}
エラータイプ: ${errorInfo.type}
メッセージ: ${errorInfo.message}
コンテキスト: ${JSON.stringify(errorInfo.context, null, 2)}

詳細なスタックトレース:
${errorInfo.stack}
    `;
    
    // PropertiesServiceから管理者メールアドレスを取得
    const adminEmail = PropertiesService.getScriptProperties().getProperty('ADMIN_EMAIL');
    if (adminEmail) {
      GmailApp.sendEmail(adminEmail, subject, body);
    }
    
  } catch (notificationError) {
    console.error('エラー通知送信失敗:', notificationError);
  }
}

/**
 * リトライ可能なエラーかどうかを判定
 */
function isRetryableError(errorInfo) {
  const retryableErrors = [
    'service unavailable',
    'timeout',
    'rate limit',
    'temporary failure'
  ];
  
  const message = errorInfo.message.toLowerCase();
  return retryableErrors.some(error => message.includes(error));
}

/**
 * クライアント向けエラーレスポンス生成
 */
function generateErrorResponse(errorInfo) {
  // セキュリティ上、内部詳細は隠す
  const clientMessage = getClientFriendlyMessage(errorInfo);
  
  return {
    success: false,
    error: {
      type: errorInfo.type,
      message: clientMessage,
      timestamp: errorInfo.timestamp,
      code: generateErrorCode(errorInfo)
    },
    data: null,
    // デバッグ情報（開発環境のみ）
    debug: isDebugMode() ? {
      originalMessage: errorInfo.message,
      context: errorInfo.context
    } : undefined
  };
}

/**
 * クライアント向けエラーメッセージの生成
 */
function getClientFriendlyMessage(errorInfo) {
  const messageMap = {
    'permission denied': 'アクセス権限がありません。管理者にお問い合わせください。',
    'quota exceeded': 'システムの使用量上限に達しました。しばらく待ってから再試行してください。',
    'service unavailable': 'サービスが一時的に利用できません。しばらく待ってから再試行してください。',
    'no item with the given id': '指定されたデータが見つかりません。',
    'invalid parameter': '入力パラメータが正しくありません。',
    'validation failed': 'データの検証に失敗しました。入力内容を確認してください。'
  };
  
  const message = errorInfo.message.toLowerCase();
  for (const [key, friendlyMessage] of Object.entries(messageMap)) {
    if (message.includes(key)) {
      return friendlyMessage;
    }
  }
  
  return '処理中にエラーが発生しました。再試行してもエラーが続く場合は、管理者にお問い合わせください。';
}

/**
 * エラーコードの生成
 */
function generateErrorCode(errorInfo) {
  const typeCode = {
    'TypeError': 'T001',
    'ReferenceError': 'R001', 
    'RangeError': 'RG001',
    'SyntaxError': 'S001',
    'UnknownError': 'U001'
  };
  
  const severityCode = {
    'CRITICAL': '4',
    'HIGH': '3',
    'MEDIUM': '2', 
    'LOW': '1'
  };
  
  const timestamp = errorInfo.timestamp.getTime().toString().slice(-4);
  
  return `${typeCode[errorInfo.type] || 'U001'}-${severityCode[errorInfo.severity]}${timestamp}`;
}

/**
 * パフォーマンス監視
 */
function monitorPerformance(functionName, startTime, endTime, context = {}) {
  const executionTime = endTime - startTime;
  
  const perfInfo = {
    functionName,
    executionTime,
    timestamp: new Date(),
    context
  };
  
  // 閾値を超えた場合は警告
  if (executionTime > ERROR_CONFIG.alertThresholds.responseTime) {
    console.warn(`Performance warning: ${functionName} took ${executionTime}ms`);
    logPerformanceIssue(perfInfo);
  }
  
  // パフォーマンス統計を更新
  updatePerformanceStats(perfInfo);
  
  return perfInfo;
}

/**
 * パフォーマンス問題のログ記録
 */
function logPerformanceIssue(perfInfo) {
  try {
    const perfSheet = getOrCreatePerformanceLogSheet();
    
    const row = [
      perfInfo.timestamp,
      perfInfo.functionName,
      perfInfo.executionTime,
      JSON.stringify(perfInfo.context),
      'SLOW_EXECUTION'
    ];
    
    perfSheet.appendRow(row);
    
  } catch (error) {
    console.error('パフォーマンスログ記録失敗:', error);
  }
}

/**
 * パフォーマンスログシートの取得・作成
 */
function getOrCreatePerformanceLogSheet() {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName('パフォーマンスログ');
  
  if (!sheet) {
    sheet = ss.insertSheet('パフォーマンスログ');
    const headers = ['発生日時', '関数名', '実行時間(ms)', 'コンテキスト', 'タイプ'];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  
  return sheet;
}

/**
 * システムヘルスチェック
 */
function checkSystemHealth() {
  try {
    const healthCheck = {
      timestamp: new Date(),
      spreadsheetAccess: false,
      dataIntegrity: false,
      memoryUsage: 0,
      errorRate: 0,
      avgResponseTime: 0
    };
    
    // スプレッドシートアクセスチェック
    try {
      const ss = getSpreadsheet();
      ss.getName();
      healthCheck.spreadsheetAccess = true;
    } catch (e) {
      healthCheck.spreadsheetAccess = false;
    }
    
    // データ整合性チェック
    try {
      const integrityResult = checkDataIntegrity();
      healthCheck.dataIntegrity = integrityResult.success;
    } catch (e) {
      healthCheck.dataIntegrity = false;
    }
    
    // エラー統計の取得
    const errorStats = getErrorStatistics();
    healthCheck.errorRate = errorStats.recentErrorRate || 0;
    healthCheck.avgResponseTime = errorStats.avgResponseTime || 0;
    
    // ヘルスチェック結果をログ
    logHealthCheck(healthCheck);
    
    return healthCheck;
    
  } catch (error) {
    console.error('システムヘルスチェック失敗:', error);
    return {
      timestamp: new Date(),
      spreadsheetAccess: false,
      dataIntegrity: false,
      error: error.toString()
    };
  }
}

/**
 * ヘルスチェック結果のログ記録
 */
function logHealthCheck(healthCheck) {
  try {
    const healthSheet = getOrCreateHealthLogSheet();
    
    const row = [
      healthCheck.timestamp,
      healthCheck.spreadsheetAccess ? 'OK' : 'NG',
      healthCheck.dataIntegrity ? 'OK' : 'NG',
      healthCheck.errorRate,
      healthCheck.avgResponseTime,
      healthCheck.error || ''
    ];
    
    healthSheet.appendRow(row);
    
    // 古いヘルスログをクリーンアップ
    cleanupOldHealthLogs(healthSheet);
    
  } catch (error) {
    console.error('ヘルスログ記録失敗:', error);
  }
}

/**
 * ヘルスログシートの取得・作成
 */
function getOrCreateHealthLogSheet() {
  const ss = getSpreadsheet();
  let sheet = ss.getSheetByName('ヘルスチェック');
  
  if (!sheet) {
    sheet = ss.insertSheet('ヘルスチェック');
    const headers = [
      '実行日時', 'スプレッドシート', 'データ整合性', 
      'エラー率(%)', '平均応答時間(ms)', 'エラー詳細'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  
  return sheet;
}

/**
 * エラー統計の取得
 */
function getErrorStatistics() {
  try {
    const errorSheet = getOrCreateErrorLogSheet();
    const lastRow = errorSheet.getLastRow();
    
    if (lastRow <= 1) {
      return { recentErrorRate: 0, avgResponseTime: 0, totalErrors: 0 };
    }
    
    // 直近24時間のエラーを分析
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    const data = errorSheet.getRange(2, 1, lastRow - 1, 3).getValues();
    const recentErrors = data.filter(row => {
      const errorTime = new Date(row[0]);
      return errorTime > oneDayAgo;
    });
    
    return {
      recentErrorRate: recentErrors.length / Math.max(data.length, 1),
      totalErrors: data.length,
      recentErrors: recentErrors.length,
      criticalErrors: recentErrors.filter(row => row[2] === 'CRITICAL').length
    };
    
  } catch (error) {
    console.error('エラー統計取得失敗:', error);
    return { recentErrorRate: 0, avgResponseTime: 0, totalErrors: 0 };
  }
}

/**
 * ユーティリティ関数
 */
function getSessionId() {
  try {
    return Session.getTemporaryActiveUserKey() || 'unknown';
  } catch (e) {
    return 'unknown';
  }
}

function getUserId() {
  try {
    return Session.getActiveUser().getEmail() || 'anonymous';
  } catch (e) {
    return 'anonymous';
  }
}

function isDebugMode() {
  try {
    const debugMode = PropertiesService.getScriptProperties().getProperty('DEBUG_MODE');
    return debugMode === 'true';
  } catch (e) {
    return false;
  }
}

/**
 * 関数実行の包括的なラッパー
 */
function executeWithMonitoring(func, functionName, ...args) {
  const startTime = new Date();
  const context = {
    functionName,
    arguments: args.length,
    startTime: startTime.toISOString()
  };
  
  try {
    console.log(`実行開始: ${functionName}`);
    
    const result = func.apply(null, args);
    const endTime = new Date();
    
    // パフォーマンス監視
    monitorPerformance(functionName, startTime, endTime, context);
    
    console.log(`実行完了: ${functionName} (${endTime - startTime}ms)`);
    
    return result;
    
  } catch (error) {
    const endTime = new Date();
    context.executionTime = endTime - startTime;
    context.failed = true;
    
    console.error(`実行エラー: ${functionName}`, error);
    
    // エラーハンドリング
    return handleError(error, context);
  }
}

// 古いログのクリーンアップ
function cleanupOldHealthLogs(sheet) {
  try {
    const lastRow = sheet.getLastRow();
    if (lastRow <= 100) return; // 100行以下は保持
    
    const deleteCount = lastRow - 100;
    sheet.deleteRows(2, deleteCount);
    console.log(`${deleteCount}件の古いヘルスログを削除しました`);
    
  } catch (error) {
    console.error('ヘルスログクリーンアップ失敗:', error);
  }
}