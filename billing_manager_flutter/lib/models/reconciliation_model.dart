import 'package:intl/intl.dart';
import 'payment_model.dart';
import 'expense_model.dart';

/// 照合記録モデル
class ReconciliationRecord {
  final int? id;
  final int? paymentId;            // 支払いID（null可）
  final int? expenseId;            // 費用ID（null可）
  final String reconciliationType; // 照合タイプ (auto, manual, unmatched)
  final String status;             // ステータス (matched, unmatched, partial)
  final double? amountDifference;  // 金額差異
  final String? notes;             // 備考
  final DateTime matchedAt;        // 照合日時
  final String matchedBy;          // 照合者
  final DateTime createdAt;
  final DateTime updatedAt;

  ReconciliationRecord({
    this.id,
    this.paymentId,
    this.expenseId,
    required this.reconciliationType,
    required this.status,
    this.amountDifference,
    this.notes,
    required this.matchedAt,
    required this.matchedBy,
    required this.createdAt,
    required this.updatedAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'payment_id': paymentId,
      'expense_id': expenseId,
      'reconciliation_type': reconciliationType,
      'status': status,
      'amount_difference': amountDifference,
      'notes': notes,
      'matched_at': matchedAt.toIso8601String(),
      'matched_by': matchedBy,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  factory ReconciliationRecord.fromMap(Map<String, dynamic> map) {
    return ReconciliationRecord(
      id: map['id']?.toInt(),
      paymentId: map['payment_id']?.toInt(),
      expenseId: map['expense_id']?.toInt(),
      reconciliationType: map['reconciliation_type'] ?? 'manual',
      status: map['status'] ?? 'unmatched',
      amountDifference: map['amount_difference']?.toDouble(),
      notes: map['notes'],
      matchedAt: DateTime.parse(map['matched_at']),
      matchedBy: map['matched_by'] ?? '',
      createdAt: DateTime.parse(map['created_at']),
      updatedAt: DateTime.parse(map['updated_at']),
    );
  }

  ReconciliationRecord copyWith({
    int? id,
    int? paymentId,
    int? expenseId,
    String? reconciliationType,
    String? status,
    double? amountDifference,
    String? notes,
    DateTime? matchedAt,
    String? matchedBy,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return ReconciliationRecord(
      id: id ?? this.id,
      paymentId: paymentId ?? this.paymentId,
      expenseId: expenseId ?? this.expenseId,
      reconciliationType: reconciliationType ?? this.reconciliationType,
      status: status ?? this.status,
      amountDifference: amountDifference ?? this.amountDifference,
      notes: notes ?? this.notes,
      matchedAt: matchedAt ?? this.matchedAt,
      matchedBy: matchedBy ?? this.matchedBy,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'ReconciliationRecord(id: $id, paymentId: $paymentId, expenseId: $expenseId, status: $status)';
  }
}

/// 照合ペアクラス
class ReconciliationPair {
  final Payment? payment;
  final Expense? expense;
  final ReconciliationRecord? reconciliation;
  final double matchScore;         // マッチングスコア (0.0 - 1.0)
  final List<String> matchReasons; // マッチング理由

  ReconciliationPair({
    this.payment,
    this.expense,
    this.reconciliation,
    required this.matchScore,
    required this.matchReasons,
  });

  bool get isMatched => reconciliation?.status == 'matched';
  bool get isPartiallyMatched => reconciliation?.status == 'partial';
  bool get isUnmatched => reconciliation?.status == 'unmatched' || reconciliation == null;

  double get amountDifference {
    if (payment == null || expense == null) return 0.0;
    return payment!.amount - expense!.amount;
  }

  String get statusDisplayName {
    if (isMatched) return '照合済み';
    if (isPartiallyMatched) return '部分照合';
    return '未照合';
  }

  Color get statusColor {
    if (isMatched) return Colors.green;
    if (isPartiallyMatched) return Colors.orange;
    return Colors.red;
  }
}

/// 照合結果サマリー
class ReconciliationSummary {
  final int totalPayments;
  final int totalExpenses;
  final int matchedPairs;
  final int partialMatches;
  final int unmatchedPayments;
  final int unmatchedExpenses;
  final double totalPaymentAmount;
  final double totalExpenseAmount;
  final double totalDifference;
  final DateTime generatedAt;

  ReconciliationSummary({
    required this.totalPayments,
    required this.totalExpenses,
    required this.matchedPairs,
    required this.partialMatches,
    required this.unmatchedPayments,
    required this.unmatchedExpenses,
    required this.totalPaymentAmount,
    required this.totalExpenseAmount,
    required this.totalDifference,
    required this.generatedAt,
  });

  double get matchRate {
    if (totalPayments == 0 && totalExpenses == 0) return 0.0;
    final totalItems = totalPayments + totalExpenses;
    return (matchedPairs * 2) / totalItems;
  }

  String get matchRateDisplay => '${(matchRate * 100).toStringAsFixed(1)}%';

  factory ReconciliationSummary.empty() {
    return ReconciliationSummary(
      totalPayments: 0,
      totalExpenses: 0,
      matchedPairs: 0,
      partialMatches: 0,
      unmatchedPayments: 0,
      unmatchedExpenses: 0,
      totalPaymentAmount: 0.0,
      totalExpenseAmount: 0.0,
      totalDifference: 0.0,
      generatedAt: DateTime.now(),
    );
  }
}

/// 照合設定
class ReconciliationConfig {
  final double amountTolerance;        // 金額許容差 (%)
  final int dateTolerance;             // 日付許容差 (日)
  final bool matchByProject;           // プロジェクト名で照合
  final bool matchByDescription;       // 説明文で照合
  final bool matchByPayee;            // 支払先で照合
  final double minimumMatchScore;      // 最小マッチングスコア
  final bool autoReconcile;           // 自動照合実行

  const ReconciliationConfig({
    this.amountTolerance = 0.01,      // 1%
    this.dateTolerance = 7,           // 7日
    this.matchByProject = true,
    this.matchByDescription = true,
    this.matchByPayee = true,
    this.minimumMatchScore = 0.8,     // 80%
    this.autoReconcile = true,
  });

  Map<String, dynamic> toMap() {
    return {
      'amountTolerance': amountTolerance,
      'dateTolerance': dateTolerance,
      'matchByProject': matchByProject,
      'matchByDescription': matchByDescription,
      'matchByPayee': matchByPayee,
      'minimumMatchScore': minimumMatchScore,
      'autoReconcile': autoReconcile,
    };
  }

  factory ReconciliationConfig.fromMap(Map<String, dynamic> map) {
    return ReconciliationConfig(
      amountTolerance: map['amountTolerance']?.toDouble() ?? 0.01,
      dateTolerance: map['dateTolerance']?.toInt() ?? 7,
      matchByProject: map['matchByProject'] ?? true,
      matchByDescription: map['matchByDescription'] ?? true,
      matchByPayee: map['matchByPayee'] ?? true,
      minimumMatchScore: map['minimumMatchScore']?.toDouble() ?? 0.8,
      autoReconcile: map['autoReconcile'] ?? true,
    );
  }

  ReconciliationConfig copyWith({
    double? amountTolerance,
    int? dateTolerance,
    bool? matchByProject,
    bool? matchByDescription,
    bool? matchByPayee,
    double? minimumMatchScore,
    bool? autoReconcile,
  }) {
    return ReconciliationConfig(
      amountTolerance: amountTolerance ?? this.amountTolerance,
      dateTolerance: dateTolerance ?? this.dateTolerance,
      matchByProject: matchByProject ?? this.matchByProject,
      matchByDescription: matchByDescription ?? this.matchByDescription,
      matchByPayee: matchByPayee ?? this.matchByPayee,
      minimumMatchScore: minimumMatchScore ?? this.minimumMatchScore,
      autoReconcile: autoReconcile ?? this.autoReconcile,
    );
  }
}

/// 照合処理結果
class ReconciliationResult {
  final bool success;
  final int processedPairs;
  final int newMatches;
  final int updatedMatches;
  final List<ReconciliationPair> matches;
  final List<Payment> unmatchedPayments;
  final List<Expense> unmatchedExpenses;
  final ReconciliationSummary summary;
  final String? errorMessage;

  ReconciliationResult({
    required this.success,
    required this.processedPairs,
    required this.newMatches,
    required this.updatedMatches,
    required this.matches,
    required this.unmatchedPayments,
    required this.unmatchedExpenses,
    required this.summary,
    this.errorMessage,
  });

  factory ReconciliationResult.success({
    required int processedPairs,
    required int newMatches,
    required int updatedMatches,
    required List<ReconciliationPair> matches,
    required List<Payment> unmatchedPayments,
    required List<Expense> unmatchedExpenses,
    required ReconciliationSummary summary,
  }) {
    return ReconciliationResult(
      success: true,
      processedPairs: processedPairs,
      newMatches: newMatches,
      updatedMatches: updatedMatches,
      matches: matches,
      unmatchedPayments: unmatchedPayments,
      unmatchedExpenses: unmatchedExpenses,
      summary: summary,
    );
  }

  factory ReconciliationResult.error(String message) {
    return ReconciliationResult(
      success: false,
      processedPairs: 0,
      newMatches: 0,
      updatedMatches: 0,
      matches: [],
      unmatchedPayments: [],
      unmatchedExpenses: [],
      summary: ReconciliationSummary.empty(),
      errorMessage: message,
    );
  }
}

/// 照合ステータス
enum ReconciliationStatus {
  matched('matched', '照合済み'),
  partial('partial', '部分照合'),
  unmatched('unmatched', '未照合');

  const ReconciliationStatus(this.value, this.displayName);
  
  final String value;
  final String displayName;

  static ReconciliationStatus fromString(String value) {
    return ReconciliationStatus.values.firstWhere(
      (status) => status.value == value,
      orElse: () => ReconciliationStatus.unmatched,
    );
  }
}

/// 照合タイプ
enum ReconciliationType {
  auto('auto', '自動照合'),
  manual('manual', '手動照合'),
  bulk('bulk', '一括照合');

  const ReconciliationType(this.value, this.displayName);
  
  final String value;
  final String displayName;

  static ReconciliationType fromString(String value) {
    return ReconciliationType.values.firstWhere(
      (type) => type.value == value,
      orElse: () => ReconciliationType.manual,
    );
  }
}

// Flutter Materialインポート
import 'package:flutter/material.dart';