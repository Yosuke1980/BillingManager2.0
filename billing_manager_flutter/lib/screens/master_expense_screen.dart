import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../models/master_expense_model.dart';
import '../services/database_service.dart';

class MasterExpenseScreen extends StatefulWidget {
  const MasterExpenseScreen({super.key});

  @override
  State<MasterExpenseScreen> createState() => _MasterExpenseScreenState();
}

class _MasterExpenseScreenState extends State<MasterExpenseScreen> {
  final _searchController = TextEditingController();
  List<MasterExpenseModel> _masterExpenses = [];
  List<MasterExpenseModel> _filteredExpenses = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadMasterExpenses();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadMasterExpenses() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final expenses = await databaseService.getAllMasterExpenses();
      
      setState(() {
        _masterExpenses = expenses;
        _filteredExpenses = expenses;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showErrorDialog('データ読み込みエラー', 'マスター費用データの読み込みに失敗しました: $e');
    }
  }

  void _filterExpenses(String searchTerm) {
    setState(() {
      if (searchTerm.isEmpty) {
        _filteredExpenses = _masterExpenses;
      } else {
        _filteredExpenses = _masterExpenses
            .where((expense) =>
                expense.name.toLowerCase().contains(searchTerm.toLowerCase()) ||
                expense.category.toLowerCase().contains(searchTerm.toLowerCase()) ||
                (expense.projectName?.toLowerCase().contains(searchTerm.toLowerCase()) ?? false))
            .toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('マスター費用管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadMasterExpenses,
          ),
          IconButton(
            icon: const Icon(Icons.calendar_month),
            onPressed: _showMonthlyGenerationDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          // 検索バー
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                labelText: '費目名、カテゴリ、プロジェクト名で検索',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.search),
              ),
              onChanged: _filterExpenses,
            ),
          ),
          
          // 統計情報
          Card(
            margin: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildStatColumn('総数', _masterExpenses.length.toString()),
                  _buildStatColumn('アクティブ', _masterExpenses.where((e) => e.isActive).length.toString()),
                  _buildStatColumn('月次合計', '¥${NumberFormat('#,###').format(_getMonthlyTotal())}'),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 8),
          
          // マスター費用リスト
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredExpenses.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.receipt_long, size: 48, color: Colors.grey),
                            SizedBox(height: 8),
                            Text(
                              'マスター費用がありません\n右下の+ボタンから追加してください',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: _filteredExpenses.length,
                        itemBuilder: (context, index) {
                          final expense = _filteredExpenses[index];
                          return _buildExpenseCard(expense);
                        },
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showExpenseDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildStatColumn(String label, String value) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.blue,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildExpenseCard(MasterExpenseModel expense) {
    final frequency = ExpenseFrequency.fromString(expense.frequency);
    
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: expense.isActive ? Colors.green : Colors.grey,
          child: Icon(
            expense.isActive ? Icons.check_circle : Icons.pause_circle,
            color: Colors.white,
          ),
        ),
        title: Text(
          expense.name,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: expense.isActive ? null : Colors.grey,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${expense.category} | ${frequency.displayName}'),
            Text('¥${NumberFormat('#,###').format(expense.amount)} | ${expense.dayOfMonth}日'),
            if (expense.projectName?.isNotEmpty == true)
              Text('プロジェクト: ${expense.projectName}'),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) => _handleMenuAction(value, expense),
          itemBuilder: (context) => [
            const PopupMenuItem(
              value: 'edit',
              child: ListTile(
                leading: Icon(Icons.edit),
                title: Text('編集'),
              ),
            ),
            PopupMenuItem(
              value: expense.isActive ? 'deactivate' : 'activate',
              child: ListTile(
                leading: Icon(expense.isActive ? Icons.pause : Icons.play_arrow),
                title: Text(expense.isActive ? '無効化' : '有効化'),
              ),
            ),
            const PopupMenuItem(
              value: 'delete',
              child: ListTile(
                leading: Icon(Icons.delete, color: Colors.red),
                title: Text('削除', style: TextStyle(color: Colors.red)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handleMenuAction(String action, MasterExpenseModel expense) {
    switch (action) {
      case 'edit':
        _showExpenseDialog(expense: expense);
        break;
      case 'activate':
      case 'deactivate':
        _toggleExpenseStatus(expense);
        break;
      case 'delete':
        _showDeleteConfirmation(expense);
        break;
    }
  }

  Future<void> _toggleExpenseStatus(MasterExpenseModel expense) async {
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final updatedExpense = expense.copyWith(
        isActive: !expense.isActive,
        updatedAt: DateTime.now(),
      );
      
      await databaseService.updateMasterExpense(updatedExpense);
      await _loadMasterExpenses();
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${expense.name}を${updatedExpense.isActive ? "有効化" : "無効化"}しました'),
        ),
      );
    } catch (e) {
      _showErrorDialog('更新エラー', '状態の更新に失敗しました: $e');
    }
  }

  void _showDeleteConfirmation(MasterExpenseModel expense) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('削除確認'),
        content: Text('「${expense.name}」を削除しますか？\nこの操作は取り消せません。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('キャンセル'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _deleteExpense(expense);
            },
            child: const Text('削除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  Future<void> _deleteExpense(MasterExpenseModel expense) async {
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      await databaseService.deleteMasterExpense(expense.id!);
      await _loadMasterExpenses();
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${expense.name}を削除しました')),
      );
    } catch (e) {
      _showErrorDialog('削除エラー', '削除に失敗しました: $e');
    }
  }

  double _getMonthlyTotal() {
    return _masterExpenses
        .where((expense) => expense.isActive && expense.frequency == 'monthly')
        .fold(0.0, (sum, expense) => sum + expense.amount);
  }

  void _showMonthlyGenerationDialog() {
    showDialog(
      context: context,
      builder: (context) => _MonthlyGenerationDialog(
        onGenerated: _loadMasterExpenses,
      ),
    );
  }

  void _showExpenseDialog({MasterExpenseModel? expense}) {
    showDialog(
      context: context,
      builder: (context) => _MasterExpenseDialog(
        expense: expense,
        onSaved: _loadMasterExpenses,
      ),
    );
  }

  void _showErrorDialog(String title, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}

class _MasterExpenseDialog extends StatefulWidget {
  final MasterExpenseModel? expense;
  final VoidCallback onSaved;

  const _MasterExpenseDialog({
    this.expense,
    required this.onSaved,
  });

  @override
  State<_MasterExpenseDialog> createState() => _MasterExpenseDialogState();
}

class _MasterExpenseDialogState extends State<_MasterExpenseDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _categoryController = TextEditingController();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _projectNameController = TextEditingController();
  final _departmentController = TextEditingController();
  final _paymentMethodController = TextEditingController();
  
  ExpenseFrequency _selectedFrequency = ExpenseFrequency.monthly;
  int _dayOfMonth = 1;
  bool _isActive = true;

  @override
  void initState() {
    super.initState();
    if (widget.expense != null) {
      final expense = widget.expense!;
      _nameController.text = expense.name;
      _categoryController.text = expense.category;
      _amountController.text = expense.amount.toString();
      _descriptionController.text = expense.description ?? '';
      _projectNameController.text = expense.projectName ?? '';
      _departmentController.text = expense.department ?? '';
      _paymentMethodController.text = expense.paymentMethod;
      _selectedFrequency = ExpenseFrequency.fromString(expense.frequency);
      _dayOfMonth = expense.dayOfMonth;
      _isActive = expense.isActive;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _categoryController.dispose();
    _amountController.dispose();
    _descriptionController.dispose();
    _projectNameController.dispose();
    _departmentController.dispose();
    _paymentMethodController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.expense == null ? 'マスター費用追加' : 'マスター費用編集'),
      content: SizedBox(
        width: 400,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(labelText: '費目名 *'),
                  validator: (value) => value?.isEmpty == true ? '費目名を入力してください' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _categoryController,
                  decoration: const InputDecoration(labelText: 'カテゴリ *'),
                  validator: (value) => value?.isEmpty == true ? 'カテゴリを入力してください' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _amountController,
                  decoration: const InputDecoration(labelText: '金額 *'),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value?.isEmpty == true) return '金額を入力してください';
                    if (double.tryParse(value!) == null) return '有効な金額を入力してください';
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<ExpenseFrequency>(
                  value: _selectedFrequency,
                  decoration: const InputDecoration(labelText: '頻度'),
                  items: ExpenseFrequency.values.map((frequency) {
                    return DropdownMenuItem(
                      value: frequency,
                      child: Text(frequency.displayName),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedFrequency = value!;
                    });
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  decoration: const InputDecoration(labelText: '支払日（月の何日）'),
                  initialValue: _dayOfMonth.toString(),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    final day = int.tryParse(value ?? '');
                    if (day == null || day < 1 || day > 31) {
                      return '1-31の範囲で入力してください';
                    }
                    return null;
                  },
                  onChanged: (value) {
                    _dayOfMonth = int.tryParse(value) ?? 1;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _paymentMethodController,
                  decoration: const InputDecoration(labelText: '支払方法 *'),
                  validator: (value) => value?.isEmpty == true ? '支払方法を入力してください' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _projectNameController,
                  decoration: const InputDecoration(labelText: 'プロジェクト名'),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _departmentController,
                  decoration: const InputDecoration(labelText: '部署'),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _descriptionController,
                  decoration: const InputDecoration(labelText: '説明'),
                  maxLines: 3,
                ),
                const SizedBox(height: 16),
                SwitchListTile(
                  title: const Text('アクティブ'),
                  subtitle: const Text('無効にすると月次生成されません'),
                  value: _isActive,
                  onChanged: (value) {
                    setState(() {
                      _isActive = value;
                    });
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('キャンセル'),
        ),
        ElevatedButton(
          onPressed: _saveMasterExpense,
          child: const Text('保存'),
        ),
      ],
    );
  }

  Future<void> _saveMasterExpense() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final now = DateTime.now();
      
      final masterExpense = MasterExpenseModel(
        id: widget.expense?.id,
        name: _nameController.text,
        category: _categoryController.text,
        amount: double.parse(_amountController.text),
        frequency: _selectedFrequency.value,
        dayOfMonth: _dayOfMonth,
        description: _descriptionController.text.isEmpty ? null : _descriptionController.text,
        isActive: _isActive,
        projectName: _projectNameController.text.isEmpty ? null : _projectNameController.text,
        department: _departmentController.text.isEmpty ? null : _departmentController.text,
        paymentMethod: _paymentMethodController.text,
        tags: null,
        createdAt: widget.expense?.createdAt ?? now,
        updatedAt: now,
      );

      if (widget.expense == null) {
        await databaseService.insertMasterExpense(masterExpense);
      } else {
        await databaseService.updateMasterExpense(masterExpense);
      }

      Navigator.pop(context);
      widget.onSaved();
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${masterExpense.name}を${widget.expense == null ? "追加" : "更新"}しました'),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('保存エラー: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}

class _MonthlyGenerationDialog extends StatefulWidget {
  final VoidCallback onGenerated;

  const _MonthlyGenerationDialog({required this.onGenerated});

  @override
  State<_MonthlyGenerationDialog> createState() => _MonthlyGenerationDialogState();
}

class _MonthlyGenerationDialogState extends State<_MonthlyGenerationDialog> {
  DateTime _selectedMonth = DateTime.now();
  bool _overwriteExisting = false;
  bool _isGenerating = false;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('月次費用生成'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('マスター費用から月次費用を生成します'),
          const SizedBox(height: 16),
          Row(
            children: [
              const Text('対象月: '),
              TextButton(
                onPressed: _selectMonth,
                child: Text('${_selectedMonth.year}年${_selectedMonth.month}月'),
              ),
            ],
          ),
          CheckboxListTile(
            title: const Text('既存データを上書き'),
            subtitle: const Text('同じ月のデータがある場合は上書きします'),
            value: _overwriteExisting,
            onChanged: (value) {
              setState(() {
                _overwriteExisting = value ?? false;
              });
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('キャンセル'),
        ),
        ElevatedButton(
          onPressed: _isGenerating ? null : _generateMonthlyExpenses,
          child: _isGenerating 
              ? const SizedBox(
                  width: 16, 
                  height: 16, 
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('生成'),
        ),
      ],
    );
  }

  Future<void> _selectMonth() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedMonth,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    
    if (picked != null) {
      setState(() {
        _selectedMonth = DateTime(picked.year, picked.month, 1);
      });
    }
  }

  Future<void> _generateMonthlyExpenses() async {
    setState(() {
      _isGenerating = true;
    });

    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final result = await databaseService.generateMonthlyExpenses(
        targetMonth: _selectedMonth,
        overwriteExisting: _overwriteExisting,
      );

      Navigator.pop(context);
      
      if (result.success) {
        widget.onGenerated();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('月次費用を${result.generatedCount}件生成しました'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('生成エラー: ${result.errorMessage}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('生成エラー: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isGenerating = false;
      });
    }
  }
}