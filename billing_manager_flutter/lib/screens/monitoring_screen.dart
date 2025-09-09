import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import 'package:intl/intl.dart';
import '../services/database_service.dart';
import '../services/file_watcher_service.dart';
import '../services/data_export_service.dart';
import '../services/expense_scheduler_service.dart';

class MonitoringScreen extends StatefulWidget {
  const MonitoringScreen({super.key});

  @override
  State<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends State<MonitoringScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  FileWatcherService? _fileWatcher;
  DataExportService? _exportService;
  ExpenseSchedulerService? _schedulerService;
  
  bool _isWatchingFiles = false;
  String _watchDirectory = '';
  String _lastStatus = 'ファイル監視は停止中';
  final List<Map<String, dynamic>> _detectedFiles = [];
  
  final List<Tab> _tabs = [
    const Tab(text: 'ファイル監視', icon: Icon(Icons.folder_open)),
    const Tab(text: 'データエクスポート', icon: Icon(Icons.file_download)),
    const Tab(text: '費用スケジュール', icon: Icon(Icons.schedule)),
    const Tab(text: 'システム状態', icon: Icon(Icons.info)),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
    _initializeServices();
  }

  void _initializeServices() {
    final databaseService = Provider.of<DatabaseService>(context, listen: false);
    _fileWatcher = FileWatcherService(databaseService);
    _exportService = DataExportService(databaseService);
    _schedulerService = ExpenseSchedulerService(databaseService);
    
    // ファイル監視のコールバック設定
    _fileWatcher!.onFileDetected = (action, data) {
      setState(() {
        _detectedFiles.insert(0, {
          ...data,
          'time': DateTime.now(),
        });
        // 最大50件まで保持
        if (_detectedFiles.length > 50) {
          _detectedFiles.removeLast();
        }
      });
    };
    
    _fileWatcher!.onStatusChanged = (message) {
      setState(() {
        _lastStatus = message;
      });
    };
  }

