import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../models/payment_model.dart';

class PaymentFormDialog extends StatefulWidget {
  final Payment? payment;

  const PaymentFormDialog({super.key, this.payment});

  @override
  State<PaymentFormDialog> createState() => _PaymentFormDialogState();
}

class _PaymentFormDialogState extends State<PaymentFormDialog> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _subjectController;
  late TextEditingController _projectNameController;
  late TextEditingController _payeeController;
  late TextEditingController _payeeCodeController;
  late TextEditingController _amountController;
  late TextEditingController _paymentDateController;
  late TextEditingController _clientNameController;
  late TextEditingController _departmentController;
  late TextEditingController _projectStartDateController;
  late TextEditingController _projectEndDateController;
  late TextEditingController _budgetController;
  late TextEditingController _approverController;

  String _status = '未処理';
  String _type = '';
  String _projectStatus = '進行中';
  String _urgencyLevel = '通常';

  final List<String> _statusOptions = ['未処理', '処理中', '完了', '保留'];
  final List<String> _typeOptions = ['', '定期支払い', '一時支払い', '緊急支払い'];
  final List<String> _projectStatusOptions = ['進行中', '完了', '保留', '中止'];
  final List<String> _urgencyOptions = ['低', '通常', '高', '緊急'];

  @override
  void initState() {
    super.initState();
    final payment = widget.payment;
    
    _subjectController = TextEditingController(text: payment?.subject ?? '');
    _projectNameController = TextEditingController(text: payment?.projectName ?? '');
    _payeeController = TextEditingController(text: payment?.payee ?? '');
    _payeeCodeController = TextEditingController(text: payment?.payeeCode ?? '');
    _amountController = TextEditingController(
      text: payment?.amount.toString() ?? ''
    );
    _paymentDateController = TextEditingController(
      text: payment?.paymentDate ?? DateFormat('yyyy-MM-dd').format(DateTime.now())
    );
    _clientNameController = TextEditingController(text: payment?.clientName ?? '');
    _departmentController = TextEditingController(text: payment?.department ?? '');
    _projectStartDateController = TextEditingController(text: payment?.projectStartDate ?? '');
    _projectEndDateController = TextEditingController(text: payment?.projectEndDate ?? '');
    _budgetController = TextEditingController(
      text: payment?.budget.toString() ?? '0'
    );
    _approverController = TextEditingController(text: payment?.approver ?? '');

    _status = payment?.status ?? '未処理';
    _type = payment?.type ?? '';
    _projectStatus = payment?.projectStatus ?? '進行中';
    _urgencyLevel = payment?.urgencyLevel ?? '通常';
  }

  @override
  void dispose() {
    _subjectController.dispose();
    _projectNameController.dispose();
    _payeeController.dispose();
    _payeeCodeController.dispose();
    _amountController.dispose();
    _paymentDateController.dispose();
    _clientNameController.dispose();
    _departmentController.dispose();
    _projectStartDateController.dispose();
    _projectEndDateController.dispose();
    _budgetController.dispose();
    _approverController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(TextEditingController controller) async {
    DateTime? selectedDate = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    
    if (selectedDate != null) {
      controller.text = DateFormat('yyyy-MM-dd').format(selectedDate);
    }
  }

  void _savePayment() {
    if (_formKey.currentState!.validate()) {
      final payment = Payment(
        id: widget.payment?.id,
        subject: _subjectController.text,
        projectName: _projectNameController.text,
        payee: _payeeController.text,
        payeeCode: _payeeCodeController.text,
        amount: double.tryParse(_amountController.text) ?? 0,
        paymentDate: _paymentDateController.text,
        status: _status,
        type: _type,
        clientName: _clientNameController.text,
        department: _departmentController.text,
        projectStatus: _projectStatus,
        projectStartDate: _projectStartDateController.text,
        projectEndDate: _projectEndDateController.text,
        budget: double.tryParse(_budgetController.text) ?? 0,
        approver: _approverController.text,
        urgencyLevel: _urgencyLevel,
      );
      
      Navigator.of(context).pop(payment);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.payment == null ? '新規支払い登録' : '支払い情報編集'),
      content: SizedBox(
        width: double.maxFinite,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 基本情報
                const Text('基本情報', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                TextFormField(
                  controller: _subjectController,
                  decoration: const InputDecoration(labelText: '件名'),
                  validator: (value) => value?.isEmpty == true ? '件名を入力してください' : null,
                ),
                
                TextFormField(
                  controller: _projectNameController,
                  decoration: const InputDecoration(labelText: 'プロジェクト名'),
                  validator: (value) => value?.isEmpty == true ? 'プロジェクト名を入力してください' : null,
                ),
                
                TextFormField(
                  controller: _payeeController,
                  decoration: const InputDecoration(labelText: '支払い先'),
                  validator: (value) => value?.isEmpty == true ? '支払い先を入力してください' : null,
                ),
                
                TextFormField(
                  controller: _payeeCodeController,
                  decoration: const InputDecoration(labelText: '支払い先コード'),
                ),
                
                TextFormField(
                  controller: _amountController,
                  decoration: const InputDecoration(labelText: '金額', suffixText: '円'),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
                  validator: (value) {
                    if (value?.isEmpty == true) return '金額を入力してください';
                    if (double.tryParse(value!) == null) return '有効な金額を入力してください';
                    return null;
                  },
                ),
                
                TextFormField(
                  controller: _paymentDateController,
                  decoration: InputDecoration(
                    labelText: '支払日',
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.calendar_today),
                      onPressed: () => _selectDate(_paymentDateController),
                    ),
                  ),
                  validator: (value) => value?.isEmpty == true ? '支払日を入力してください' : null,
                ),

                const SizedBox(height: 16),
                
                // ステータス・分類
                const Text('ステータス・分類', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                DropdownButtonFormField<String>(
                  value: _status,
                  decoration: const InputDecoration(labelText: 'ステータス'),
                  items: _statusOptions.map((status) => DropdownMenuItem(
                    value: status,
                    child: Text(status),
                  )).toList(),
                  onChanged: (value) => setState(() => _status = value!),
                ),
                
                DropdownButtonFormField<String>(
                  value: _type,
                  decoration: const InputDecoration(labelText: 'タイプ'),
                  items: _typeOptions.map((type) => DropdownMenuItem(
                    value: type,
                    child: Text(type.isEmpty ? '選択なし' : type),
                  )).toList(),
                  onChanged: (value) => setState(() => _type = value!),
                ),
                
                DropdownButtonFormField<String>(
                  value: _urgencyLevel,
                  decoration: const InputDecoration(labelText: '緊急度'),
                  items: _urgencyOptions.map((level) => DropdownMenuItem(
                    value: level,
                    child: Text(level),
                  )).toList(),
                  onChanged: (value) => setState(() => _urgencyLevel = value!),
                ),

                const SizedBox(height: 16),
                
                // プロジェクト情報
                const Text('プロジェクト情報', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                TextFormField(
                  controller: _clientNameController,
                  decoration: const InputDecoration(labelText: 'クライアント名'),
                ),
                
                TextFormField(
                  controller: _departmentController,
                  decoration: const InputDecoration(labelText: '部署'),
                ),
                
                DropdownButtonFormField<String>(
                  value: _projectStatus,
                  decoration: const InputDecoration(labelText: 'プロジェクトステータス'),
                  items: _projectStatusOptions.map((status) => DropdownMenuItem(
                    value: status,
                    child: Text(status),
                  )).toList(),
                  onChanged: (value) => setState(() => _projectStatus = value!),
                ),
                
                TextFormField(
                  controller: _projectStartDateController,
                  decoration: InputDecoration(
                    labelText: 'プロジェクト開始日',
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.calendar_today),
                      onPressed: () => _selectDate(_projectStartDateController),
                    ),
                  ),
                ),
                
                TextFormField(
                  controller: _projectEndDateController,
                  decoration: InputDecoration(
                    labelText: 'プロジェクト終了日',
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.calendar_today),
                      onPressed: () => _selectDate(_projectEndDateController),
                    ),
                  ),
                ),
                
                TextFormField(
                  controller: _budgetController,
                  decoration: const InputDecoration(labelText: '予算', suffixText: '円'),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))],
                ),
                
                TextFormField(
                  controller: _approverController,
                  decoration: const InputDecoration(labelText: '承認者'),
                ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('キャンセル'),
        ),
        ElevatedButton(
          onPressed: _savePayment,
          child: Text(widget.payment == null ? '登録' : '更新'),
        ),
      ],
    );
  }
}