import 'dart:math';
import 'database_service.dart';
import '../models/payment_model.dart';
import '../models/expense_model.dart';
import '../models/reconciliation_model.dart';

class ReconciliationService {
  final DatabaseService _databaseService;
  ReconciliationConfig _config = const ReconciliationConfig();

  ReconciliationService(this._databaseService);

  /// 照合設定を更新
  void updateConfig(ReconciliationConfig config) {
    _config = config;
  }

  /// 現在の設定を取得
  ReconciliationConfig get config => _config;

  /// 自動照合を実行
  Future<ReconciliationResult> performAutoReconciliation({
    DateTime? startDate,
    DateTime? endDate,
    String? projectName,
  }) async {
    try {
      // データを取得
      final payments = await _getPaymentsForReconciliation(startDate, endDate, projectName);
      final expenses = await _getExpensesForReconciliation(startDate, endDate, projectName);
      
      if (payments.isEmpty && expenses.isEmpty) {
        return ReconciliationResult.error('照合対象のデータがありません');
      }

      // 既存の照合記録を取得
      final existingReconciliations = await _getExistingReconciliations(
        paymentIds: payments.map((p) => p.id!).toList(),
        expenseIds: expenses.map((e) => e.id!).toList(),
      );

      // 未照合データを抽出
      final unmatchedPayments = _getUnmatchedPayments(payments, existingReconciliations);
      final unmatchedExpenses = _getUnmatchedExpenses(expenses, existingReconciliations);

      // マッチング実行
      final matchResults = await _performMatching(unmatchedPayments, unmatchedExpenses);
      
      // 照合記録を保存
      int newMatches = 0;
      final allMatches = <ReconciliationPair>[];
      
      for (final pair in matchResults) {
        if (pair.matchScore >= _config.minimumMatchScore) {
          final reconciliation = await _createReconciliationRecord(
            payment: pair.payment,
            expense: pair.expense,
            matchScore: pair.matchScore,
            matchReasons: pair.matchReasons,
            reconciliationType: ReconciliationType.auto,
          );
          
          allMatches.add(ReconciliationPair(
            payment: pair.payment,
            expense: pair.expense,
            reconciliation: reconciliation,
            matchScore: pair.matchScore,
            matchReasons: pair.matchReasons,
          ));
          newMatches++;
        }
      }

      // 既存の照合済みデータを追加
      final existingMatches = await _getExistingMatches(existingReconciliations);
      allMatches.addAll(existingMatches);

      // 未照合データを更新
      final finalUnmatchedPayments = _getFinalUnmatchedPayments(payments, allMatches);
      final finalUnmatchedExpenses = _getFinalUnmatchedExpenses(expenses, allMatches);

      // サマリーを生成
      final summary = _generateSummary(
        payments: payments,
        expenses: expenses,
        matches: allMatches,
        unmatchedPayments: finalUnmatchedPayments,
        unmatchedExpenses: finalUnmatchedExpenses,
      );

      return ReconciliationResult.success(
        processedPairs: matchResults.length,
        newMatches: newMatches,
        updatedMatches: 0,
        matches: allMatches,
        unmatchedPayments: finalUnmatchedPayments,
        unmatchedExpenses: finalUnmatchedExpenses,
        summary: summary,
      );

    } catch (e) {
      return ReconciliationResult.error('自動照合処理中にエラーが発生しました: $e');
    }
  }

