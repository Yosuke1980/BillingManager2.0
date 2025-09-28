/**
 * パフォーマンス最適化システム
 */

// パフォーマンス設定
const PERFORMANCE_CONFIG = {
  // キャッシュ設定
  cache: {
    enabled: true,
    defaultTTL: 300, // 5分
    maxSize: 100 // 最大100エントリ
  },
  
  // バッチ処理設定  
  batch: {
    enabled: true,
    maxBatchSize: 100,
    batchTimeout: 1000 // 1秒
  },
  
  // 非同期処理設定
  async: {
    enabled: true,
    maxConcurrency: 5
  },
  
  // データ圧縮設定
  compression: {
    enabled: true,
    threshold: 1000 // 1000文字以上で圧縮
  }
};

/**
 * キャッシュマネージャー
 */
class CacheManager {
  constructor() {
    this.cache = new Map();
    this.expiry = new Map();
    this.hitCount = 0;
    this.missCount = 0;
  }
  
  get(key) {
    // 有効期限チェック
    if (this.expiry.has(key) && this.expiry.get(key) < Date.now()) {
      this.cache.delete(key);
      this.expiry.delete(key);
      this.missCount++;
      return null;
    }
    
    if (this.cache.has(key)) {
      this.hitCount++;
      return this.cache.get(key);
    }
    
    this.missCount++;
    return null;
  }
  
  set(key, value, ttl = PERFORMANCE_CONFIG.cache.defaultTTL) {
    // キャッシュサイズ制限
    if (this.cache.size >= PERFORMANCE_CONFIG.cache.maxSize) {
      this.evictOldest();
    }
    
    this.cache.set(key, value);
    this.expiry.set(key, Date.now() + (ttl * 1000));
  }
  
  evictOldest() {
    const oldestKey = this.cache.keys().next().value;
    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.expiry.delete(oldestKey);
    }
  }
  
  clear() {
    this.cache.clear();
    this.expiry.clear();
  }
  
  getStats() {
    return {
      size: this.cache.size,
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: this.hitCount / (this.hitCount + this.missCount) || 0
    };
  }
}

// グローバルキャッシュインスタンス
const globalCache = new CacheManager();

/**
 * バッチ処理マネージャー
 */
class BatchProcessor {
  constructor() {
    this.batches = new Map();
    this.timers = new Map();
  }
  
  add(batchKey, item, processor) {
    if (!this.batches.has(batchKey)) {
      this.batches.set(batchKey, []);
    }
    
    this.batches.get(batchKey).push(item);
    
    // バッチサイズまたはタイムアウトで処理実行
    if (this.batches.get(batchKey).length >= PERFORMANCE_CONFIG.batch.maxBatchSize) {
      this.processBatch(batchKey, processor);
    } else if (!this.timers.has(batchKey)) {
      this.timers.set(batchKey, setTimeout(() => {
        this.processBatch(batchKey, processor);
      }, PERFORMANCE_CONFIG.batch.batchTimeout));
    }
  }
  
  processBatch(batchKey, processor) {
    const batch = this.batches.get(batchKey);
    if (batch && batch.length > 0) {
      try {
        processor(batch);
      } catch (error) {
        console.error(`バッチ処理エラー [${batchKey}]:`, error);
      }
      
      this.batches.delete(batchKey);
      if (this.timers.has(batchKey)) {
        clearTimeout(this.timers.get(batchKey));
        this.timers.delete(batchKey);
      }
    }
  }
  
  flush(batchKey, processor) {
    if (this.batches.has(batchKey)) {
      this.processBatch(batchKey, processor);
    }
  }
}

const globalBatchProcessor = new BatchProcessor();

/**
 * データ圧縮ユーティリティ
 */
