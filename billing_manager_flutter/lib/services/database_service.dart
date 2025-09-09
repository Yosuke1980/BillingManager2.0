import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/payment_model.dart';
import '../models/expense_model.dart';

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
      version: 1,
      onCreate: _onCreate,
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

    // expense_master テーブル作成
    await db.execute('''
      CREATE TABLE expense_master (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE,
        description TEXT,
        default_amount REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1
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

    print('データベーステーブルを作成しました');
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

  // データベースのクローズ
  Future<void> close() async {
    final db = await database;
    await db.close();
  }
}