class Payment {
  final int? id;
  final String subject;
  final String projectName;
  final String payee;
  final String payeeCode;
  final double amount;
  final String paymentDate;
  final String status;
  final String type;
  final String clientName;
  final String department;
  final String projectStatus;
  final String projectStartDate;
  final String projectEndDate;
  final double budget;
  final String approver;
  final String urgencyLevel;

  Payment({
    this.id,
    required this.subject,
    required this.projectName,
    required this.payee,
    required this.payeeCode,
    required this.amount,
    required this.paymentDate,
    this.status = '未処理',
    this.type = '',
    this.clientName = '',
    this.department = '',
    this.projectStatus = '進行中',
    this.projectStartDate = '',
    this.projectEndDate = '',
    this.budget = 0,
    this.approver = '',
    this.urgencyLevel = '通常',
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'subject': subject,
      'project_name': projectName,
      'payee': payee,
      'payee_code': payeeCode,
      'amount': amount,
      'payment_date': paymentDate,
      'status': status,
      'type': type,
      'client_name': clientName,
      'department': department,
      'project_status': projectStatus,
      'project_start_date': projectStartDate,
      'project_end_date': projectEndDate,
      'budget': budget,
      'approver': approver,
      'urgency_level': urgencyLevel,
    };
  }

  factory Payment.fromMap(Map<String, dynamic> map) {
    return Payment(
      id: map['id'],
      subject: map['subject'] ?? '',
      projectName: map['project_name'] ?? '',
      payee: map['payee'] ?? '',
      payeeCode: map['payee_code'] ?? '',
      amount: map['amount']?.toDouble() ?? 0.0,
      paymentDate: map['payment_date'] ?? '',
      status: map['status'] ?? '未処理',
      type: map['type'] ?? '',
      clientName: map['client_name'] ?? '',
      department: map['department'] ?? '',
      projectStatus: map['project_status'] ?? '進行中',
      projectStartDate: map['project_start_date'] ?? '',
      projectEndDate: map['project_end_date'] ?? '',
      budget: map['budget']?.toDouble() ?? 0.0,
      approver: map['approver'] ?? '',
      urgencyLevel: map['urgency_level'] ?? '通常',
    );
  }

  Payment copyWith({
    int? id,
    String? subject,
    String? projectName,
    String? payee,
    String? payeeCode,
    double? amount,
    String? paymentDate,
    String? status,
    String? type,
    String? clientName,
    String? department,
    String? projectStatus,
    String? projectStartDate,
    String? projectEndDate,
    double? budget,
    String? approver,
    String? urgencyLevel,
  }) {
    return Payment(
      id: id ?? this.id,
      subject: subject ?? this.subject,
      projectName: projectName ?? this.projectName,
      payee: payee ?? this.payee,
      payeeCode: payeeCode ?? this.payeeCode,
      amount: amount ?? this.amount,
      paymentDate: paymentDate ?? this.paymentDate,
      status: status ?? this.status,
      type: type ?? this.type,
      clientName: clientName ?? this.clientName,
      department: department ?? this.department,
      projectStatus: projectStatus ?? this.projectStatus,
      projectStartDate: projectStartDate ?? this.projectStartDate,
      projectEndDate: projectEndDate ?? this.projectEndDate,
      budget: budget ?? this.budget,
      approver: approver ?? this.approver,
      urgencyLevel: urgencyLevel ?? this.urgencyLevel,
    );
  }
}