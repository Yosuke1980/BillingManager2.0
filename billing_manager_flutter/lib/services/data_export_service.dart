import 'dart:io';
import 'dart:convert';
import 'package:csv/csv.dart';
import 'package:path/path.dart' as path;
import 'package:intl/intl.dart';
import '../models/payment_model.dart';
import '../models/expense_model.dart';
import 'database_service.dart';

class DataExportService {
  final DatabaseService _databaseService;
  
  DataExportService(this._databaseService);
  
  /// 支払いデータをCSVエクスポート
  Future<ExportResult> exportPaymentsToCSV({
    String? filePath,
    DateTime? startDate,
    DateTime? endDate,
    String? status,
    String? projectName,
  }) async {
    try {
      // データを取得
      final payments = await _databaseService.searchPayments(
        status: status,
        projectName: projectName,
        startDate: startDate?.toIso8601String(),
        endDate: endDate?.toIso8601String(),
      );
      
      if (payments.isEmpty) {
        return ExportResult.error('エクスポートするデータがありません');
      }
      
      // CSVヘッダー
      final headers = [
        'ID',
        '件名',
        'プロジェクト名',
        '支払い先',
        '支払い先コード',
        '金額',
        '支払日',
        'ステータス',
        'タイプ',
        'クライアント名',
        '部署',
        'プロジェクトステータス',
        'プロジェクト開始日',
        'プロジェクト終了日',
        '予算',
        '承認者',
        '緊急度',
        'エクスポート日時',
      ];
      
      // CSVデータ
      final rows = <List<String>>[];
      rows.add(headers);
      
      final exportTime = DateFormat('yyyy-MM-dd HH:mm:ss').format(DateTime.now());
      
      for (final payment in payments) {
        rows.add([
          payment.id?.toString() ?? '',
          payment.subject,
          payment.projectName,
          payment.payee,
          payment.payeeCode,
          payment.amount.toString(),
          payment.paymentDate,
          payment.status,
          payment.type,
          payment.clientName,
          payment.department,
          payment.projectStatus,
          payment.projectStartDate,
          payment.projectEndDate,
          payment.budget.toString(),
          payment.approver,
          payment.urgencyLevel,
          exportTime,
        ]);
      }
      
      // ファイルパス生成
      final fileName = filePath ?? _generateFileName('payments', 'csv');
      
      // CSV書き込み
      final csvString = const ListToCsvConverter().convert(rows);
      final file = File(fileName);
      await file.writeAsString(csvString, encoding: utf8);
      
      return ExportResult.success(
        filePath: fileName,
        recordCount: payments.length,
        fileSize: await file.length(),
      );
      
    } catch (e) {
      return ExportResult.error('CSVエクスポートに失敗しました: $e');
    }
  }
  
  /// 費用データをCSVエクスポート
  Future<ExportResult> exportExpensesToCSV({
    String? filePath,
    DateTime? startDate,
    DateTime? endDate,
    String? category,
    String? projectName,
  }) async {
    try {
      // データを取得
      final expenses = await _databaseService.searchExpenses(
        category: category,
        projectName: projectName,
        startDate: startDate?.toIso8601String(),
        endDate: endDate?.toIso8601String(),
      );
      
      if (expenses.isEmpty) {
        return ExportResult.error('エクスポートするデータがありません');
      }
      
      // CSVヘッダー
      final headers = [
        'ID',
        '日付',
        'プロジェクト名',
        'カテゴリ',
        '説明',
        '金額',
        '支払方法',
        'レシート番号',
        '承認状況',
        '承認者',
        '備考',
        'クライアント名',
        '部署',
        'エクスポート日時',
      ];
      
      // CSVデータ
      final rows = <List<String>>[];
      rows.add(headers);
      
      final exportTime = DateFormat('yyyy-MM-dd HH:mm:ss').format(DateTime.now());
      
      for (final expense in expenses) {
        rows.add([
          expense.id?.toString() ?? '',
          expense.date,
          expense.projectName,
          expense.category,
          expense.description,
          expense.amount.toString(),
          expense.paymentMethod,
          expense.receiptNumber,
          expense.approvalStatus,
          expense.approver,
          expense.notes,
          expense.clientName,
          expense.department,
          exportTime,
        ]);
      }
      
      // ファイルパス生成
      final fileName = filePath ?? _generateFileName('expenses', 'csv');
      
      // CSV書き込み
      final csvString = const ListToCsvConverter().convert(rows);
      final file = File(fileName);
      await file.writeAsString(csvString, encoding: utf8);
      
      return ExportResult.success(
        filePath: fileName,
        recordCount: expenses.length,
        fileSize: await file.length(),
      );
      
    } catch (e) {
      return ExportResult.error('CSVエクスポートに失敗しました: $e');
    }
  }
  
