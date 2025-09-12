import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../models/payment_model.dart';
import '../services/database_service.dart';
import '../widgets/payment_form_dialog.dart';
import '../widgets/payment_list_item.dart';
import '../widgets/search_filter_bar.dart';

class PaymentsScreen extends StatefulWidget {
  const PaymentsScreen({super.key});

  @override
  State<PaymentsScreen> createState() => _PaymentsScreenState();
}

class _PaymentsScreenState extends State<PaymentsScreen> {
  List<Payment> _payments = [];
  List<Payment> _filteredPayments = [];
  bool _isLoading = true;
  String _searchQuery = '';
  String? _statusFilter;
  String? _payeeFilter;
  DateTime? _startDateFilter;
  DateTime? _endDateFilter;
  
  // 選択機能用の状態管理
  bool _isSelectionMode = false;
  Set<int> _selectedPaymentIds = {};
  bool _selectAll = false;

  final List<String> _statusOptions = [
    '全て',
    '未処理',
    '処理中',
    '完了',
    '保留',
  ];

  @override
  void initState() {
    super.initState();
    _loadPayments();
  }

  Future<void> _loadPayments() async {
    setState(() => _isLoading = true);
    
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final payments = await databaseService.getAllPayments();
      
      setState(() {
        _payments = payments;
        _filteredPayments = payments;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      _showErrorSnackBar('データの読み込みに失敗しました: $e');
    }
  }

  void _filterPayments() {
    setState(() {
      _filteredPayments = _payments.where((payment) {
        // テキスト検索
        final matchesSearch = _searchQuery.isEmpty ||
            payment.subject.toLowerCase().contains(_searchQuery.toLowerCase()) ||
            payment.projectName.toLowerCase().contains(_searchQuery.toLowerCase()) ||
            payment.payee.toLowerCase().contains(_searchQuery.toLowerCase());

        // ステータスフィルタ
        final matchesStatus = _statusFilter == null ||
            _statusFilter == '全て' ||
            payment.status == _statusFilter;

        // 支払い先フィルタ
        final matchesPayee = _payeeFilter == null ||
            _payeeFilter!.isEmpty ||
            payment.payee.toLowerCase().contains(_payeeFilter!.toLowerCase());

        // 日付フィルタ
        bool matchesDateRange = true;
        if (_startDateFilter != null || _endDateFilter != null) {
          try {
            final paymentDate = DateTime.parse(payment.paymentDate);
            if (_startDateFilter != null && paymentDate.isBefore(_startDateFilter!)) {
              matchesDateRange = false;
            }
            if (_endDateFilter != null && paymentDate.isAfter(_endDateFilter!)) {
              matchesDateRange = false;
            }
          } catch (e) {
            matchesDateRange = false;
          }
        }

        return matchesSearch && matchesStatus && matchesPayee && matchesDateRange;
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

  Future<void> _addPayment() async {
    final result = await showDialog<Payment>(
      context: context,
      builder: (context) => const PaymentFormDialog(),
    );

    if (result != null) {
      try {
        final databaseService = Provider.of<DatabaseService>(context, listen: false);
        await databaseService.insertPayment(result);
        _showSuccessSnackBar('支払い情報を追加しました');
        _loadPayments();
      } catch (e) {
        _showErrorSnackBar('支払い情報の追加に失敗しました: $e');
      }
    }
  }

  Future<void> _editPayment(Payment payment) async {
    final result = await showDialog<Payment>(
      context: context,
      builder: (context) => PaymentFormDialog(payment: payment),
    );

    if (result != null) {
      try {
        final databaseService = Provider.of<DatabaseService>(context, listen: false);
        await databaseService.updatePayment(result);
        _showSuccessSnackBar('支払い情報を更新しました');
        _loadPayments();
      } catch (e) {
        _showErrorSnackBar('支払い情報の更新に失敗しました: $e');
      }
    }
  }

  Future<void> _deletePayment(Payment payment) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('削除確認'),
        content: Text('「${payment.subject}」を削除しますか？\nこの操作は取り消せません。'),
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
        await databaseService.deletePayment(payment.id!);
        _showSuccessSnackBar('支払い情報を削除しました');
        _loadPayments();
      } catch (e) {
        _showErrorSnackBar('支払い情報の削除に失敗しました: $e');
      }
    }
  }

  // 選択モードの切り替え
  void _toggleSelectionMode() {
    setState(() {
      _isSelectionMode = !_isSelectionMode;
      if (!_isSelectionMode) {
        _selectedPaymentIds.clear();
        _selectAll = false;
      }
    });
  }

  // 個別選択の切り替え
  void _togglePaymentSelection(int paymentId) {
    setState(() {
      if (_selectedPaymentIds.contains(paymentId)) {
        _selectedPaymentIds.remove(paymentId);
      } else {
        _selectedPaymentIds.add(paymentId);
      }
      _selectAll = _selectedPaymentIds.length == _filteredPayments.length;
    });
  }

  // 全選択の切り替え
  void _toggleSelectAll() {
    setState(() {
      _selectAll = !_selectAll;
      if (_selectAll) {
        _selectedPaymentIds = _filteredPayments.map((p) => p.id!).toSet();
      } else {
        _selectedPaymentIds.clear();
      }
    });
  }

  // 選択した項目の一括削除
  Future<void> _deleteSelectedPayments() async {
    if (_selectedPaymentIds.isEmpty) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('一括削除確認'),
        content: Text('選択した${_selectedPaymentIds.length}件の支払い情報を削除しますか？\nこの操作は取り消せません。'),
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
        for (final paymentId in _selectedPaymentIds) {
          await databaseService.deletePayment(paymentId);
        }
        _showSuccessSnackBar('${_selectedPaymentIds.length}件の支払い情報を削除しました');
        _selectedPaymentIds.clear();
        _selectAll = false;
        _toggleSelectionMode();
        _loadPayments();
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
          SearchFilterBar(
            searchQuery: _searchQuery,
            onSearchChanged: (query) {
              setState(() => _searchQuery = query);
              _filterPayments();
            },
            statusFilter: _statusFilter,
            statusOptions: _statusOptions,
            onStatusFilterChanged: (status) {
              setState(() => _statusFilter = status);
              _filterPayments();
            },
            onDateRangeChanged: (start, end) {
              setState(() {
                _startDateFilter = start;
                _endDateFilter = end;
              });
              _filterPayments();
            },
          ),

          // 選択モード用のコントロールバー
          if (_isSelectionMode)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: Colors.blue.shade100,
              child: Row(
                children: [
                  Checkbox(
                    value: _selectAll,
                    onChanged: (value) => _toggleSelectAll(),
                  ),
                  Text('全選択 (${_selectedPaymentIds.length}/${_filteredPayments.length})'),
                  const Spacer(),
                  ElevatedButton.icon(
                    onPressed: _selectedPaymentIds.isEmpty ? null : _deleteSelectedPayments,
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
            color: Colors.blue.shade50,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatCard('総件数', _payments.length.toString(), Colors.blue),
                _buildStatCard(
                  '総金額', 
                  NumberFormat('#,###').format(
                    _payments.fold<double>(0, (sum, p) => sum + p.amount)
                  ) + '円',
                  Colors.green,
                ),
                _buildStatCard(
                  '未処理', 
                  _payments.where((p) => p.status == '未処理').length.toString(),
                  Colors.orange,
                ),
                _buildStatCard(
                  '完了', 
                  _payments.where((p) => p.status == '完了').length.toString(),
                  Colors.purple,
                ),
              ],
            ),
          ),

          // 支払いリスト
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredPayments.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.inbox, size: 64, color: Colors.grey),
                            SizedBox(height: 16),
                            Text(
                              '支払い情報がありません',
                              style: TextStyle(fontSize: 16, color: Colors.grey),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadPayments,
                        child: ListView.builder(
                          itemCount: _filteredPayments.length,
                          itemBuilder: (context, index) {
                            final payment = _filteredPayments[index];
                            final isSelected = _selectedPaymentIds.contains(payment.id);
                            
                            return _isSelectionMode
                                ? CheckboxListTile(
                                    value: isSelected,
                                    onChanged: (checked) => _togglePaymentSelection(payment.id!),
                                    title: Text(payment.subject),
                                    subtitle: Text('${payment.payee} - ${NumberFormat('#,###').format(payment.amount)}円'),
                                    secondary: CircleAvatar(
                                      backgroundColor: _getStatusColor(payment.status),
                                      child: Text(payment.status.substring(0, 1)),
                                    ),
                                  )
                                : PaymentListItem(
                                    payment: payment,
                                    onEdit: () => _editPayment(payment),
                                    onDelete: () => _deletePayment(payment),
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
                  heroTag: "select",
                  onPressed: _toggleSelectionMode,
                  backgroundColor: Colors.orange,
                  child: const Icon(Icons.checklist),
                ),
                const SizedBox(width: 16),
                FloatingActionButton(
                  heroTag: "add",
                  onPressed: _addPayment,
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

  Color _getStatusColor(String status) {
    switch (status) {
      case '未処理':
        return Colors.orange;
      case '処理中':
        return Colors.blue;
      case '完了':
        return Colors.green;
      case '保留':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}