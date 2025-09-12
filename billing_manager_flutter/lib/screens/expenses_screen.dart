import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../models/expense_model.dart';
import '../services/database_service.dart';
import '../widgets/expense_form_dialog.dart';
import '../widgets/expense_list_item.dart';
import '../widgets/expense_search_filter_bar.dart';

class ExpensesScreen extends StatefulWidget {
  const ExpensesScreen({super.key});

  @override
  State<ExpensesScreen> createState() => _ExpensesScreenState();
}

class _ExpensesScreenState extends State<ExpensesScreen> {
  List<Expense> _expenses = [];
  List<Expense> _filteredExpenses = [];
  bool _isLoading = true;
  String _searchQuery = '';
  String? _categoryFilter;
  String? _approvalStatusFilter;
  DateTime? _startDateFilter;
  DateTime? _endDateFilter;
  
  // 選択機能用の状態管理
  bool _isSelectionMode = false;
  Set<int> _selectedExpenseIds = {};
  bool _selectAll = false;

  final List<String> _approvalStatusOptions = [
    '全て',
    '未承認',
    '承認済み',
    '却下',
  ];

  final List<String> _categoryOptions = [
    '全て',
    '交通費',
    '宿泊費',
    '食事代',
    '資料費',
    '通信費',
    '機材費',
    'その他',
  ];

  @override
  void initState() {
    super.initState();
    _loadExpenses();
  }

  Future<void> _loadExpenses() async {
    setState(() => _isLoading = true);
    
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final expenses = await databaseService.getAllExpenses();
      
      setState(() {
        _expenses = expenses;
        _filteredExpenses = expenses;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      _showErrorSnackBar('データの読み込みに失敗しました: $e');
    }
  }

  void _filterExpenses() {
    setState(() {
      _filteredExpenses = _expenses.where((expense) {
        // テキスト検索
        final matchesSearch = _searchQuery.isEmpty ||
            expense.description.toLowerCase().contains(_searchQuery.toLowerCase()) ||
            expense.projectName.toLowerCase().contains(_searchQuery.toLowerCase()) ||
            expense.category.toLowerCase().contains(_searchQuery.toLowerCase());

        // カテゴリフィルタ
        final matchesCategory = _categoryFilter == null ||
            _categoryFilter == '全て' ||
            expense.category == _categoryFilter;

        // 承認状態フィルタ
        final matchesApproval = _approvalStatusFilter == null ||
            _approvalStatusFilter == '全て' ||
            expense.approvalStatus == _approvalStatusFilter;

        // 日付フィルタ
        bool matchesDateRange = true;
        if (_startDateFilter != null || _endDateFilter != null) {
          try {
            final expenseDate = DateTime.parse(expense.date);
            if (_startDateFilter != null && expenseDate.isBefore(_startDateFilter!)) {
              matchesDateRange = false;
            }
            if (_endDateFilter != null && expenseDate.isAfter(_endDateFilter!)) {
              matchesDateRange = false;
            }
          } catch (e) {
            matchesDateRange = false;
          }
        }

        return matchesSearch && matchesCategory && matchesApproval && matchesDateRange;
      }).toList();
    });
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  Future<void> _addExpense() async {
    final result = await showDialog<Expense>(
      context: context,
      builder: (context) => const ExpenseFormDialog(),
    );

    if (result != null) {
      try {
        final databaseService = Provider.of<DatabaseService>(context, listen: false);
        await databaseService.insertExpense(result);
        _showSuccessSnackBar('費用情報を追加しました');
        _loadExpenses();
      } catch (e) {
        _showErrorSnackBar('費用情報の追加に失敗しました: $e');
      }
    }
  }

  Future<void> _editExpense(Expense expense) async {
    final result = await showDialog<Expense>(
      context: context,
      builder: (context) => ExpenseFormDialog(expense: expense),
    );

    if (result != null) {
      try {
        final databaseService = Provider.of<DatabaseService>(context, listen: false);
        await databaseService.updateExpense(result);
        _showSuccessSnackBar('費用情報を更新しました');
        _loadExpenses();
      } catch (e) {
        _showErrorSnackBar('費用情報の更新に失敗しました: $e');
      }
    }
  }

  Future<void> _deleteExpense(Expense expense) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('削除確認'),
        content: Text('「${expense.description}」を削除しますか？\nこの操作は取り消せません。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('キャンセル'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('削除'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        final databaseService = Provider.of<DatabaseService>(context, listen: false);
        await databaseService.deleteExpense(expense.id!);
        _showSuccessSnackBar('費用情報を削除しました');
        _loadExpenses();
      } catch (e) {
        _showErrorSnackBar('費用情報の削除に失敗しました: $e');
      }
    }
  }

  // 選択モードの切り替え
  void _toggleSelectionMode() {
    setState(() {
      _isSelectionMode = !_isSelectionMode;
      if (!_isSelectionMode) {
        _selectedExpenseIds.clear();
        _selectAll = false;
      }
    });
  }

  // 個別選択の切り替え
  void _toggleExpenseSelection(int expenseId) {
    setState(() {
      if (_selectedExpenseIds.contains(expenseId)) {
        _selectedExpenseIds.remove(expenseId);
      } else {
        _selectedExpenseIds.add(expenseId);
      }
      _selectAll = _selectedExpenseIds.length == _filteredExpenses.length;
    });
  }

