import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import '../models/expense_model.dart';

class ExpenseFormDialog extends StatefulWidget {
  final Expense? expense;

  const ExpenseFormDialog({super.key, this.expense});

  @override
  State<ExpenseFormDialog> createState() => _ExpenseFormDialogState();
}

class _ExpenseFormDialogState extends State<ExpenseFormDialog> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _dateController;
  late TextEditingController _projectNameController;
  late TextEditingController _descriptionController;
  late TextEditingController _amountController;
  late TextEditingController _paymentMethodController;
  late TextEditingController _receiptNumberController;
  late TextEditingController _approverController;
  late TextEditingController _notesController;
  late TextEditingController _clientNameController;
  late TextEditingController _departmentController;

  String _category = '交通費';
  String _approvalStatus = '未承認';

  final List<String> _categoryOptions = [
    '交通費',
    '宿泊費',
    '食事代',
    '資料費',
    '通信費',
    '機材費',
    'その他',
  ];

  final List<String> _approvalStatusOptions = [
    '未承認',
    '承認済み',
    '却下',
  ];

  final List<String> _paymentMethodOptions = [
    '',
    '現金',
    'クレジットカード',
    '銀行振込',
    '小切手',
  ];

  @override
  void initState() {
    super.initState();
    final expense = widget.expense;
    
    _dateController = TextEditingController(
      text: expense?.date ?? DateFormat('yyyy-MM-dd').format(DateTime.now())
    );
    _projectNameController = TextEditingController(text: expense?.projectName ?? '');
    _descriptionController = TextEditingController(text: expense?.description ?? '');
    _amountController = TextEditingController(
      text: expense?.amount.toString() ?? ''
    );
    _paymentMethodController = TextEditingController(text: expense?.paymentMethod ?? '');
    _receiptNumberController = TextEditingController(text: expense?.receiptNumber ?? '');
    _approverController = TextEditingController(text: expense?.approver ?? '');
    _notesController = TextEditingController(text: expense?.notes ?? '');
    _clientNameController = TextEditingController(text: expense?.clientName ?? '');
    _departmentController = TextEditingController(text: expense?.department ?? '');

    _category = expense?.category ?? '交通費';
    _approvalStatus = expense?.approvalStatus ?? '未承認';
  }

  @override
  void dispose() {
    _dateController.dispose();
    _projectNameController.dispose();
    _descriptionController.dispose();
    _amountController.dispose();
    _paymentMethodController.dispose();
    _receiptNumberController.dispose();
    _approverController.dispose();
    _notesController.dispose();
    _clientNameController.dispose();
    _departmentController.dispose();
    super.dispose();
  }

  Future<void> _selectDate() async {
    DateTime? selectedDate = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    
    if (selectedDate != null) {
      _dateController.text = DateFormat('yyyy-MM-dd').format(selectedDate);
    }
  }

  void _saveExpense() {
    if (_formKey.currentState!.validate()) {
      final expense = Expense(
        id: widget.expense?.id,
        date: _dateController.text,
        projectName: _projectNameController.text,
        category: _category,
        description: _descriptionController.text,
        amount: double.tryParse(_amountController.text) ?? 0,
        paymentMethod: _paymentMethodController.text,
        receiptNumber: _receiptNumberController.text,
        approvalStatus: _approvalStatus,
        approver: _approverController.text,
        notes: _notesController.text,
        clientName: _clientNameController.text,
        department: _departmentController.text,
      );
      
      Navigator.of(context).pop(expense);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.expense == null ? '新規費用登録' : '費用情報編集'),
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
                  controller: _dateController,
                  decoration: InputDecoration(
                    labelText: '日付',
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.calendar_today),
                      onPressed: _selectDate,
                    ),
                  ),
                  validator: (value) => value?.isEmpty == true ? '日付を入力してください' : null,
                ),
                
                TextFormField(
                  controller: _projectNameController,
                  decoration: const InputDecoration(labelText: 'プロジェクト名'),
                  validator: (value) => value?.isEmpty == true ? 'プロジェクト名を入力してください' : null,
                ),
                
                DropdownButtonFormField<String>(
                  value: _category,
                  decoration: const InputDecoration(labelText: 'カテゴリ'),
                  items: _categoryOptions.map((category) => DropdownMenuItem(
                    value: category,
                    child: Text(category),
                  )).toList(),
                  onChanged: (value) => setState(() => _category = value!),
                ),
                
                TextFormField(
                  controller: _descriptionController,
                  decoration: const InputDecoration(labelText: '説明'),
                  maxLines: 2,
                  validator: (value) => value?.isEmpty == true ? '説明を入力してください' : null,
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

                const SizedBox(height: 16),
                
                // 支払い情報
                const Text('支払い情報', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                DropdownButtonFormField<String>(
                  value: _paymentMethodController.text.isEmpty ? '' : _paymentMethodController.text,
                  decoration: const InputDecoration(labelText: '支払方法'),
                  items: _paymentMethodOptions.map((method) => DropdownMenuItem(
                    value: method,
                    child: Text(method.isEmpty ? '選択なし' : method),
                  )).toList(),
                  onChanged: (value) {
                    setState(() {
                      _paymentMethodController.text = value ?? '';
                    });
                  },
                ),
                
                TextFormField(
                  controller: _receiptNumberController,
                  decoration: const InputDecoration(labelText: 'レシート番号'),
                ),

                const SizedBox(height: 16),
                
                // 承認情報
                const Text('承認情報', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                DropdownButtonFormField<String>(
                  value: _approvalStatus,
                  decoration: const InputDecoration(labelText: '承認状況'),
                  items: _approvalStatusOptions.map((status) => DropdownMenuItem(
                    value: status,
                    child: Text(status),
                  )).toList(),
                  onChanged: (value) => setState(() => _approvalStatus = value!),
                ),
                
                TextFormField(
                  controller: _approverController,
                  decoration: const InputDecoration(labelText: '承認者'),
                ),

                const SizedBox(height: 16),
                
                // その他情報
                const Text('その他情報', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                
                TextFormField(
                  controller: _clientNameController,
                  decoration: const InputDecoration(labelText: 'クライアント名'),
                ),
                
                TextFormField(
                  controller: _departmentController,
                  decoration: const InputDecoration(labelText: '部署'),
                ),
                
                TextFormField(
                  controller: _notesController,
                  decoration: const InputDecoration(labelText: '備考'),
                  maxLines: 3,
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
          onPressed: _saveExpense,
          child: Text(widget.expense == null ? '登録' : '更新'),
        ),
      ],
    );
  }
}