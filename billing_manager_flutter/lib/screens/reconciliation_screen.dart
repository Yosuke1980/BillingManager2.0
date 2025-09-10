import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../models/reconciliation_model.dart';
import '../models/payment_model.dart';
import '../models/expense_model.dart';
import '../services/database_service.dart';
import '../services/reconciliation_service.dart';

class ReconciliationScreen extends StatefulWidget {
  const ReconciliationScreen({super.key});

  @override
  State<ReconciliationScreen> createState() => _ReconciliationScreenState();
}

class _ReconciliationScreenState extends State<ReconciliationScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  ReconciliationService? _reconciliationService;
  
  ReconciliationSummary _summary = ReconciliationSummary.empty();
  List<ReconciliationPair> _matches = [];
  List<Payment> _unmatchedPayments = [];
  List<Expense> _unmatchedExpenses = [];
  bool _isLoading = false;

  final List<Tab> _tabs = [
    const Tab(text: '照合結果', icon: Icon(Icons.compare_arrows)),
    const Tab(text: '未照合項目', icon: Icon(Icons.error_outline)),
    const Tab(text: '統計・設定', icon: Icon(Icons.settings)),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
    _initializeService();
    _loadReconciliationData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _initializeService() {
    final databaseService = Provider.of<DatabaseService>(context, listen: false);
    _reconciliationService = ReconciliationService(databaseService);
  }

  Future<void> _loadReconciliationData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final summary = await _reconciliationService!.getReconciliationStatus();
      setState(() {
        _summary = summary;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showErrorDialog('データ読み込みエラー', '照合データの読み込みに失敗しました: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('照合管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadReconciliationData,
          ),
          IconButton(
            icon: const Icon(Icons.auto_fix_high),
            onPressed: _performAutoReconciliation,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: _tabs,
          indicatorColor: Colors.white,
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildReconciliationResultsTab(),
                _buildUnmatchedItemsTab(),
                _buildStatsAndSettingsTab(),
              ],
            ),
    );
  }

  Widget _buildReconciliationResultsTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // サマリーカード
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '照合サマリー',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildSummaryColumn('照合率', _summary.matchRateDisplay, Colors.blue),
                      _buildSummaryColumn('照合済み', '${_summary.matchedPairs}件', Colors.green),
                      _buildSummaryColumn('未照合', '${_summary.unmatchedPayments + _summary.unmatchedExpenses}件', Colors.red),
                      _buildSummaryColumn('差額', '¥${NumberFormat('#,###').format(_summary.totalDifference)}', Colors.orange),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // 照合済み項目リスト
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '照合済み項目',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: _matches.isEmpty
                          ? const Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.compare_arrows, size: 48, color: Colors.grey),
                                  SizedBox(height: 8),
                                  Text(
                                    '照合済み項目がありません\n自動照合を実行してください',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: Colors.grey),
                                  ),
                                ],
                              ),
                            )
                          : ListView.builder(
                              itemCount: _matches.length,
                              itemBuilder: (context, index) {
                                final match = _matches[index];
                                return _buildMatchCard(match);
                              },
                            ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUnmatchedItemsTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // 未照合項目統計
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildSummaryColumn('未照合支払い', '${_unmatchedPayments.length}件', Colors.red),
                  _buildSummaryColumn('未照合費用', '${_unmatchedExpenses.length}件', Colors.orange),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // 未照合項目リスト
          Expanded(
            child: DefaultTabController(
              length: 2,
              child: Column(
                children: [
                  const TabBar(
                    tabs: [
                      Tab(text: '未照合支払い'),
                      Tab(text: '未照合費用'),
                    ],
                  ),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _buildUnmatchedPaymentsList(),
                        _buildUnmatchedExpensesList(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsAndSettingsTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // 統計情報
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '照合統計',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  _buildStatRow('総支払い件数', '${_summary.totalPayments}件'),
                  _buildStatRow('総費用件数', '${_summary.totalExpenses}件'),
                  _buildStatRow('照合完了件数', '${_summary.matchedPairs}件'),
                  _buildStatRow('部分照合件数', '${_summary.partialMatches}件'),
                  _buildStatRow('照合率', _summary.matchRateDisplay),
                  _buildStatRow('金額差合計', '¥${NumberFormat('#,###').format(_summary.totalDifference)}'),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // アクション
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'アクション',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  Wrap(
                    spacing: 8.0,
                    runSpacing: 8.0,
                    children: [
                      ElevatedButton.icon(
                        onPressed: _performAutoReconciliation,
                        icon: const Icon(Icons.auto_fix_high),
                        label: const Text('自動照合実行'),
                      ),
                      ElevatedButton.icon(
                        onPressed: _showManualMatchDialog,
                        icon: const Icon(Icons.link),
                        label: const Text('手動照合'),
                      ),
                      ElevatedButton.icon(
                        onPressed: _showReconciliationConfig,
                        icon: const Icon(Icons.settings),
                        label: const Text('照合設定'),
                      ),
                      ElevatedButton.icon(
                        onPressed: _exportReconciliationReport,
                        icon: const Icon(Icons.file_download),
                        label: const Text('レポート出力'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryColumn(String label, String value, Color color) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
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

  Widget _buildStatRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildMatchCard(ReconciliationPair match) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: match.statusColor,
          child: Icon(
            match.isMatched ? Icons.check : Icons.warning,
            color: Colors.white,
            size: 16,
          ),
        ),
        title: Text(
          '${match.payment?.subject ?? "支払い不明"} ↔ ${match.expense?.description ?? "費用不明"}',
          style: const TextStyle(fontSize: 14),
        ),
        subtitle: Text(
          '差額: ¥${NumberFormat('#,###').format(match.amountDifference)} | ${match.statusDisplayName}',
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                if (match.payment != null) ...[
                  Row(
                    children: [
                      const Icon(Icons.payment, color: Colors.blue),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('支払い: ${match.payment!.subject}'),
                            Text('金額: ¥${NumberFormat('#,###').format(match.payment!.amount)}'),
                            Text('日付: ${match.payment!.paymentDate}'),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                ],
                if (match.expense != null) ...[
                  Row(
                    children: [
                      const Icon(Icons.receipt, color: Colors.green),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('費用: ${match.expense!.description}'),
                            Text('金額: ¥${NumberFormat('#,###').format(match.expense!.amount)}'),
                            Text('日付: ${match.expense!.date}'),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                ],
                if (match.reconciliation?.notes != null) ...[
                  Text('備考: ${match.reconciliation!.notes}'),
                  const SizedBox(height: 8),
                ],
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => _unmatchItems(match),
                      child: const Text('照合解除'),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: () => _editMatch(match),
                      child: const Text('編集'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUnmatchedPaymentsList() {
    return ListView.builder(
      itemCount: _unmatchedPayments.length,
      itemBuilder: (context, index) {
        final payment = _unmatchedPayments[index];
        return ListTile(
          leading: const Icon(Icons.payment, color: Colors.blue),
          title: Text(payment.subject),
          subtitle: Text('¥${NumberFormat('#,###').format(payment.amount)} - ${payment.paymentDate}'),
          trailing: IconButton(
            icon: const Icon(Icons.link),
            onPressed: () => _showManualMatchDialog(payment: payment),
          ),
        );
      },
    );
  }

  Widget _buildUnmatchedExpensesList() {
    return ListView.builder(
      itemCount: _unmatchedExpenses.length,
      itemBuilder: (context, index) {
        final expense = _unmatchedExpenses[index];
        return ListTile(
          leading: const Icon(Icons.receipt, color: Colors.green),
          title: Text(expense.description),
          subtitle: Text('¥${NumberFormat('#,###').format(expense.amount)} - ${expense.date}'),
          trailing: IconButton(
            icon: const Icon(Icons.link),
            onPressed: () => _showManualMatchDialog(expense: expense),
          ),
        );
      },
    );
  }

  Future<void> _performAutoReconciliation() async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('自動照合を実行中...'),
          ],
        ),
      ),
    );

    try {
      final result = await _reconciliationService!.performAutoReconciliation();
      
      Navigator.pop(context); // プログレスダイアログを閉じる
      
      if (result.success) {
        setState(() {
          _matches = result.matches;
          _unmatchedPayments = result.unmatchedPayments;
          _unmatchedExpenses = result.unmatchedExpenses;
          _summary = result.summary;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('自動照合完了: ${result.newMatches}件の新規照合が見つかりました'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        _showErrorDialog('自動照合エラー', result.errorMessage ?? '不明なエラー');
      }
    } catch (e) {
      Navigator.pop(context);
      _showErrorDialog('自動照合エラー', '自動照合中にエラーが発生しました: $e');
    }
  }

  void _showManualMatchDialog({Payment? payment, Expense? expense}) {
    showDialog(
      context: context,
      builder: (context) => _ManualMatchDialog(
        initialPayment: payment,
        initialExpense: expense,
        onMatched: () {
          _loadReconciliationData();
        },
      ),
    );
  }

  void _showReconciliationConfig() {
    showDialog(
      context: context,
      builder: (context) => _ConfigDialog(
        config: _reconciliationService!.config,
        onConfigChanged: (config) {
          _reconciliationService!.updateConfig(config);
        },
      ),
    );
  }

  Future<void> _unmatchItems(ReconciliationPair match) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('照合解除確認'),
        content: const Text('この照合を解除しますか？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('キャンセル'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('解除'),
          ),
        ],
      ),
    );

    if (confirm == true && match.reconciliation?.id != null) {
      final success = await _reconciliationService!.unmatch(match.reconciliation!.id!);
      if (success) {
        _loadReconciliationData();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('照合を解除しました'),
            backgroundColor: Colors.orange,
          ),
        );
      } else {
        _showErrorDialog('解除エラー', '照合の解除に失敗しました');
      }
    }
  }

  void _editMatch(ReconciliationPair match) {
    // TODO: 照合編集機能を実装
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('照合編集機能は実装予定です')),
    );
  }

  void _exportReconciliationReport() {
    // TODO: レポート出力機能を実装
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('レポート出力機能は実装予定です')),
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

class _ManualMatchDialog extends StatefulWidget {
  final Payment? initialPayment;
  final Expense? initialExpense;
  final VoidCallback onMatched;

  const _ManualMatchDialog({
    this.initialPayment,
    this.initialExpense,
    required this.onMatched,
  });

  @override
  State<_ManualMatchDialog> createState() => _ManualMatchDialogState();
}

class _ManualMatchDialogState extends State<_ManualMatchDialog> {
  Payment? _selectedPayment;
  Expense? _selectedExpense;
  final _notesController = TextEditingController();
  
  List<Payment> _payments = [];
  List<Expense> _expenses = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _selectedPayment = widget.initialPayment;
    _selectedExpense = widget.initialExpense;
    _loadData();
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final payments = await databaseService.getAllPayments();
      final expenses = await databaseService.getAllExpenses();
      
      setState(() {
        _payments = payments;
        _expenses = expenses;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('手動照合'),
      content: SizedBox(
        width: 400,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // 支払い選択
                  DropdownButtonFormField<Payment>(
                    value: _selectedPayment,
                    decoration: const InputDecoration(labelText: '支払い'),
                    items: _payments.map((payment) {
                      return DropdownMenuItem(
                        value: payment,
                        child: Text('${payment.subject} - ¥${NumberFormat('#,###').format(payment.amount)}'),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedPayment = value;
                      });
                    },
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 費用選択
                  DropdownButtonFormField<Expense>(
                    value: _selectedExpense,
                    decoration: const InputDecoration(labelText: '費用'),
                    items: _expenses.map((expense) {
                      return DropdownMenuItem(
                        value: expense,
                        child: Text('${expense.description} - ¥${NumberFormat('#,###').format(expense.amount)}'),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedExpense = value;
                      });
                    },
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // 備考入力
                  TextField(
                    controller: _notesController,
                    decoration: const InputDecoration(labelText: '備考'),
                    maxLines: 3,
                  ),
                ],
              ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('キャンセル'),
        ),
        ElevatedButton(
          onPressed: (_selectedPayment != null || _selectedExpense != null) 
              ? _performManualMatch 
              : null,
          child: const Text('照合実行'),
        ),
      ],
    );
  }

  Future<void> _performManualMatch() async {
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final reconciliationService = ReconciliationService(databaseService);
      
      await reconciliationService.performManualReconciliation(
        payment: _selectedPayment,
        expense: _selectedExpense,
        notes: _notesController.text,
        matchedBy: 'user',
      );
      
      Navigator.pop(context);
      widget.onMatched();
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('手動照合を実行しました'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('手動照合エラー: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}

class _ConfigDialog extends StatefulWidget {
  final ReconciliationConfig config;
  final Function(ReconciliationConfig) onConfigChanged;

  const _ConfigDialog({
    required this.config,
    required this.onConfigChanged,
  });

  @override
  State<_ConfigDialog> createState() => _ConfigDialogState();
}

class _ConfigDialogState extends State<_ConfigDialog> {
  late ReconciliationConfig _config;

  @override
  void initState() {
    super.initState();
    _config = widget.config;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('照合設定'),
      content: SizedBox(
        width: 400,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 金額許容差
            Row(
              children: [
                const Expanded(child: Text('金額許容差 (%)')),
                SizedBox(
                  width: 100,
                  child: TextFormField(
                    initialValue: (_config.amountTolerance * 100).toString(),
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      final tolerance = double.tryParse(value);
                      if (tolerance != null) {
                        _config = _config.copyWith(amountTolerance: tolerance / 100);
                      }
                    },
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // 日付許容差
            Row(
              children: [
                const Expanded(child: Text('日付許容差 (日)')),
                SizedBox(
                  width: 100,
                  child: TextFormField(
                    initialValue: _config.dateTolerance.toString(),
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      final tolerance = int.tryParse(value);
                      if (tolerance != null) {
                        _config = _config.copyWith(dateTolerance: tolerance);
                      }
                    },
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // マッチング設定
            SwitchListTile(
              title: const Text('プロジェクト名で照合'),
              value: _config.matchByProject,
              onChanged: (value) {
                setState(() {
                  _config = _config.copyWith(matchByProject: value);
                });
              },
            ),
            
            SwitchListTile(
              title: const Text('説明文で照合'),
              value: _config.matchByDescription,
              onChanged: (value) {
                setState(() {
                  _config = _config.copyWith(matchByDescription: value);
                });
              },
            ),
            
            SwitchListTile(
              title: const Text('支払先で照合'),
              value: _config.matchByPayee,
              onChanged: (value) {
                setState(() {
                  _config = _config.copyWith(matchByPayee: value);
                });
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('キャンセル'),
        ),
        ElevatedButton(
          onPressed: () {
            widget.onConfigChanged(_config);
            Navigator.pop(context);
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('設定を更新しました')),
            );
          },
          child: const Text('保存'),
        ),
      ],
    );
  }
}