  /// 手動照合を実行
  Future<ReconciliationRecord> performManualReconciliation({
    Payment? payment,
    Expense? expense,
    String? notes,
    String matchedBy = 'user',
  }) async {
    if (payment == null && expense == null) {
      throw ArgumentError('payment または expense のいずれかは必須です');
    }

    final reconciliation = ReconciliationRecord(
      paymentId: payment?.id,
      expenseId: expense?.id,
      reconciliationType: ReconciliationType.manual.value,
      status: (payment != null && expense != null) 
          ? ReconciliationStatus.matched.value 
          : ReconciliationStatus.partial.value,
      amountDifference: (payment != null && expense != null) 
          ? payment.amount - expense.amount 
          : null,
      notes: notes,
      matchedAt: DateTime.now(),
      matchedBy: matchedBy,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    final id = await _databaseService.insertReconciliation(reconciliation);
    return reconciliation.copyWith(id: id);
  }

  /// 照合を解除
  Future<bool> unmatch(int reconciliationId) async {
    try {
      await _databaseService.deleteReconciliation(reconciliationId);
      return true;
    } catch (e) {
      print('照合解除エラー: $e');
      return false;
    }
  }

  /// 支払いデータを取得
  Future<List<Payment>> _getPaymentsForReconciliation(
    DateTime? startDate,
    DateTime? endDate,
    String? projectName,
  ) async {
    return await _databaseService.searchPayments(
      startDate: startDate?.toIso8601String().substring(0, 10),
      endDate: endDate?.toIso8601String().substring(0, 10),
      projectName: projectName,
    );
  }

  /// 費用データを取得
  Future<List<Expense>> _getExpensesForReconciliation(
    DateTime? startDate,
    DateTime? endDate,
    String? projectName,
  ) async {
    return await _databaseService.searchExpenses(
      startDate: startDate?.toIso8601String().substring(0, 10),
      endDate: endDate?.toIso8601String().substring(0, 10),
      projectName: projectName,
    );
  }

  /// 既存の照合記録を取得
  Future<List<ReconciliationRecord>> _getExistingReconciliations({
    required List<int> paymentIds,
    required List<int> expenseIds,
  }) async {
    return await _databaseService.getReconciliationsByIds(
      paymentIds: paymentIds,
      expenseIds: expenseIds,
    );
  }

  /// マッチング処理を実行
  Future<List<ReconciliationPair>> _performMatching(
    List<Payment> payments,
    List<Expense> expenses,
  ) async {
    final matchResults = <ReconciliationPair>[];

    for (final payment in payments) {
      for (final expense in expenses) {
        final matchScore = _calculateMatchScore(payment, expense);
        final matchReasons = _getMatchReasons(payment, expense);

        if (matchScore > 0.0) {
          matchResults.add(ReconciliationPair(
            payment: payment,
            expense: expense,
            reconciliation: null,
            matchScore: matchScore,
            matchReasons: matchReasons,
          ));
        }
      }
    }

    // スコア順にソート
    matchResults.sort((a, b) => b.matchScore.compareTo(a.matchScore));
    
    // 重複を除去（最高スコアのマッチのみ保持）
    return _removeDuplicateMatches(matchResults);
  }

  /// マッチングスコアを計算
  double _calculateMatchScore(Payment payment, Expense expense) {
    double score = 0.0;
    int factors = 0;

    // 金額マッチング (40%)
    factors++;
    final amountDifference = (payment.amount - expense.amount).abs();
    final amountTolerance = payment.amount * _config.amountTolerance;
    if (amountDifference <= amountTolerance) {
      score += 0.4;
    } else if (amountDifference <= amountTolerance * 2) {
      score += 0.2;
    }

    // 日付マッチング (25%)
    factors++;
    final paymentDate = DateTime.tryParse(payment.paymentDate);
    final expenseDate = DateTime.tryParse(expense.date);
    if (paymentDate != null && expenseDate != null) {
      final dateDifference = paymentDate.difference(expenseDate).inDays.abs();
      if (dateDifference <= _config.dateTolerance) {
        final dateScore = 1.0 - (dateDifference / _config.dateTolerance);
        score += 0.25 * dateScore;
      }
    }

    // プロジェクト名マッチング (15%)
    if (_config.matchByProject && factors < 5) {
      factors++;
      if (_similarityScore(payment.projectName, expense.projectName) > 0.8) {
        score += 0.15;
      }
    }

    // 説明文マッチング (10%)
    if (_config.matchByDescription && factors < 5) {
      factors++;
      final paymentDesc = '${payment.subject} ${payment.payee}'.toLowerCase();
      final expenseDesc = '${expense.description} ${expense.category}'.toLowerCase();
      if (_containsSimilarWords(paymentDesc, expenseDesc)) {
        score += 0.1;
      }
    }

    // 支払先マッチング (10%)
    if (_config.matchByPayee && factors < 5) {
      factors++;
      if (_similarityScore(payment.payee, expense.category) > 0.7) {
        score += 0.1;
      }
    }

    return min(score, 1.0);
  }

  /// マッチング理由を取得
  List<String> _getMatchReasons(Payment payment, Expense expense) {
    final reasons = <String>[];

    // 金額チェック
    final amountDifference = (payment.amount - expense.amount).abs();
    final amountTolerance = payment.amount * _config.amountTolerance;
    if (amountDifference <= amountTolerance) {
      reasons.add('金額が一致');
    } else if (amountDifference <= amountTolerance * 2) {
      reasons.add('金額が近似');
    }

    // 日付チェック
    final paymentDate = DateTime.tryParse(payment.paymentDate);
    final expenseDate = DateTime.tryParse(expense.date);
    if (paymentDate != null && expenseDate != null) {
      final dateDifference = paymentDate.difference(expenseDate).inDays.abs();
      if (dateDifference <= _config.dateTolerance) {
        reasons.add('日付が近似 (${dateDifference}日差)');
      }
    }

    // プロジェクト名チェック
    if (_config.matchByProject && _similarityScore(payment.projectName, expense.projectName) > 0.8) {
      reasons.add('プロジェクト名が一致');
    }

    // その他のマッチング理由を追加
    if (_config.matchByDescription) {
      final paymentDesc = '${payment.subject} ${payment.payee}'.toLowerCase();
      final expenseDesc = '${expense.description} ${expense.category}'.toLowerCase();
      if (_containsSimilarWords(paymentDesc, expenseDesc)) {
        reasons.add('説明文に共通語句');
      }
    }

    return reasons;
  }

  /// 文字列類似度を計算 (簡易版)
  double _similarityScore(String str1, String str2) {
    if (str1.isEmpty || str2.isEmpty) return 0.0;
    
    final words1 = str1.toLowerCase().split(RegExp(r'\s+'));
    final words2 = str2.toLowerCase().split(RegExp(r'\s+'));
    
    int commonWords = 0;
    for (final word1 in words1) {
      if (words2.contains(word1)) {
        commonWords++;
      }
    }
    
    return commonWords / max(words1.length, words2.length);
  }

  /// 共通語句が含まれているかチェック
  bool _containsSimilarWords(String text1, String text2) {
    final words1 = text1.split(RegExp(r'\s+'));
    final words2 = text2.split(RegExp(r'\s+'));
    
    for (final word1 in words1) {
      if (word1.length >= 3) { // 3文字以上の単語のみチェック
        for (final word2 in words2) {
          if (word2.contains(word1) || word1.contains(word2)) {
            return true;
          }
        }
      }
    }
    return false;
  }

  /// 重複マッチを除去
  List<ReconciliationPair> _removeDuplicateMatches(List<ReconciliationPair> matches) {
    final usedPayments = <int>{};
    final usedExpenses = <int>{};
    final uniqueMatches = <ReconciliationPair>[];

    for (final match in matches) {
      final paymentId = match.payment?.id;
      final expenseId = match.expense?.id;

      if (paymentId != null && usedPayments.contains(paymentId)) continue;
      if (expenseId != null && usedExpenses.contains(expenseId)) continue;

      uniqueMatches.add(match);
      if (paymentId != null) usedPayments.add(paymentId);
      if (expenseId != null) usedExpenses.add(expenseId);
    }

    return uniqueMatches;
  }

  /// 照合記録を作成
  Future<ReconciliationRecord> _createReconciliationRecord({
    Payment? payment,
    Expense? expense,
    required double matchScore,
    required List<String> matchReasons,
    required ReconciliationType reconciliationType,
  }) async {
    final reconciliation = ReconciliationRecord(
      paymentId: payment?.id,
      expenseId: expense?.id,
      reconciliationType: reconciliationType.value,
      status: (payment != null && expense != null)
          ? ReconciliationStatus.matched.value
          : ReconciliationStatus.partial.value,
      amountDifference: (payment != null && expense != null)
          ? payment.amount - expense.amount
          : null,
      notes: 'マッチスコア: ${(matchScore * 100).toStringAsFixed(1)}% - ${matchReasons.join(", ")}',
      matchedAt: DateTime.now(),
      matchedBy: 'system',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    final id = await _databaseService.insertReconciliation(reconciliation);
    return reconciliation.copyWith(id: id);
  }

  /// 未照合の支払いデータを取得
  List<Payment> _getUnmatchedPayments(
    List<Payment> payments,
    List<ReconciliationRecord> reconciliations,
  ) {
    final matchedPaymentIds = reconciliations
        .where((r) => r.paymentId != null)
        .map((r) => r.paymentId!)
        .toSet();

    return payments.where((p) => !matchedPaymentIds.contains(p.id)).toList();
  }

  /// 未照合の費用データを取得
  List<Expense> _getUnmatchedExpenses(
    List<Expense> expenses,
    List<ReconciliationRecord> reconciliations,
  ) {
    final matchedExpenseIds = reconciliations
        .where((r) => r.expenseId != null)
        .map((r) => r.expenseId!)
        .toSet();

    return expenses.where((e) => !matchedExpenseIds.contains(e.id)).toList();
  }

  /// 既存のマッチを取得
  Future<List<ReconciliationPair>> _getExistingMatches(
    List<ReconciliationRecord> reconciliations,
  ) async {
    final matches = <ReconciliationPair>[];

    for (final reconciliation in reconciliations) {
      Payment? payment;
      Expense? expense;

      if (reconciliation.paymentId != null) {
        payment = await _databaseService.getPayment(reconciliation.paymentId!);
      }
      if (reconciliation.expenseId != null) {
        expense = await _databaseService.getExpense(reconciliation.expenseId!);
      }

      matches.add(ReconciliationPair(
        payment: payment,
        expense: expense,
        reconciliation: reconciliation,
        matchScore: 1.0, // 既存マッチは100%
        matchReasons: ['既存照合'],
      ));
    }

    return matches;
  }

  /// 最終的な未照合支払いデータを取得
  List<Payment> _getFinalUnmatchedPayments(
    List<Payment> allPayments,
    List<ReconciliationPair> matches,
  ) {
    final matchedPaymentIds = matches
        .where((m) => m.payment?.id != null)
        .map((m) => m.payment!.id!)
        .toSet();

    return allPayments.where((p) => !matchedPaymentIds.contains(p.id)).toList();
  }

  /// 最終的な未照合費用データを取得
  List<Expense> _getFinalUnmatchedExpenses(
    List<Expense> allExpenses,
    List<ReconciliationPair> matches,
  ) {
    final matchedExpenseIds = matches
        .where((m) => m.expense?.id != null)
        .map((m) => m.expense!.id!)
        .toSet();

    return allExpenses.where((e) => !matchedExpenseIds.contains(e.id)).toList();
  }

  /// サマリーを生成
  ReconciliationSummary _generateSummary({
    required List<Payment> payments,
    required List<Expense> expenses,
    required List<ReconciliationPair> matches,
    required List<Payment> unmatchedPayments,
    required List<Expense> unmatchedExpenses,
  }) {
    final totalPaymentAmount = payments.fold(0.0, (sum, p) => sum + p.amount);
    final totalExpenseAmount = expenses.fold(0.0, (sum, e) => sum + e.amount);

    return ReconciliationSummary(
      totalPayments: payments.length,
      totalExpenses: expenses.length,
      matchedPairs: matches.where((m) => m.isMatched).length,
      partialMatches: matches.where((m) => m.isPartiallyMatched).length,
      unmatchedPayments: unmatchedPayments.length,
      unmatchedExpenses: unmatchedExpenses.length,
      totalPaymentAmount: totalPaymentAmount,
      totalExpenseAmount: totalExpenseAmount,
      totalDifference: totalPaymentAmount - totalExpenseAmount,
      generatedAt: DateTime.now(),
    );
  }

  /// 照合状況を取得
  Future<ReconciliationSummary> getReconciliationStatus({
    DateTime? startDate,
    DateTime? endDate,
    String? projectName,
  }) async {
    try {
      final payments = await _getPaymentsForReconciliation(startDate, endDate, projectName);
      final expenses = await _getExpensesForReconciliation(startDate, endDate, projectName);
      
      final existingReconciliations = await _getExistingReconciliations(
        paymentIds: payments.map((p) => p.id!).toList(),
        expenseIds: expenses.map((e) => e.id!).toList(),
      );

      final matches = await _getExistingMatches(existingReconciliations);
      final unmatchedPayments = _getFinalUnmatchedPayments(payments, matches);
      final unmatchedExpenses = _getFinalUnmatchedExpenses(expenses, matches);

      return _generateSummary(
        payments: payments,
        expenses: expenses,
        matches: matches,
        unmatchedPayments: unmatchedPayments,
        unmatchedExpenses: unmatchedExpenses,
      );
    } catch (e) {
      print('照合状況取得エラー: $e');
      return ReconciliationSummary.empty();
    }
  }
}