function compressData(data) {
  if (!PERFORMANCE_CONFIG.compression.enabled) {
    return data;
  }
  
  const dataString = JSON.stringify(data);
  if (dataString.length < PERFORMANCE_CONFIG.compression.threshold) {
    return data;
  }
  
  try {
    // 簡易圧縮（重複データの除去）
    const compressed = {
      __compressed: true,
      data: compressArray(data)
    };
    
    const compressedString = JSON.stringify(compressed);
    if (compressedString.length < dataString.length) {
      console.log(`データ圧縮: ${dataString.length} -> ${compressedString.length} bytes (${Math.round((1 - compressedString.length / dataString.length) * 100)}% 削減)`);
      return compressed;
    }
    
  } catch (error) {
    console.warn('データ圧縮失敗:', error);
  }
  
  return data;
}

/**
 * 配列データの圧縮
 */
function compressArray(array) {
  if (!Array.isArray(array) || array.length === 0) {
    return array;
  }
  
  // 共通キーを抽出
  const keys = Object.keys(array[0] || {});
  
  // 値のみの配列に変換
  const values = array.map(item => keys.map(key => item[key]));
  
  return {
    keys: keys,
    values: values
  };
}

/**
 * データの展開
 */
function decompressData(data) {
  if (!data || !data.__compressed) {
    return data;
  }
  
  try {
    return decompressArray(data.data);
  } catch (error) {
    console.error('データ展開エラー:', error);
    return data;
  }
}

/**
 * 配列データの展開
 */
function decompressArray(compressedArray) {
  if (!compressedArray.keys || !compressedArray.values) {
    return compressedArray;
  }
  
  return compressedArray.values.map(valueArray => {
    const item = {};
    compressedArray.keys.forEach((key, index) => {
      item[key] = valueArray[index];
    });
    return item;
  });
}

/**
 * 最適化されたデータ取得関数
 */
function getOptimizedPaymentData(searchTerm = '') {
  const cacheKey = `payments_${searchTerm}`;
  const startTime = Date.now();
  
  try {
    // キャッシュチェック
    const cachedData = globalCache.get(cacheKey);
    if (cachedData) {
      console.log(`キャッシュヒット: ${cacheKey} (${Date.now() - startTime}ms)`);
      return decompressData(cachedData);
    }
    
    // データ取得
    const result = getPaymentData(searchTerm);
    
    if (result.success && result.data) {
      // キャッシュに保存（圧縮して）
      const compressedData = compressData(result);
      globalCache.set(cacheKey, compressedData);
      
      console.log(`データ取得完了: ${cacheKey} (${Date.now() - startTime}ms)`);
    }
    
    return result;
    
  } catch (error) {
    console.error('最適化データ取得エラー:', error);
    return handleError(error, { function: 'getOptimizedPaymentData', searchTerm });
  }
}

/**
 * 非同期データ読み込み
 */
function loadDataAsync(dataSources) {
  if (!PERFORMANCE_CONFIG.async.enabled || dataSources.length <= 1) {
    // 同期的に順次処理
    return dataSources.map(source => source.loader());
  }
  
  // 並列処理をシミュレート（GASでは真の非同期は制限されるため）
  const results = [];
  const errors = [];
  
  try {
    dataSources.forEach((source, index) => {
      try {
        const startTime = Date.now();
        const result = source.loader();
        const endTime = Date.now();
        
        results[index] = {
          ...result,
          loadTime: endTime - startTime,
          source: source.name
        };
      } catch (error) {
        errors.push({
          index,
          source: source.name,
          error: error.toString()
        });
        results[index] = {
          success: false,
          error: error.toString(),
          source: source.name
        };
      }
    });
    
    return {
      results,
      errors,
      totalSources: dataSources.length,
      successCount: results.filter(r => r.success).length
    };
    
  } catch (error) {
    console.error('非同期データ読み込みエラー:', error);
    return {
      results: [],
      errors: [{ error: error.toString() }],
      totalSources: dataSources.length,
      successCount: 0
    };
  }
}

/**
 * 大量データの効率的な処理
 */