  /// JSONエクスポート（バックアップ用）
  Future<ExportResult> exportToJSON({
    String? filePath,
    bool includePayments = true,
    bool includeExpenses = true,
  }) async {
    try {
      final Map<String, dynamic> data = {
        'export_info': {
          'timestamp': DateTime.now().toIso8601String(),
          'version': '1.0.0',
          'app': 'billing_manager_flutter',
        },
      };
      
      int totalRecords = 0;
      
      if (includePayments) {
        final payments = await _databaseService.getAllPayments();
        data['payments'] = payments.map((p) => p.toMap()).toList();
        totalRecords += payments.length;
      }
      
      if (includeExpenses) {
        final expenses = await _databaseService.getAllExpenses();
        data['expenses'] = expenses.map((e) => e.toMap()).toList();
        totalRecords += expenses.length;
      }
      
      if (totalRecords == 0) {
        return ExportResult.error('エクスポートするデータがありません');
      }
      
      // ファイルパス生成
      final fileName = filePath ?? _generateFileName('backup', 'json');
      
      // JSON書き込み
      final jsonString = const JsonEncoder.withIndent('  ').convert(data);
      final file = File(fileName);
      await file.writeAsString(jsonString, encoding: utf8);
      
      return ExportResult.success(
        filePath: fileName,
        recordCount: totalRecords,
        fileSize: await file.length(),
      );
      
    } catch (e) {
      return ExportResult.error('JSONエクスポートに失敗しました: $e');
    }
  }
  
  /// レポート形式でエクスポート
  Future<ExportResult> exportReport({
    required ReportType reportType,
    String? filePath,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final fileName = filePath ?? _generateFileName('report_${reportType.name}', 'csv');
      
      switch (reportType) {
        case ReportType.monthlySummary:
          return await _exportMonthlySummary(fileName, startDate, endDate);
        case ReportType.projectSummary:
          return await _exportProjectSummary(fileName, startDate, endDate);
        case ReportType.payeeSummary:
          return await _exportPayeeSummary(fileName, startDate, endDate);
        case ReportType.expenseByCategory:
          return await _exportExpenseByCategory(fileName, startDate, endDate);
      }
    } catch (e) {
      return ExportResult.error('レポートエクスポートに失敗しました: $e');
    }
  }
  
  /// 月次集計レポート
  Future<ExportResult> _exportMonthlySummary(
    String fileName, 
    DateTime? startDate, 
    DateTime? endDate
  ) async {
    // 実装は省略 - 月次集計ロジック
    return ExportResult.error('月次集計レポートは実装中です');
  }
  
  /// プロジェクト集計レポート
  Future<ExportResult> _exportProjectSummary(
    String fileName,
    DateTime? startDate,
    DateTime? endDate
  ) async {
    // 実装は省略 - プロジェクト集計ロジック
    return ExportResult.error('プロジェクト集計レポートは実装中です');
  }
  
  /// 支払い先集計レポート
  Future<ExportResult> _exportPayeeSummary(
    String fileName,
    DateTime? startDate,
    DateTime? endDate
  ) async {
    // 実装は省略 - 支払い先集計ロジック
    return ExportResult.error('支払い先集計レポートは実装中です');
  }
  
  /// 費用カテゴリ別集計レポート
  Future<ExportResult> _exportExpenseByCategory(
    String fileName,
    DateTime? startDate,
    DateTime? endDate
  ) async {
    // 実装は省略 - 費用カテゴリ集計ロジック
    return ExportResult.error('費用カテゴリ集計レポートは実装中です');
  }
  
  /// ファイル名生成
  String _generateFileName(String prefix, String extension) {
    final timestamp = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
    return path.join(
      Directory.systemTemp.path,
      '${prefix}_$timestamp.$extension',
    );
  }
}

/// エクスポート結果クラス
class ExportResult {
  final bool success;
  final String? filePath;
  final int recordCount;
  final int fileSize;
  final String? errorMessage;
  
  ExportResult._({
    required this.success,
    this.filePath,
    required this.recordCount,
    required this.fileSize,
    this.errorMessage,
  });
  
  factory ExportResult.success({
    required String filePath,
    required int recordCount,
    required int fileSize,
  }) {
    return ExportResult._(
      success: true,
      filePath: filePath,
      recordCount: recordCount,
      fileSize: fileSize,
    );
  }
  
  factory ExportResult.error(String message) {
    return ExportResult._(
      success: false,
      recordCount: 0,
      fileSize: 0,
      errorMessage: message,
    );
  }
}

/// レポートタイプ
enum ReportType {
  monthlySummary,    // 月次集計
  projectSummary,    // プロジェクト別集計
  payeeSummary,      // 支払い先別集計
  expenseByCategory, // 費用カテゴリ別集計
}