  // 全選択の切り替え
  void _toggleSelectAll() {
    setState(() {
      _selectAll = !_selectAll;
      if (_selectAll) {
        _selectedExpenseIds = _filteredExpenses.map((e) => e.id!).toSet();
      } else {
        _selectedExpenseIds.clear();
      }
    });
  }

  // 選択した項目の一括削除
  Future<void> _deleteSelectedExpenses() async {
    if (_selectedExpenseIds.isEmpty) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('一括削除確認'),
        content: Text('選択した${_selectedExpenseIds.length}件の費用情報を削除しますか？\nこの操作は取り消せません。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('キャンセル'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('削除'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        final databaseService = Provider.of<DatabaseService>(context, listen: false);
        for (final expenseId in _selectedExpenseIds) {
          await databaseService.deleteExpense(expenseId);
        }
        _showSuccessSnackBar('${_selectedExpenseIds.length}件の費用情報を削除しました');
        _selectedExpenseIds.clear();
        _selectAll = false;
        _toggleSelectionMode();
        _loadExpenses();
      } catch (e) {
        _showErrorSnackBar('一括削除に失敗しました: $e');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // 検索・フィルターバー
          ExpenseSearchFilterBar(
            searchQuery: _searchQuery,
            onSearchChanged: (query) {
              setState(() => _searchQuery = query);
              _filterExpenses();
            },
            categoryFilter: _categoryFilter,
            categoryOptions: _categoryOptions,
            onCategoryFilterChanged: (category) {
              setState(() => _categoryFilter = category);
              _filterExpenses();
            },
            approvalStatusFilter: _approvalStatusFilter,
            approvalStatusOptions: _approvalStatusOptions,
            onApprovalStatusFilterChanged: (status) {
              setState(() => _approvalStatusFilter = status);
              _filterExpenses();
            },
            onDateRangeChanged: (start, end) {
              setState(() {
                _startDateFilter = start;
                _endDateFilter = end;
              });
              _filterExpenses();
            },
          ),

          // 選択モード用のコントロールバー
          if (_isSelectionMode)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: Colors.green.shade100,
              child: Row(
                children: [
                  Checkbox(
                    value: _selectAll,
                    onChanged: (value) => _toggleSelectAll(),
                  ),
                  Text('全選択 (${_selectedExpenseIds.length}/${_filteredExpenses.length})'),
                  const Spacer(),
                  ElevatedButton.icon(
                    onPressed: _selectedExpenseIds.isEmpty ? null : _deleteSelectedExpenses,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                    icon: const Icon(Icons.delete, color: Colors.white),
                    label: const Text('削除', style: TextStyle(color: Colors.white)),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: _toggleSelectionMode,
                    child: const Text('キャンセル'),
                  ),
                ],
              ),
            ),
          
          // 統計情報
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.green.shade50,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatCard('総件数', _expenses.length.toString(), Colors.green),
                _buildStatCard(
                  '総金額', 
                  NumberFormat('#,###').format(
                    _expenses.fold<double>(0, (sum, e) => sum + e.amount)
                  ) + '円',
                  Colors.blue,
                ),
                _buildStatCard(
                  '未承認', 
                  _expenses.where((e) => e.approvalStatus == '未承認').length.toString(),
                  Colors.orange,
                ),
                _buildStatCard(
                  '承認済み', 
                  _expenses.where((e) => e.approvalStatus == '承認済み').length.toString(),
                  Colors.purple,
                ),
              ],
            ),
          ),

          // 費用リスト
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredExpenses.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.receipt_long, size: 64, color: Colors.grey),
                            SizedBox(height: 16),
                            Text(
                              '費用情報がありません',
                              style: TextStyle(fontSize: 16, color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadExpenses,
                        child: ListView.builder(
                          itemCount: _filteredExpenses.length,
                          itemBuilder: (context, index) {
                            final expense = _filteredExpenses[index];
                            final isSelected = _selectedExpenseIds.contains(expense.id);
                            
                            return _isSelectionMode
                                ? CheckboxListTile(
                                    value: isSelected,
                                    onChanged: (checked) => _toggleExpenseSelection(expense.id!),
                                    title: Text(expense.description),
                                    subtitle: Text('${expense.category} - ${NumberFormat('#,###').format(expense.amount)}円'),
                                    secondary: CircleAvatar(
                                      backgroundColor: _getApprovalStatusColor(expense.approvalStatus),
                                      child: Text(expense.approvalStatus.substring(0, 1)),
                                    ),
                                  )
                                : ExpenseListItem(
                                    expense: expense,
                                    onEdit: () => _editExpense(expense),
                                    onDelete: () => _deleteExpense(expense),
                                  );
                          },
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: _isSelectionMode
          ? null
          : Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                FloatingActionButton(
                  heroTag: "select_expense",
                  onPressed: _toggleSelectionMode,
                  backgroundColor: Colors.orange,
                  child: const Icon(Icons.checklist),
                ),
                const SizedBox(width: 16),
                FloatingActionButton(
                  heroTag: "add_expense",
                  onPressed: _addExpense,
                  child: const Icon(Icons.add),
                ),
              ],
            ),
    );
  }

  Widget _buildStatCard(String title, String value, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Text(
              title,
              style: TextStyle(
                fontSize: 12,
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 14,
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getApprovalStatusColor(String status) {
    switch (status) {
      case '未承認':
        return Colors.orange;
      case '承認済み':
        return Colors.green;
      case '却下':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}