import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/payment_model.dart';
import '../models/expense_model.dart';
import '../models/master_expense_model.dart';
import '../models/reconciliation_model.dart';

class DatabaseService {
  static Database? _database;
  static const String _billingDb = 'billing.db';
  static const String _expensesDb = 'expenses.db';

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _billingDb);

    return await openDatabase(
      path,
      version: 3,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    // payments テーブル作成
    await db.execute('''
      CREATE TABLE payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        project_name TEXT,
        payee TEXT,
        payee_code TEXT,
        amount REAL,
        payment_date TEXT,
        status TEXT DEFAULT '未処理',
        type TEXT DEFAULT '',
        client_name TEXT DEFAULT '',
        department TEXT DEFAULT '',
        project_status TEXT DEFAULT '進行中',
        project_start_date TEXT DEFAULT '',
        project_end_date TEXT DEFAULT '',
        budget REAL DEFAULT 0,
        approver TEXT DEFAULT '',
        urgency_level TEXT DEFAULT '通常'
      )
    ''');

    // expenses テーブル作成
    await db.execute('''
      CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        project_name TEXT,
        category TEXT,
        description TEXT,
        amount REAL,
        payment_method TEXT DEFAULT '',
        receipt_number TEXT DEFAULT '',
        approval_status TEXT DEFAULT '未承認',
        approver TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        client_name TEXT DEFAULT '',
        department TEXT DEFAULT ''
      )
    ''');

    // expense_master テーブル作成（既存）
    await db.execute('''
      CREATE TABLE expense_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE,
        description TEXT,
        default_amount REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1
      )
    ''');

    // master_expenses テーブル作成（新規）
    await db.execute('''
      CREATE TABLE master_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        frequency TEXT NOT NULL DEFAULT 'monthly',
        day_of_month INTEGER NOT NULL DEFAULT 1,
        description TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        project_name TEXT,
        department TEXT,
        payment_method TEXT NOT NULL,
        tags TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    // payee_master テーブル作成
    await db.execute('''
      CREATE TABLE payee_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payee_code TEXT UNIQUE,
        payee_name TEXT,
        address TEXT DEFAULT '',
        contact_info TEXT DEFAULT '',
        payment_terms TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1
      )
    ''');

    // reconciliations テーブル作成
    await db.execute('''
      CREATE TABLE reconciliations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id INTEGER,
        expense_id INTEGER,
        reconciliation_type TEXT NOT NULL DEFAULT 'manual',
        status TEXT NOT NULL DEFAULT 'unmatched',
        amount_difference REAL,
        notes TEXT,
        matched_at TEXT NOT NULL,
        matched_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (payment_id) REFERENCES payments (id),
        FOREIGN KEY (expense_id) REFERENCES expenses (id)
      )
    ''');

    print('データベーステーブルを作成しました');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      // master_expenses テーブルを追加
      await db.execute('''
        CREATE TABLE master_expenses (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          category TEXT NOT NULL,
          amount REAL NOT NULL,
          frequency TEXT NOT NULL DEFAULT 'monthly',
          day_of_month INTEGER NOT NULL DEFAULT 1,
          description TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          project_name TEXT,
          department TEXT,
          payment_method TEXT NOT NULL,
          tags TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
      ''');
      print('master_expenses テーブルを追加しました');
    }
    
    if (oldVersion < 3) {
      // reconciliations テーブルを追加
      await db.execute('''
        CREATE TABLE reconciliations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          payment_id INTEGER,
          expense_id INTEGER,
          reconciliation_type TEXT NOT NULL DEFAULT 'manual',
          status TEXT NOT NULL DEFAULT 'unmatched',
          amount_difference REAL,
          notes TEXT,
          matched_at TEXT NOT NULL,
          matched_by TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (payment_id) REFERENCES payments (id),
          FOREIGN KEY (expense_id) REFERENCES expenses (id)
        )
      ''');
      print('reconciliations テーブルを追加しました');
    }
  }

  // Payments CRUD操作
  Future<int> insertPayment(Payment payment) async {
    final db = await database;
    return await db.insert('payments', payment.toMap());
  }

  Future<List<Payment>> getAllPayments() async {
    final db = await database;
    final maps = await db.query('payments', orderBy: 'payment_date DESC');
    return List.generate(maps.length, (i) => Payment.fromMap(maps[i]));
  }

  Future<Payment?> getPayment(int id) async {
    final db = await database;
    final maps = await db.query(
      'payments',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    
    if (maps.isNotEmpty) {
      return Payment.fromMap(maps.first);
    }
    return null;
  }

  Future<int> updatePayment(Payment payment) async {
    final db = await database;
    return await db.update(
      'payments',
      payment.toMap(),
      where: 'id = ?',
      whereArgs: [payment.id],
    );
  }

  Future<int> deletePayment(int id) async {
    final db = await database;
    return await db.delete(
      'payments',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Expenses CRUD操作
  Future<int> insertExpense(Expense expense) async {
    final db = await database;
    return await db.insert('expenses', expense.toMap());
  }

  Future<List<Expense>> getAllExpenses() async {
    final db = await database;
    final maps = await db.query('expenses', orderBy: 'date DESC');
    return List.generate(maps.length, (i) => Expense.fromMap(maps[i]));
  }

  Future<Expense?> getExpense(int id) async {
    final db = await database;
    final maps = await db.query(
      'expenses',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    
    if (maps.isNotEmpty) {
      return Expense.fromMap(maps.first);
    }
    return null;
  }

  Future<int> updateExpense(Expense expense) async {
    final db = await database;
    return await db.update(
      'expenses',
      expense.toMap(),
      where: 'id = ?',
      whereArgs: [expense.id],
    );
  }

  Future<int> deleteExpense(int id) async {
    final db = await database;
    return await db.delete(
      'expenses',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // フィルタリング・検索機能
  Future<List<Payment>> searchPayments({
    String? status,
    String? projectName,
    String? payee,
    String? startDate,
    String? endDate,
  }) async {
    final db = await database;
    String whereClause = '1=1';
    List<dynamic> whereArgs = [];

    if (status != null && status.isNotEmpty) {
      whereClause += ' AND status = ?';
      whereArgs.add(status);
    }
    
    if (projectName != null && projectName.isNotEmpty) {
      whereClause += ' AND project_name LIKE ?';
      whereArgs.add('%$projectName%');
    }
    
    if (payee != null && payee.isNotEmpty) {
      whereClause += ' AND payee LIKE ?';
      whereArgs.add('%$payee%');
    }

    if (startDate != null && startDate.isNotEmpty) {
      whereClause += ' AND payment_date >= ?';
      whereArgs.add(startDate);
    }

    if (endDate != null && endDate.isNotEmpty) {
      whereClause += ' AND payment_date <= ?';
      whereArgs.add(endDate);
    }

    final maps = await db.query(
      'payments',
      where: whereClause,
      whereArgs: whereArgs,
      orderBy: 'payment_date DESC',
    );

    return List.generate(maps.length, (i) => Payment.fromMap(maps[i]));
  }

  Future<List<Expense>> searchExpenses({
    String? category,
    String? projectName,
    String? startDate,
    String? endDate,
  }) async {
    final db = await database;
    String whereClause = '1=1';
    List<dynamic> whereArgs = [];

    if (category != null && category.isNotEmpty) {
      whereClause += ' AND category = ?';
      whereArgs.add(category);
    }
    
    if (projectName != null && projectName.isNotEmpty) {
      whereClause += ' AND project_name LIKE ?';
      whereArgs.add('%$projectName%');
    }

    if (startDate != null && startDate.isNotEmpty) {
      whereClause += ' AND date >= ?';
      whereArgs.add(startDate);
    }

    if (endDate != null && endDate.isNotEmpty) {
      whereClause += ' AND date <= ?';
      whereArgs.add(endDate);
    }

    final maps = await db.query(
      'expenses',
      where: whereClause,
      whereArgs: whereArgs,
      orderBy: 'date DESC',
    );

    return List.generate(maps.length, (i) => Expense.fromMap(maps[i]));
  }

  // Master Expenses CRUD操作
  Future<int> insertMasterExpense(MasterExpenseModel masterExpense) async {
    final db = await database;
    return await db.insert('master_expenses', masterExpense.toMap());
  }

  Future<List<MasterExpenseModel>> getAllMasterExpenses() async {
    final db = await database;
    final maps = await db.query('master_expenses', orderBy: 'name ASC');
    return List.generate(maps.length, (i) => MasterExpenseModel.fromMap(maps[i]));
  }

  Future<List<MasterExpenseModel>> getActiveMasterExpenses() async {
    final db = await database;
    final maps = await db.query(
      'master_expenses',
      where: 'is_active = ?',
      whereArgs: [1],
      orderBy: 'name ASC',
    );
    return List.generate(maps.length, (i) => MasterExpenseModel.fromMap(maps[i]));
  }

  Future<MasterExpenseModel?> getMasterExpense(int id) async {
    final db = await database;
    final maps = await db.query(
      'master_expenses',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    
    if (maps.isNotEmpty) {
      return MasterExpenseModel.fromMap(maps.first);
    }
    return null;
  }

  Future<int> updateMasterExpense(MasterExpenseModel masterExpense) async {
    final db = await database;
    return await db.update(
      'master_expenses',
      masterExpense.toMap(),
      where: 'id = ?',
      whereArgs: [masterExpense.id],
    );
  }

  Future<int> deleteMasterExpense(int id) async {
    final db = await database;
    return await db.delete(
      'master_expenses',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// 月次費用を自動生成
  Future<ExpenseGenerationResult> generateMonthlyExpenses({
    DateTime? targetMonth,
    bool overwriteExisting = false,
  }) async {
    try {
      final targetDate = targetMonth ?? DateTime.now();
      final yearMonth = '${targetDate.year}-${targetDate.month.toString().padLeft(2, '0')}';
      
      // アクティブなマスター費用を取得
      final masterExpenses = await getActiveMasterExpenses();
      
      if (masterExpenses.isEmpty) {
        return ExpenseGenerationResult.error('アクティブなマスター費用がありません');
      }

      final db = await database;
      int generatedCount = 0;
      final List<String> generatedMonths = [yearMonth];

      for (final master in masterExpenses) {
        // 頻度に基づいて生成が必要かチェック
        if (!_shouldGenerateExpense(master, targetDate)) {
          continue;
        }

        // 同じ月に既に生成されているかチェック
        final existingExpenses = await db.query(
          'expenses',
          where: 'project_name = ? AND category = ? AND date LIKE ?',
          whereArgs: [master.projectName ?? '', master.category, '$yearMonth-%'],
        );

        if (existingExpenses.isNotEmpty && !overwriteExisting) {
          continue; // 既存データがあり上書きしない場合はスキップ
        }

        // 上書きの場合は既存データを削除
        if (existingExpenses.isNotEmpty && overwriteExisting) {
          for (final existing in existingExpenses) {
            await db.delete('expenses', where: 'id = ?', whereArgs: [existing['id']]);
          }
        }

        // 支払日を計算
        final paymentDay = master.dayOfMonth.clamp(1, _getDaysInMonth(targetDate.year, targetDate.month));
        final expenseDate = DateTime(targetDate.year, targetDate.month, paymentDay);

        // 新しい費用エントリを作成
        final expense = Expense(
          date: expenseDate.toIso8601String().substring(0, 10),
          projectName: master.projectName ?? '',
          category: master.category,
          description: '${master.name} (${master.frequency})',
          amount: master.amount,
          paymentMethod: master.paymentMethod,
          receiptNumber: '',
          approvalStatus: '未承認',
          approver: '',
          notes: master.description ?? '',
          clientName: '',
          department: master.department ?? '',
        );

        await insertExpense(expense);
        generatedCount++;
      }

      return ExpenseGenerationResult.success(
        generatedCount: generatedCount,
        generatedMonths: generatedMonths,
      );

    } catch (e) {
      return ExpenseGenerationResult.error('月次費用生成エラー: $e');
    }
  }

  /// 複数月の費用を一括生成
  Future<ExpenseGenerationResult> generateExpensesForRange({
    required DateTime startMonth,
    required DateTime endMonth,
    bool overwriteExisting = false,
  }) async {
    try {
      int totalGenerated = 0;
      final List<String> generatedMonths = [];

      DateTime currentMonth = DateTime(startMonth.year, startMonth.month, 1);
      final endDate = DateTime(endMonth.year, endMonth.month, 1);

      while (currentMonth.isBefore(endDate) || currentMonth.isAtSameMomentAs(endDate)) {
        final result = await generateMonthlyExpenses(
          targetMonth: currentMonth,
          overwriteExisting: overwriteExisting,
        );

        if (result.success) {
          totalGenerated += result.generatedCount;
          generatedMonths.addAll(result.generatedMonths);
        }

        // 次の月に移動
        if (currentMonth.month == 12) {
          currentMonth = DateTime(currentMonth.year + 1, 1, 1);
        } else {
          currentMonth = DateTime(currentMonth.year, currentMonth.month + 1, 1);
        }
      }

      return ExpenseGenerationResult.success(
        generatedCount: totalGenerated,
        generatedMonths: generatedMonths,
      );

    } catch (e) {
      return ExpenseGenerationResult.error('複数月費用生成エラー: $e');
    }
  }

  /// 頻度に基づいて生成が必要かチェック
  bool _shouldGenerateExpense(MasterExpenseModel master, DateTime targetDate) {
    final frequency = ExpenseFrequency.fromString(master.frequency);
    
    switch (frequency) {
      case ExpenseFrequency.monthly:
        return true;
      case ExpenseFrequency.quarterly:
        return targetDate.month % 3 == 1; // 1, 4, 7, 10月
      case ExpenseFrequency.semiAnnually:
        return targetDate.month == 1 || targetDate.month == 7;
      case ExpenseFrequency.yearly:
        return targetDate.month == 1;
      case ExpenseFrequency.custom:
        return true; // カスタムは手動で管理
    }
  }

  /// 月の日数を取得
  int _getDaysInMonth(int year, int month) {
    return DateTime(year, month + 1, 0).day;
  }

  // Reconciliation CRUD操作
  Future<int> insertReconciliation(ReconciliationRecord reconciliation) async {
    final db = await database;
    return await db.insert('reconciliations', reconciliation.toMap());
  }

  Future<List<ReconciliationRecord>> getAllReconciliations() async {
    final db = await database;
    final maps = await db.query('reconciliations', orderBy: 'matched_at DESC');
    return List.generate(maps.length, (i) => ReconciliationRecord.fromMap(maps[i]));
  }

  Future<ReconciliationRecord?> getReconciliation(int id) async {
    final db = await database;
    final maps = await db.query(
      'reconciliations',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    
    if (maps.isNotEmpty) {
      return ReconciliationRecord.fromMap(maps.first);
    }
    return null;
  }

  Future<List<ReconciliationRecord>> getReconciliationsByIds({
    List<int>? paymentIds,
    List<int>? expenseIds,
  }) async {
    final db = await database;
    String whereClause = '1=0'; // Start with false condition
    List<dynamic> whereArgs = [];

    if (paymentIds != null && paymentIds.isNotEmpty) {
      whereClause += ' OR payment_id IN (${paymentIds.map((_) => '?').join(',')})';
      whereArgs.addAll(paymentIds);
    }

    if (expenseIds != null && expenseIds.isNotEmpty) {
      whereClause += ' OR expense_id IN (${expenseIds.map((_) => '?').join(',')})';
      whereArgs.addAll(expenseIds);
    }

    final maps = await db.query(
      'reconciliations',
      where: whereClause,
      whereArgs: whereArgs,
      orderBy: 'matched_at DESC',
    );

    return List.generate(maps.length, (i) => ReconciliationRecord.fromMap(maps[i]));
  }

  Future<List<ReconciliationRecord>> getReconciliationsByPaymentId(int paymentId) async {
    final db = await database;
    final maps = await db.query(
      'reconciliations',
      where: 'payment_id = ?',
      whereArgs: [paymentId],
      orderBy: 'matched_at DESC',
    );
    return List.generate(maps.length, (i) => ReconciliationRecord.fromMap(maps[i]));
  }

  Future<List<ReconciliationRecord>> getReconciliationsByExpenseId(int expenseId) async {
    final db = await database;
    final maps = await db.query(
      'reconciliations',
      where: 'expense_id = ?',
      whereArgs: [expenseId],
      orderBy: 'matched_at DESC',
    );
    return List.generate(maps.length, (i) => ReconciliationRecord.fromMap(maps[i]));
  }

  Future<List<ReconciliationRecord>> searchReconciliations({
    String? status,
    String? reconciliationType,
    String? startDate,
    String? endDate,
  }) async {
    final db = await database;
    String whereClause = '1=1';
    List<dynamic> whereArgs = [];

    if (status != null && status.isNotEmpty) {
      whereClause += ' AND status = ?';
      whereArgs.add(status);
    }

    if (reconciliationType != null && reconciliationType.isNotEmpty) {
      whereClause += ' AND reconciliation_type = ?';
      whereArgs.add(reconciliationType);
    }

    if (startDate != null && startDate.isNotEmpty) {
      whereClause += ' AND matched_at >= ?';
      whereArgs.add(startDate);
    }

    if (endDate != null && endDate.isNotEmpty) {
      whereClause += ' AND matched_at <= ?';
      whereArgs.add(endDate);
    }

    final maps = await db.query(
      'reconciliations',
      where: whereClause,
      whereArgs: whereArgs,
      orderBy: 'matched_at DESC',
    );

    return List.generate(maps.length, (i) => ReconciliationRecord.fromMap(maps[i]));
  }

  Future<int> updateReconciliation(ReconciliationRecord reconciliation) async {
    final db = await database;
    return await db.update(
      'reconciliations',
      reconciliation.toMap(),
      where: 'id = ?',
      whereArgs: [reconciliation.id],
    );
  }

  Future<int> deleteReconciliation(int id) async {
    final db = await database;
    return await db.delete(
      'reconciliations',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// 照合統計を取得
  Future<Map<String, dynamic>> getReconciliationStats({
    String? startDate,
    String? endDate,
  }) async {
    final db = await database;
    String dateFilter = '';
    List<dynamic> whereArgs = [];

    if (startDate != null && endDate != null) {
      dateFilter = ' WHERE matched_at >= ? AND matched_at <= ?';
      whereArgs = [startDate, endDate];
    }

    final result = await db.rawQuery('''
      SELECT 
        status,
        COUNT(*) as count,
        SUM(CASE WHEN amount_difference IS NOT NULL THEN amount_difference ELSE 0 END) as total_difference
      FROM reconciliations$dateFilter
      GROUP BY status
    ''', whereArgs);

    final stats = <String, dynamic>{
      'matched': 0,
      'partial': 0,
      'unmatched': 0,
      'total_difference': 0.0,
    };

    for (final row in result) {
      final status = row['status'] as String;
      final count = row['count'] as int;
      final difference = (row['total_difference'] as num?)?.toDouble() ?? 0.0;
      
      stats[status] = count;
      stats['total_difference'] = (stats['total_difference'] as double) + difference;
    }

    return stats;
  }

  // データベースのクローズ
  Future<void> close() async {
    final db = await database;
    await db.close();
  }
}