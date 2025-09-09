import 'dart:async';
import 'database_service.dart';
import '../models/master_expense_model.dart';

class ExpenseSchedulerService {
  final DatabaseService _databaseService;
  Timer? _monthlyTimer;
  bool _isRunning = false;
  
  // コールバック関数
  Function(String message)? onScheduleExecuted;
  Function(String message)? onScheduleError;

  ExpenseSchedulerService(this._databaseService);

  /// スケジューラーを開始
  void startScheduler() {
    if (_isRunning) return;
    
    _isRunning = true;
    _scheduleMonthlyGeneration();
    print('費用生成スケジューラーを開始しました');
  }

  /// スケジューラーを停止
  void stopScheduler() {
    _monthlyTimer?.cancel();
    _monthlyTimer = null;
    _isRunning = false;
    print('費用生成スケジューラーを停止しました');
  }

  /// 月次費用生成をスケジュール
  void _scheduleMonthlyGeneration() {
    final now = DateTime.now();
    final nextMonth = DateTime(now.year, now.month + 1, 1);
    final timeUntilNextMonth = nextMonth.difference(now);

    // 次月の1日になったら実行
    _monthlyTimer = Timer(timeUntilNextMonth, () {
      _executeMonthlyGeneration();
      _scheduleMonthlyGeneration(); // 次のスケジュールを設定
    });
  }

  /// 月次費用生成を実行
  Future<void> _executeMonthlyGeneration() async {
    try {
      final targetMonth = DateTime.now();
      final result = await _databaseService.generateMonthlyExpenses(
        targetMonth: targetMonth,
        overwriteExisting: false,
      );

      if (result.success) {
        final message = '自動月次費用生成完了: ${result.generatedCount}件生成 (${result.generatedMonths.join(", ")})';
        print(message);
        onScheduleExecuted?.call(message);
      } else {
        final message = '自動月次費用生成エラー: ${result.errorMessage}';
        print(message);
        onScheduleError?.call(message);
      }
    } catch (e) {
      final message = '月次費用生成中にエラーが発生: $e';
      print(message);
      onScheduleError?.call(message);
    }
  }

  /// 手動で月次費用生成を実行
  Future<ExpenseGenerationResult> executeManualGeneration({
    DateTime? targetMonth,
    bool overwriteExisting = false,
  }) async {
    return await _databaseService.generateMonthlyExpenses(
      targetMonth: targetMonth,
      overwriteExisting: overwriteExisting,
    );
  }

  /// 複数月の一括生成
  Future<ExpenseGenerationResult> executeBulkGeneration({
    required DateTime startMonth,
    required DateTime endMonth,
    bool overwriteExisting = false,
  }) async {
    return await _databaseService.generateExpensesForRange(
      startMonth: startMonth,
      endMonth: endMonth,
      overwriteExisting: overwriteExisting,
    );
  }

  /// 今月の費用が既に生成されているかチェック
  Future<bool> isCurrentMonthGenerated() async {
    final now = DateTime.now();
    final yearMonth = '${now.year}-${now.month.toString().padLeft(2, '0')}';
    
    final masterExpenses = await _databaseService.getActiveMasterExpenses();
    
    for (final master in masterExpenses) {
      final existingExpenses = await _databaseService.searchExpenses(
        category: master.category,
        projectName: master.projectName ?? '',
        startDate: '$yearMonth-01',
        endDate: '$yearMonth-31',
      );
      
      if (existingExpenses.isEmpty) {
        return false; // まだ生成されていない費用がある
      }
    }
    
    return true; // すべて生成済み
  }

  /// 次回実行予定時刻を取得
  DateTime? getNextExecutionTime() {
    if (!_isRunning || _monthlyTimer == null) return null;
    
    final now = DateTime.now();
    return DateTime(now.year, now.month + 1, 1);
  }

  /// スケジューラー状態を取得
  bool get isRunning => _isRunning;

  /// リソースをクリーンアップ
  void dispose() {
    stopScheduler();
  }
}

/// スケジューラー設定
class SchedulerConfig {
  final bool autoGenerate;         // 自動生成を有効にするか
  final int executionHour;         // 実行時刻（時）
  final int executionMinute;       // 実行時刻（分）
  final bool overwriteExisting;    // 既存データを上書きするか
  final bool notifyOnSuccess;      // 成功時に通知するか
  final bool notifyOnError;        // エラー時に通知するか

  const SchedulerConfig({
    this.autoGenerate = true,
    this.executionHour = 1,
    this.executionMinute = 0,
    this.overwriteExisting = false,
    this.notifyOnSuccess = true,
    this.notifyOnError = true,
  });

  Map<String, dynamic> toMap() {
    return {
      'autoGenerate': autoGenerate,
      'executionHour': executionHour,
      'executionMinute': executionMinute,
      'overwriteExisting': overwriteExisting,
      'notifyOnSuccess': notifyOnSuccess,
      'notifyOnError': notifyOnError,
    };
  }

  factory SchedulerConfig.fromMap(Map<String, dynamic> map) {
    return SchedulerConfig(
      autoGenerate: map['autoGenerate'] ?? true,
      executionHour: map['executionHour'] ?? 1,
      executionMinute: map['executionMinute'] ?? 0,
      overwriteExisting: map['overwriteExisting'] ?? false,
      notifyOnSuccess: map['notifyOnSuccess'] ?? true,
      notifyOnError: map['notifyOnError'] ?? true,
    );
  }

  SchedulerConfig copyWith({
    bool? autoGenerate,
    int? executionHour,
    int? executionMinute,
    bool? overwriteExisting,
    bool? notifyOnSuccess,
    bool? notifyOnError,
  }) {
    return SchedulerConfig(
      autoGenerate: autoGenerate ?? this.autoGenerate,
      executionHour: executionHour ?? this.executionHour,
      executionMinute: executionMinute ?? this.executionMinute,
      overwriteExisting: overwriteExisting ?? this.overwriteExisting,
      notifyOnSuccess: notifyOnSuccess ?? this.notifyOnSuccess,
      notifyOnError: notifyOnError ?? this.notifyOnError,
    );
  }
}