function processLargeDataset(data, processor, options = {}) {
  const {
    batchSize = 100,
    progressCallback = null,
    maxRetries = 3
  } = options;
  
  const results = [];
  const errors = [];
  const totalItems = data.length;
  let processedItems = 0;
  
  console.log(`大量データ処理開始: ${totalItems}件`);
  
  for (let i = 0; i < totalItems; i += batchSize) {
    const batch = data.slice(i, i + batchSize);
    let retryCount = 0;
    let batchSuccess = false;
    
    while (retryCount < maxRetries && !batchSuccess) {
      try {
        const batchResults = processor(batch);
        results.push(...batchResults);
        batchSuccess = true;
        processedItems += batch.length;
        
        // 進捗報告
        if (progressCallback) {
          progressCallback({
            processed: processedItems,
            total: totalItems,
            percentage: Math.round((processedItems / totalItems) * 100)
          });
        }
        
        // CPUを他の処理に譲る（簡易的な非同期処理）
        if (i % (batchSize * 10) === 0) {
          Utilities.sleep(10);
        }
        
      } catch (error) {
        retryCount++;
        console.warn(`バッチ処理エラー (試行 ${retryCount}/${maxRetries}):`, error);
        
        if (retryCount >= maxRetries) {
          errors.push({
            batchIndex: Math.floor(i / batchSize),
            items: batch.map(item => item.id || item.ID),
            error: error.toString()
          });
          processedItems += batch.length; // 失敗分も進捗に含める
        } else {
          // 少し待ってからリトライ
          Utilities.sleep(1000 * retryCount);
        }
      }
    }
  }
  
  console.log(`大量データ処理完了: 成功 ${results.length}件, エラー ${errors.length}件`);
  
  return {
    results,
    errors,
    totalProcessed: processedItems,
    successRate: results.length / totalItems
  };
}

/**
 * スプレッドシートの最適化された読み書き
 */
function optimizedSheetRead(sheet, startRow, numRows, numCols) {
  const cacheKey = `sheet_${sheet.getName()}_${startRow}_${numRows}_${numCols}`;
  
  // キャッシュチェック
  const cachedData = globalCache.get(cacheKey);
  if (cachedData) {
    return decompressData(cachedData);
  }
  
  try {
    const data = sheet.getRange(startRow, 1, numRows, numCols).getValues();
    
    // キャッシュに保存
    globalCache.set(cacheKey, compressData(data), 60); // 1分間キャッシュ
    
    return data;
    
  } catch (error) {
    console.error('最適化シート読み込みエラー:', error);
    throw error;
  }
}

/**
 * バッチでのスプレッドシート書き込み
 */
function batchSheetWrite(sheet, data, startRow = 2) {
  if (!data || data.length === 0) {
    return { success: true, written: 0 };
  }
  
  const batchSize = PERFORMANCE_CONFIG.batch.maxBatchSize;
  let totalWritten = 0;
  
  try {
    for (let i = 0; i < data.length; i += batchSize) {
      const batch = data.slice(i, i + batchSize);
      const range = sheet.getRange(startRow + i, 1, batch.length, batch[0].length);
      range.setValues(batch);
      totalWritten += batch.length;
      
      // 大量データの場合は少し休む
      if (i > 0 && i % (batchSize * 5) === 0) {
        Utilities.sleep(100);
      }
    }
    
    console.log(`バッチ書き込み完了: ${totalWritten}行`);
    
    // 関連キャッシュをクリア
    clearSheetCache(sheet.getName());
    
    return { success: true, written: totalWritten };
    
  } catch (error) {
    console.error('バッチ書き込みエラー:', error);
    return { success: false, written: totalWritten, error: error.toString() };
  }
}

/**
 * シート関連キャッシュのクリア
 */
