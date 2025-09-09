class MasterExpenseModel {
  final int? id;
  final String name;                    // 費目名
  final String category;               // カテゴリ
  final double amount;                 // 基本金額
  final String frequency;              // 頻度 (monthly, quarterly, yearly, custom)
  final int dayOfMonth;               // 支払日（月の何日）
  final String? description;          // 説明
  final bool isActive;                // アクティブ状態
  final String? projectName;          // プロジェクト名
  final String? department;           // 部署
  final String paymentMethod;         // 支払方法
  final String? tags;                 // タグ（カンマ区切り）
  final DateTime createdAt;
  final DateTime updatedAt;

  MasterExpenseModel({
    this.id,
    required this.name,
    required this.category,
    required this.amount,
    required this.frequency,
    required this.dayOfMonth,
    this.description,
    required this.isActive,
    this.projectName,
    this.department,
    required this.paymentMethod,
    this.tags,
    required this.createdAt,
    required this.updatedAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'category': category,
      'amount': amount,
      'frequency': frequency,
      'day_of_month': dayOfMonth,
      'description': description,
      'is_active': isActive ? 1 : 0,
      'project_name': projectName,
      'department': department,
      'payment_method': paymentMethod,
      'tags': tags,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  factory MasterExpenseModel.fromMap(Map<String, dynamic> map) {
    return MasterExpenseModel(
      id: map['id']?.toInt(),
      name: map['name'] ?? '',
      category: map['category'] ?? '',
      amount: (map['amount'] ?? 0.0).toDouble(),
      frequency: map['frequency'] ?? 'monthly',
      dayOfMonth: (map['day_of_month'] ?? 1).toInt(),
      description: map['description'],
      isActive: map['is_active'] == 1,
      projectName: map['project_name'],
      department: map['department'],
      paymentMethod: map['payment_method'] ?? '',
      tags: map['tags'],
      createdAt: DateTime.parse(map['created_at']),
      updatedAt: DateTime.parse(map['updated_at']),
    );
  }

  MasterExpenseModel copyWith({
    int? id,
    String? name,
    String? category,
    double? amount,
    String? frequency,
    int? dayOfMonth,
    String? description,
    bool? isActive,
    String? projectName,
    String? department,
    String? paymentMethod,
    String? tags,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return MasterExpenseModel(
      id: id ?? this.id,
      name: name ?? this.name,
      category: category ?? this.category,
      amount: amount ?? this.amount,
      frequency: frequency ?? this.frequency,
      dayOfMonth: dayOfMonth ?? this.dayOfMonth,
      description: description ?? this.description,
      isActive: isActive ?? this.isActive,
      projectName: projectName ?? this.projectName,
      department: department ?? this.department,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      tags: tags ?? this.tags,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'MasterExpenseModel(id: $id, name: $name, category: $category, amount: $amount, frequency: $frequency, dayOfMonth: $dayOfMonth, isActive: $isActive)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is MasterExpenseModel && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}

/// 費用生成結果
class ExpenseGenerationResult {
  final bool success;
  final int generatedCount;
  final String? errorMessage;
  final List<String> generatedMonths;

  ExpenseGenerationResult({
    required this.success,
    required this.generatedCount,
    this.errorMessage,
    required this.generatedMonths,
  });

  factory ExpenseGenerationResult.success({
    required int generatedCount,
    required List<String> generatedMonths,
  }) {
    return ExpenseGenerationResult(
      success: true,
      generatedCount: generatedCount,
      generatedMonths: generatedMonths,
    );
  }

  factory ExpenseGenerationResult.error(String message) {
    return ExpenseGenerationResult(
      success: false,
      generatedCount: 0,
      errorMessage: message,
      generatedMonths: [],
    );
  }
}

/// 頻度タイプ
enum ExpenseFrequency {
  monthly('monthly', '月次', 1),
  quarterly('quarterly', '四半期', 3),
  semiAnnually('semi_annually', '半期', 6),
  yearly('yearly', '年次', 12),
  custom('custom', 'カスタム', 0);

  const ExpenseFrequency(this.value, this.displayName, this.monthInterval);
  
  final String value;
  final String displayName;
  final int monthInterval;

  static ExpenseFrequency fromString(String value) {
    return ExpenseFrequency.values.firstWhere(
      (freq) => freq.value == value,
      orElse: () => ExpenseFrequency.monthly,
    );
  }
}