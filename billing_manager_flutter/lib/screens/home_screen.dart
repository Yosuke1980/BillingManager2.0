import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'payments_screen.dart';
import 'expenses_screen.dart';
import 'master_data_screen.dart';
import 'project_filter_screen.dart';
import 'monitoring_screen.dart';
import '../services/database_service.dart';
import '../services/csv_import_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  int _currentIndex = 0;

  final List<Tab> _tabs = [
    const Tab(text: '支払い管理', icon: Icon(Icons.payment)),
    const Tab(text: '費用管理', icon: Icon(Icons.receipt)),
    const Tab(text: 'マスター管理', icon: Icon(Icons.settings)),
    const Tab(text: 'プロジェクトフィルタ', icon: Icon(Icons.filter_alt)),
    const Tab(text: 'モニタリング', icon: Icon(Icons.monitor)),
  ];

  final List<Widget> _screens = [
    const PaymentsScreen(),
    const ExpensesScreen(),
    const MasterDataScreen(),
    const ProjectFilterScreen(),
    const MonitoringScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
    _tabController.addListener(_handleTabChange);
  }

  void _handleTabChange() {
    setState(() {
      _currentIndex = _tabController.index;
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ラジオ局支払い・費用管理システム'),
        centerTitle: true,
        bottom: TabBar(
          controller: _tabController,
          tabs: _tabs,
          isScrollable: true,
          indicatorColor: Colors.white,
          labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _currentIndex,
        onTap: (index) {
          _tabController.animateTo(index);
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.payment),
            label: '支払い',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.receipt),
            label: '費用',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'マスター',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.filter_alt),
            label: 'フィルタ',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.monitor),
            label: 'モニタ',
          ),
        ],
        selectedItemColor: Colors.blue,
        unselectedItemColor: Colors.grey,
        selectedLabelStyle: const TextStyle(fontSize: 10),
        unselectedLabelStyle: const TextStyle(fontSize: 9),
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(
                color: Colors.blue,
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.account_balance,
                    size: 48,
                    color: Colors.white,
                  ),
                  SizedBox(height: 8),
                  Text(
                    '支払い・費用管理システム',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            ListTile(
              leading: const Icon(Icons.dashboard),
              title: const Text('ダッシュボード'),
              onTap: () {
                Navigator.pop(context);
                _tabController.animateTo(0);
              },
            ),
            ListTile(
              leading: const Icon(Icons.file_upload),
              title: const Text('データインポート'),
              onTap: () {
                Navigator.pop(context);
                _showImportDialog();
              },
            ),
            ListTile(
              leading: const Icon(Icons.file_download),
              title: const Text('データエクスポート'),
              onTap: () {
                Navigator.pop(context);
                _showExportDialog();
              },
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('設定'),
              onTap: () {
                Navigator.pop(context);
                _showSettingsDialog();
              },
            ),
            ListTile(
              leading: const Icon(Icons.help),
              title: const Text('ヘルプ'),
              onTap: () {
                Navigator.pop(context);
                _showHelpDialog();
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showImportDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('データインポート'),
        content: const Text('CSVファイルからデータをインポートします。\nインポートするデータの種類を選択してください。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('キャンセル'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _importPaymentsCsv();
            },
            child: const Text('支払いデータ'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _importExpensesCsv();
            },
            child: const Text('費用データ'),
          ),
        ],
      ),
    );
  }

  Future<void> _importPaymentsCsv() async {
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final csvService = CsvImportService(databaseService);
      
      // インポート処理実行
      final result = await csvService.importPaymentsFromCsv();
      
      if (result.cancelled) {
        return; // キャンセルされた場合は何もしない
      }
      
      if (result.success) {
        _showImportResultDialog(
          '支払いデータインポート完了',
          '成功: ${result.successCount}件\nエラー: ${result.errorCount}件',
          result.errors,
        );
      } else {
        _showErrorDialog('インポートエラー', result.errorMessage ?? '不明なエラーが発生しました');
      }
    } catch (e) {
      _showErrorDialog('インポートエラー', 'インポート処理中にエラーが発生しました: $e');
    }
  }

  Future<void> _importExpensesCsv() async {
    try {
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final csvService = CsvImportService(databaseService);
      
      // インポート処理実行
      final result = await csvService.importExpensesFromCsv();
      
      if (result.cancelled) {
        return; // キャンセルされた場合は何もしない
      }
      
      if (result.success) {
        _showImportResultDialog(
          '費用データインポート完了',
          '成功: ${result.successCount}件\nエラー: ${result.errorCount}件',
          result.errors,
        );
      } else {
        _showErrorDialog('インポートエラー', result.errorMessage ?? '不明なエラーが発生しました');
      }
    } catch (e) {
      _showErrorDialog('インポートエラー', 'インポート処理中にエラーが発生しました: $e');
    }
  }

  void _showImportResultDialog(String title, String summary, List<String> errors) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SizedBox(
          width: double.maxFinite,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(summary, style: const TextStyle(fontWeight: FontWeight.bold)),
              if (errors.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text('エラー詳細:', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                SizedBox(
                  height: 200,
                  child: ListView.builder(
                    itemCount: errors.length,
                    itemBuilder: (context, index) {
                      return Text(
                        errors[index],
                        style: const TextStyle(fontSize: 12, color: Colors.red),
                      );
                    },
                  ),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('閉じる'),
          ),
        ],
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
            child: const Text('閉じる'),
          ),
        ],
      ),
    );
  }

  void _showExportDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('データエクスポート'),
        content: const Text('現在のデータをCSVファイルとしてエクスポートします。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('キャンセル'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // TODO: CSV export functionality
            },
            child: const Text('エクスポート'),
          ),
        ],
      ),
    );
  }

  void _showSettingsDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('設定'),
        content: const Text('アプリケーション設定を変更できます。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('閉じる'),
          ),
        ],
      ),
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('ヘルプ'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('■ 基本操作'),
              Text('・各タブで支払いや費用の管理ができます'),
              Text('・データの追加、編集、削除が可能です'),
              SizedBox(height: 12),
              Text('■ データインポート'),
              Text('・CSVファイルからデータを一括登録できます'),
              Text('・メニューからインポート機能をご利用ください'),
              SizedBox(height: 12),
              Text('■ フィルタリング'),
              Text('・各種条件でデータの絞り込みが可能です'),
              Text('・検索機能も併用してください'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('閉じる'),
          ),
        ],
      ),
    );
  }
}