class Expense {
  final int? id;
  final String date;
  final String projectName;
  final String category;
  final String description;
  final double amount;
  final String paymentMethod;
  final String receiptNumber;
  final String approvalStatus;
  final String approver;
  final String notes;
  final String clientName;
  final String department;

  Expense({
    this.id,
    required this.date,
    required this.projectName,
    required this.category,
    required this.description,
    required this.amount,
    this.paymentMethod = '',
    this.receiptNumber = '',
    this.approvalStatus = '未承認',
    this.approver = '',
    this.notes = '',
    this.clientName = '',
    this.department = '',
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'date': date,
      'project_name': projectName,
      'category': category,
      'description': description,
      'amount': amount,
      'payment_method': paymentMethod,
      'receipt_number': receiptNumber,
      'approval_status': approvalStatus,
      'approver': approver,
      'notes': notes,
      'client_name': clientName,
      'department': department,
    };
  }

  factory Expense.fromMap(Map<String, dynamic> map) {
    return Expense(
      id: map['id'],
      date: map['date'] ?? '',
      projectName: map['project_name'] ?? '',
      category: map['category'] ?? '',
      description: map['description'] ?? '',
      amount: map['amount']?.toDouble() ?? 0.0,
      paymentMethod: map['payment_method'] ?? '',
      receiptNumber: map['receipt_number'] ?? '',
      approvalStatus: map['approval_status'] ?? '未承認',
      approver: map['approver'] ?? '',
      notes: map['notes'] ?? '',
      clientName: map['client_name'] ?? '',
      department: map['department'] ?? '',
    );
  }

  Expense copyWith({
    int? id,
    String? date,
    String? projectName,
    String? category,
    String? description,
    double? amount,
    String? paymentMethod,
    String? receiptNumber,
    String? approvalStatus,
    String? approver,
    String? notes,
    String? clientName,
    String? department,
  }) {
    return Expense(
      id: id ?? this.id,
      date: date ?? this.date,
      projectName: projectName ?? this.projectName,
      category: category ?? this.category,
      description: description ?? this.description,
      amount: amount ?? this.amount,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      receiptNumber: receiptNumber ?? this.receiptNumber,
      approvalStatus: approvalStatus ?? this.approvalStatus,
      approver: approver ?? this.approver,
      notes: notes ?? this.notes,
      clientName: clientName ?? this.clientName,
      department: department ?? this.department,
    );
  }
}