  @override
  void dispose() {
    _tabController.dispose();
    _fileWatcher?.dispose();
    _schedulerService?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(48),
        child: AppBar(
          automaticallyImplyLeading: false,
          bottom: TabBar(
            controller: _tabController,
            tabs: _tabs,
            indicatorColor: Colors.white,
          ),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildFileWatchTab(),
          _buildDataExportTab(),
          _buildSchedulerTab(),
          _buildSystemStatusTab(),
        ],
      ),
    );
  }

  Widget _buildFileWatchTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ファイル監視設定
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ファイル監視設定',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: TextEditingController(text: _watchDirectory),
                          decoration: const InputDecoration(
                            labelText: '監視フォルダ',
                            border: OutlineInputBorder(),
                          ),
                          readOnly: true,
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton.icon(
                        onPressed: _selectWatchDirectory,
                        icon: const Icon(Icons.folder),
                        label: const Text('選択'),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  Row(
                    children: [
                      ElevatedButton.icon(
                        onPressed: _watchDirectory.isNotEmpty ? _toggleFileWatch : null,
                        icon: Icon(_isWatchingFiles ? Icons.stop : Icons.play_arrow),
                        label: Text(_isWatchingFiles ? '監視停止' : '監視開始'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _isWatchingFiles ? Colors.red : Colors.green,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Text(
                          _lastStatus,
                          style: TextStyle(
                            color: _isWatchingFiles ? Colors.green : Colors.grey,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // 検出されたファイル一覧
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          '検出されたファイル',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        if (_detectedFiles.isNotEmpty)
                          TextButton.icon(
                            onPressed: () {
                              setState(() {
                                _detectedFiles.clear();
                              });
                            },
                            icon: const Icon(Icons.clear),
                            label: const Text('クリア'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    
                    Expanded(
                      child: _detectedFiles.isEmpty
                          ? const Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.folder_open, size: 48, color: Colors.grey),
                                  SizedBox(height: 8),
                                  Text(
                                    'ファイル監視を開始すると\n検出されたファイルがここに表示されます',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: Colors.grey),
                                  ),
                                ],
                              ),
                            )
                          : ListView.builder(
                              itemCount: _detectedFiles.length,
                              itemBuilder: (context, index) {
                                final file = _detectedFiles[index];
                                return ListTile(
                                  leading: const Icon(Icons.description),
                                  title: Text(file['filename'] ?? ''),
                                  subtitle: Text('${file['type']} - ${DateFormat('MM/dd HH:mm:ss').format(file['time'])}'),
                                  trailing: IconButton(
                                    icon: const Icon(Icons.folder_open),
                                    onPressed: () {
                                      // ファイルの場所を表示する処理
                                    },
                                  ),
                                );
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

  Widget _buildDataExportTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // エクスポートオプション
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'データエクスポート',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  const Text('エクスポート種類を選択してください：'),
                  const SizedBox(height: 12),
                  
                  Wrap(
                    spacing: 8.0,
                    runSpacing: 8.0,
                    children: [
                      ElevatedButton.icon(
                        onPressed: () => _exportData('payments_csv'),
                        icon: const Icon(Icons.payment),
                        label: const Text('支払いデータ (CSV)'),
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _exportData('expenses_csv'),
                        icon: const Icon(Icons.receipt),
                        label: const Text('費用データ (CSV)'),
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _exportData('backup_json'),
                        icon: const Icon(Icons.backup),
                        label: const Text('全データバックアップ (JSON)'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // エクスポート履歴（ダミー）
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'エクスポート履歴',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    const Expanded(
                      child: Center(
                        child: Text(
                          'エクスポート履歴はここに表示されます',
                          style: TextStyle(color: Colors.grey),
                        ),
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

  Widget _buildSchedulerTab() {
    final isSchedulerRunning = _schedulerService?.isRunning ?? false;
    final nextExecution = _schedulerService?.getNextExecutionTime();

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // スケジューラー制御
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '月次費用生成スケジューラー',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  Row(
                    children: [
                      ElevatedButton.icon(
                        onPressed: () {
                          if (isSchedulerRunning) {
                            _schedulerService?.stopScheduler();
                          } else {
                            _schedulerService?.startScheduler();
                          }
                          setState(() {});
                        },
                        icon: Icon(isSchedulerRunning ? Icons.stop : Icons.play_arrow),
                        label: Text(isSchedulerRunning ? 'スケジューラー停止' : 'スケジューラー開始'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: isSchedulerRunning ? Colors.red : Colors.green,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '状態: ${isSchedulerRunning ? "実行中" : "停止中"}',
                              style: TextStyle(
                                color: isSchedulerRunning ? Colors.green : Colors.grey,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (nextExecution != null)
                              Text(
                                '次回実行: ${DateFormat('yyyy/MM/dd HH:mm').format(nextExecution)}',
                                style: const TextStyle(fontSize: 12, color: Colors.grey),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // 手動生成ボタン
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '手動生成',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  const Text('マスター費用から月次費用を手動で生成します'),
                  const SizedBox(height: 12),
                  
                  Wrap(
                    spacing: 8.0,
                    runSpacing: 8.0,
                    children: [
                      ElevatedButton.icon(
                        onPressed: () => _generateCurrentMonth(),
                        icon: const Icon(Icons.today),
                        label: const Text('今月を生成'),
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _showMonthSelectionDialog(),
                        icon: const Icon(Icons.date_range),
                        label: const Text('指定月を生成'),
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _showBulkGenerationDialog(),
                        icon: const Icon(Icons.calendar_month),
                        label: const Text('複数月を生成'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // 生成統計
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '生成履歴・統計',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    FutureBuilder<bool>(
                      future: _schedulerService?.isCurrentMonthGenerated(),
                      builder: (context, snapshot) {
                        final isGenerated = snapshot.data ?? false;
                        return ListTile(
                          leading: Icon(
                            isGenerated ? Icons.check_circle : Icons.pending,
                            color: isGenerated ? Colors.green : Colors.orange,
                          ),
                          title: const Text('今月の費用生成状況'),
                          subtitle: Text(isGenerated ? '生成済み' : '未生成'),
                        );
                      },
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

  Widget _buildSystemStatusTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // システム情報
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'システム情報',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  
                  _buildSystemInfoRow('アプリバージョン', '1.0.0'),
                  _buildSystemInfoRow('プラットフォーム', Platform.operatingSystem),
                  _buildSystemInfoRow('起動時刻', DateFormat('yyyy/MM/dd HH:mm:ss').format(DateTime.now())),
                  _buildSystemInfoRow('ファイル監視状態', _isWatchingFiles ? '監視中' : '停止中'),
                  _buildSystemInfoRow('スケジューラー状態', _schedulerService?.isRunning == true ? '実行中' : '停止中'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSystemInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Future<void> _selectWatchDirectory() async {
    final result = await FilePicker.platform.getDirectoryPath();
    if (result != null) {
      setState(() {
        _watchDirectory = result;
      });
    }
  }

  Future<void> _toggleFileWatch() async {
    if (_isWatchingFiles) {
      await _fileWatcher!.stopWatching();
      setState(() {
        _isWatchingFiles = false;
      });
    } else {
      final success = await _fileWatcher!.startWatching(_watchDirectory);
      setState(() {
        _isWatchingFiles = success;
      });
    }
  }

  Future<void> _exportData(String type) async {
    if (_exportService == null) return;

    try {
      ExportResult? result;
      
      switch (type) {
        case 'payments_csv':
          result = await _exportService!.exportPaymentsToCSV();
          break;
        case 'expenses_csv':
          result = await _exportService!.exportExpensesToCSV();
          break;
        case 'backup_json':
          result = await _exportService!.exportToJSON();
          break;
      }
      
      if (result != null) {
        if (result.success) {
          _showExportSuccessDialog(result);
        } else {
          _showErrorDialog('エクスポートエラー', result.errorMessage ?? '不明なエラー');
        }
      }
      
    } catch (e) {
      _showErrorDialog('エクスポートエラー', 'エクスポート中にエラーが発生しました: $e');
    }
  }

  void _showExportSuccessDialog(ExportResult result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('エクスポート完了'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('ファイル: ${result.filePath}'),
            Text('件数: ${result.recordCount}件'),
            Text('サイズ: ${(result.fileSize / 1024).toStringAsFixed(1)} KB'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
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
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Future<void> _generateCurrentMonth() async {
    try {
      final result = await _schedulerService?.executeManualGeneration();
      if (result?.success == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('今月の費用を${result!.generatedCount}件生成しました'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        _showErrorDialog('生成エラー', result?.errorMessage ?? '不明なエラー');
      }
    } catch (e) {
      _showErrorDialog('生成エラー', '月次費用生成中にエラーが発生しました: $e');
    }
  }

  void _showMonthSelectionDialog() {
    DateTime selectedMonth = DateTime.now();
    bool overwriteExisting = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('指定月の費用生成'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('生成したい月を選択してください'),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Text('対象月: '),
                  TextButton(
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: selectedMonth,
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2030),
                      );
                      if (picked != null) {
                        setState(() {
                          selectedMonth = DateTime(picked.year, picked.month, 1);
                        });
                      }
                    },
                    child: Text('${selectedMonth.year}年${selectedMonth.month}月'),
                  ),
                ],
              ),
              CheckboxListTile(
                title: const Text('既存データを上書き'),
                value: overwriteExisting,
                onChanged: (value) {
                  setState(() {
                    overwriteExisting = value ?? false;
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
              onPressed: () {
                Navigator.pop(context);
                _executeMonthGeneration(selectedMonth, overwriteExisting);
              },
              child: const Text('生成'),
            ),
          ],
        ),
      ),
    );
  }

  void _showBulkGenerationDialog() {
    DateTime startMonth = DateTime.now();
    DateTime endMonth = DateTime.now();
    bool overwriteExisting = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('複数月の一括生成'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('生成したい期間を選択してください'),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Text('開始月: '),
                  TextButton(
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: startMonth,
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2030),
                      );
                      if (picked != null) {
                        setState(() {
                          startMonth = DateTime(picked.year, picked.month, 1);
                        });
                      }
                    },
                    child: Text('${startMonth.year}年${startMonth.month}月'),
                  ),
                ],
              ),
              Row(
                children: [
                  const Text('終了月: '),
                  TextButton(
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: endMonth,
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2030),
                      );
                      if (picked != null) {
                        setState(() {
                          endMonth = DateTime(picked.year, picked.month, 1);
                        });
                      }
                    },
                    child: Text('${endMonth.year}年${endMonth.month}月'),
                  ),
                ],
              ),
              CheckboxListTile(
                title: const Text('既存データを上書き'),
                value: overwriteExisting,
                onChanged: (value) {
                  setState(() {
                    overwriteExisting = value ?? false;
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
              onPressed: () {
                Navigator.pop(context);
                _executeBulkGeneration(startMonth, endMonth, overwriteExisting);
              },
              child: const Text('一括生成'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _executeMonthGeneration(DateTime targetMonth, bool overwriteExisting) async {
    try {
      final result = await _schedulerService?.executeManualGeneration(
        targetMonth: targetMonth,
        overwriteExisting: overwriteExisting,
      );
      
      if (result?.success == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${targetMonth.year}年${targetMonth.month}月の費用を${result!.generatedCount}件生成しました'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        _showErrorDialog('生成エラー', result?.errorMessage ?? '不明なエラー');
      }
    } catch (e) {
      _showErrorDialog('生成エラー', '月次費用生成中にエラーが発生しました: $e');
    }
  }

  Future<void> _executeBulkGeneration(DateTime startMonth, DateTime endMonth, bool overwriteExisting) async {
    try {
      final result = await _schedulerService?.executeBulkGeneration(
        startMonth: startMonth,
        endMonth: endMonth,
        overwriteExisting: overwriteExisting,
      );
      
      if (result?.success == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${result!.generatedMonths.length}ヶ月分の費用を${result.generatedCount}件生成しました'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        _showErrorDialog('生成エラー', result?.errorMessage ?? '不明なエラー');
      }
    } catch (e) {
      _showErrorDialog('生成エラー', '複数月費用生成中にエラーが発生しました: $e');
    }
  }
}