function clearSheetCache(sheetName) {
  const keysToDelete = [];
  
  for (const [key] of globalCache.cache) {
    if (key.startsWith(`sheet_${sheetName}_`)) {
      keysToDelete.push(key);
    }
  }
  
  keysToDelete.forEach(key => {
    globalCache.cache.delete(key);
    globalCache.expiry.delete(key);
  });
  
  console.log(`シートキャッシュクリア: ${sheetName} (${keysToDelete.length}件)`);
}

/**
 * メモリ使用量の監視
 */
function monitorMemoryUsage() {
  try {
    // GASでは直接メモリ使用量を取得できないため、推定値を計算
    const cacheStats = globalCache.getStats();
    const estimatedMemoryUsage = {
      cacheSize: cacheStats.size,
      cacheHitRate: cacheStats.hitRate,
      timestamp: new Date()
    };
    
    console.log('推定メモリ使用量:', estimatedMemoryUsage);
    
    // メモリ使用量が多い場合はキャッシュをクリア
    if (cacheStats.size > PERFORMANCE_CONFIG.cache.maxSize * 0.8) {
      console.warn('メモリ使用量が多いためキャッシュをクリア');
      globalCache.clear();
    }
    
    return estimatedMemoryUsage;
    
  } catch (error) {
    console.error('メモリ監視エラー:', error);
    return { error: error.toString() };
  }
}

/**
 * パフォーマンス統計の取得
 */
function getPerformanceStats() {
  try {
    return {
      cache: globalCache.getStats(),
      memory: monitorMemoryUsage(),
      timestamp: new Date(),
      config: PERFORMANCE_CONFIG
    };
  } catch (error) {
    console.error('パフォーマンス統計取得エラー:', error);
    return { error: error.toString() };
  }
}

/**
 * パフォーマンス最適化の設定
 */
function configurePerformance(newConfig) {
  try {
    Object.assign(PERFORMANCE_CONFIG, newConfig);
    console.log('パフォーマンス設定を更新:', PERFORMANCE_CONFIG);
    return { success: true, config: PERFORMANCE_CONFIG };
  } catch (error) {
    console.error('パフォーマンス設定エラー:', error);
    return { success: false, error: error.toString() };
  }
}

/**
 * 定期的なメンテナンス
 */
function performMaintenance() {
  try {
    console.log('=== 定期メンテナンス開始 ===');
    
    // キャッシュのクリーンアップ
    const beforeCacheSize = globalCache.cache.size;
    globalCache.clear();
    console.log(`キャッシュクリーンアップ: ${beforeCacheSize}件削除`);
    
    // バッチ処理の強制フラッシュ
    for (const [batchKey] of globalBatchProcessor.batches) {
      globalBatchProcessor.flush(batchKey, (batch) => {
        console.log(`バッチ強制処理: ${batchKey} (${batch.length}件)`);
      });
    }
    
    // メモリ監視
    const memoryUsage = monitorMemoryUsage();
    
    // パフォーマンス統計の更新
    const stats = getPerformanceStats();
    
    console.log('=== 定期メンテナンス完了 ===');
    
    return {
      success: true,
      clearedCache: beforeCacheSize,
      memoryUsage,
      stats,
      timestamp: new Date()
    };
    
  } catch (error) {
    console.error('メンテナンスエラー:', error);
    return { success: false, error: error.toString() };
  }
}

// 自動メンテナンスのセットアップ（トリガー使用）
function setupPerformanceTriggers() {
  try {
    // 既存のトリガーを削除
    const triggers = ScriptApp.getProjectTriggers();
    triggers.forEach(trigger => {
      if (trigger.getHandlerFunction() === 'performMaintenance') {
        ScriptApp.deleteTrigger(trigger);
      }
    });
    
    // 1時間ごとのメンテナンストリガーを作成
    ScriptApp.newTrigger('performMaintenance')
      .timeBased()
      .everyHours(1)
      .create();
      
    console.log('パフォーマンストリガーを設定しました');
    return { success: true };
    
  } catch (error) {
    console.error('トリガー設定エラー:', error);
    return { success: false, error: error.toString() };
  }
}