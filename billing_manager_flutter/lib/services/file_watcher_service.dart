import 'dart:io';
import 'dart:async';
import 'package:watcher/watcher.dart';
import 'package:path/path.dart' as path;
import 'csv_import_service.dart';
import 'database_service.dart';

class FileWatcherService {
  final DatabaseService _databaseService;
  late CsvImportService _csvImportService;
  
  DirectoryWatcher? _watcher;
  StreamSubscription<WatchEvent>? _subscription;
  
  String _watchedDirectory = '';
  bool _isWatching = false;
  
  // ファイル処理の重複を防ぐ
  final Set<String> _processingFiles = <String>{};
  final Map<String, DateTime> _lastProcessed = <String, DateTime>{};
  
  // コールバック関数
  Function(String action, Map<String, dynamic> data)? onFileDetected;
  Function(String message)? onStatusChanged;
  
  FileWatcherService(this._databaseService) {
    _csvImportService = CsvImportService(_databaseService);
  }
  
  /// ファイル監視を開始
  Future<bool> startWatching(String directory) async {
    try {
      if (_isWatching) {
        await stopWatching();
      }
      
      final dir = Directory(directory);
      if (!await dir.exists()) {
        _notifyStatus('監視対象ディレクトリが存在しません: $directory');
        return false;
      }
      
      _watchedDirectory = directory;
      _watcher = DirectoryWatcher(directory);
      
      _subscription = _watcher!.events.listen(
        _onFileEvent,
        onError: (error) {
          _notifyStatus('ファイル監視エラー: $error');
        },
      );
      
      _isWatching = true;
      _notifyStatus('ファイル監視を開始しました: $directory');
      return true;
      
    } catch (e) {
      _notifyStatus('ファイル監視の開始に失敗しました: $e');
      return false;
    }
  }
  
  /// ファイル監視を停止
  Future<void> stopWatching() async {
    if (_subscription != null) {
      await _subscription!.cancel();
      _subscription = null;
    }
    
    _watcher = null;
    _isWatching = false;
    _processingFiles.clear();
    _notifyStatus('ファイル監視を停止しました');
  }
  
  /// 監視状態を取得
  bool get isWatching => _isWatching;
  String get watchedDirectory => _watchedDirectory;
  
  /// ファイル変更イベントを処理
  void _onFileEvent(WatchEvent event) {
    final filePath = event.path;
    final fileName = path.basename(filePath);
    
    // CSVファイルのみを対象とする
    if (!fileName.toLowerCase().endsWith('.csv')) {
      return;
    }
    
    // ファイル処理中の場合はスキップ
    if (_processingFiles.contains(filePath)) {
      return;
    }
    
    // 短時間の重複イベントを防ぐ
    final now = DateTime.now();
    final lastProcessed = _lastProcessed[filePath];
    if (lastProcessed != null && 
        now.difference(lastProcessed).inSeconds < 2) {
      return;
    }
    
    _lastProcessed[filePath] = now;
    
    // ファイルイベントを通知
    _notifyFileDetected(event.type.toString(), {
      'file_path': filePath,
      'filename': fileName,
      'type': event.type.toString(),
      'timestamp': now.toIso8601String(),
    });
    
    // CSVファイルの場合は自動インポートを試行
    if (event.type == ChangeType.ADD || event.type == ChangeType.MODIFY) {
      _processCSVFile(filePath);
    }
  }
  
  /// CSVファイルを自動処理
  Future<void> _processCSVFile(String filePath) async {
    _processingFiles.add(filePath);
    
    try {
      // ファイルの書き込み完了を待つ
      await _waitForFileCompletion(filePath);
      
      _notifyStatus('CSVファイルを処理中: ${path.basename(filePath)}');
      
      // ファイル名から支払いデータか費用データかを判定
      final fileName = path.basename(filePath).toLowerCase();
      
      if (fileName.contains('payment') || fileName.contains('billing') || 
          fileName.contains('支払') || fileName.contains('請求')) {
        // 支払いデータとして処理
        final result = await _csvImportService.importPaymentsFromCsv();
        if (result.success) {
          _notifyStatus('支払いデータを自動インポートしました: ${result.successCount}件');
        } else {
          _notifyStatus('支払いデータのインポートに失敗: ${result.errorMessage}');
        }
      } else if (fileName.contains('expense') || fileName.contains('cost') || 
                 fileName.contains('費用') || fileName.contains('経費')) {
        // 費用データとして処理
        final result = await _csvImportService.importExpensesFromCsv();
        if (result.success) {
          _notifyStatus('費用データを自動インポートしました: ${result.successCount}件');
        } else {
          _notifyStatus('費用データのインポートに失敗: ${result.errorMessage}');
        }
      } else {
        _notifyStatus('CSVファイルの種類を判定できませんでした: ${path.basename(filePath)}');
      }
      
    } catch (e) {
      _notifyStatus('CSVファイル処理中にエラーが発生: $e');
    } finally {
      _processingFiles.remove(filePath);
    }
  }
  
  /// ファイル書き込み完了まで待機
  Future<void> _waitForFileCompletion(String filePath) async {
    final file = File(filePath);
    int previousSize = 0;
    int stableCount = 0;
    
    // 最大30秒間、ファイルサイズが安定するまで待機
    for (int i = 0; i < 30; i++) {
      try {
        if (!await file.exists()) {
          return;
        }
        
        final currentSize = await file.length();
        
        if (currentSize == previousSize) {
          stableCount++;
          if (stableCount >= 3) { // 3秒間安定していれば完了とみなす
            break;
          }
        } else {
          stableCount = 0;
          previousSize = currentSize;
        }
        
        await Future.delayed(const Duration(seconds: 1));
        
      } catch (e) {
        // ファイルアクセスエラー（他のプロセスが使用中など）
        await Future.delayed(const Duration(seconds: 1));
      }
    }
  }
  
  /// ファイル検出通知
  void _notifyFileDetected(String action, Map<String, dynamic> data) {
    if (onFileDetected != null) {
      onFileDetected!(action, data);
    }
  }
  
  /// ステータス変更通知
  void _notifyStatus(String message) {
    print('[FileWatcher] $message');
    if (onStatusChanged != null) {
      onStatusChanged!(message);
    }
  }
  
  /// リソースをクリーンアップ
  void dispose() {
    stopWatching();
  }
}

/// ファイル監視の設定
class FileWatchConfig {
  final String watchDirectory;
  final bool autoImport;
  final bool notifyOnDetection;
  final List<String> fileExtensions;
  final int processingDelay; // 秒
  
  const FileWatchConfig({
    required this.watchDirectory,
    this.autoImport = true,
    this.notifyOnDetection = true,
    this.fileExtensions = const ['.csv'],
    this.processingDelay = 2,
  });
  
  Map<String, dynamic> toMap() {
    return {
      'watchDirectory': watchDirectory,
      'autoImport': autoImport,
      'notifyOnDetection': notifyOnDetection,
      'fileExtensions': fileExtensions,
      'processingDelay': processingDelay,
    };
  }
  
  factory FileWatchConfig.fromMap(Map<String, dynamic> map) {
    return FileWatchConfig(
      watchDirectory: map['watchDirectory'] ?? '',
      autoImport: map['autoImport'] ?? true,
      notifyOnDetection: map['notifyOnDetection'] ?? true,
      fileExtensions: List<String>.from(map['fileExtensions'] ?? ['.csv']),
      processingDelay: map['processingDelay'] ?? 2,
    );
  }
}