import 'dart:io';
import 'dart:convert';
import 'dart:typed_data';
import 'package:csv/csv.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import '../models/payment_model.dart';
import '../models/expense_model.dart';
import '../models/master_expense_model.dart';
import 'database_service.dart';

class CsvImportService {
  final DatabaseService _databaseService;

  CsvImportService(this._databaseService);

  // CSVファイルを自動的にUTF-8に変換して読み込み
  Future<String> _readCsvWithEncodingDetection(File file) async {
    final bytes = await file.readAsBytes();
    print('Debug: File size: ${bytes.length} bytes');
    
    // 1. Shift_JISかどうかを判定
    if (await _isShiftJisEncoded(bytes)) {
      print('Debug: Detected Shift_JIS encoding, converting to UTF-8');
      return await _convertShiftJisToUtf8UsingIconv(file);
    }
    
    // 2. UTF-8として読み込み
    try {
      final content = utf8.decode(bytes);
      // 文字化けチェック：制御文字や変な文字が多すぎないかチェック
      final weirdCharCount = content.split('').where((c) => 
        c.codeUnitAt(0) < 32 && c != '\n' && c != '\r' && c != '\t').length;
      
      if (weirdCharCount < content.length * 0.1) { // 10%未満なら正常とみなす
        print('Debug: Using UTF-8 encoding, weird chars: $weirdCharCount/${content.length}');
        return content;
      } else {
        print('Debug: UTF-8 has too many weird chars: $weirdCharCount/${content.length}');
      }
    } catch (e) {
      print('Debug: UTF-8 failed: $e');
    }
    
    // 3. Latin1（バックアップ）を試す
    try {
      final content = latin1.decode(bytes);
      print('Debug: Using Latin1 encoding as fallback');
      return content;
    } catch (e) {
      print('Debug: Latin1 failed: $e');
    }
    
    // 4. 最後の手段：UTF-8でエラーを許容
    print('Debug: Using UTF-8 with allowMalformed');
    return utf8.decode(bytes, allowMalformed: true);
  }

  // Shift_JISエンコーディング判定
  Future<bool> _isShiftJisEncoded(List<int> bytes) async {
    // Shift_JISの特徴的なバイトパターンをチェック
    int shiftJisLikeBytes = 0;
    for (int i = 0; i < bytes.length - 1; i++) {
      final byte1 = bytes[i];
      final byte2 = bytes[i + 1];
      
      // Shift_JISの2バイト文字の範囲
      if ((byte1 >= 0x81 && byte1 <= 0x9f) || (byte1 >= 0xe0 && byte1 <= 0xfc)) {
        if ((byte2 >= 0x40 && byte2 <= 0x7e) || (byte2 >= 0x80 && byte2 <= 0xfc)) {
          shiftJisLikeBytes += 2;
          i++; // 2バイト処理したのでスキップ
        }
      }
    }
    
    // 全体の10%以上がShift_JISパターンならShift_JISと判定
    final ratio = shiftJisLikeBytes / bytes.length;
    print('Debug: Shift_JIS pattern ratio: ${ratio * 100}%');
    return ratio > 0.1;
  }

  // システムiconvを使用したShift_JIS→UTF-8変換
  Future<String> _convertShiftJisToUtf8UsingIconv(File originalFile) async {
    try {
      // 一時ディレクトリを取得
      final tempDir = await getTemporaryDirectory();
      final tempUtf8File = File('${tempDir.path}/temp_utf8_${DateTime.now().millisecondsSinceEpoch}.csv');
      
      // iconvコマンドでShift_JIS→UTF-8変換
      final result = await Process.run('iconv', [
        '-f', 'SHIFT_JIS',
        '-t', 'UTF-8',
        originalFile.path
      ]);
      
      if (result.exitCode == 0) {
        // 変換成功：UTF-8として書き出し
        await tempUtf8File.writeAsString(result.stdout as String);
        final content = await tempUtf8File.readAsString();
        
        // 一時ファイル削除
        if (await tempUtf8File.exists()) {
          await tempUtf8File.delete();
        }
        
        print('Debug: Successfully converted Shift_JIS to UTF-8 using iconv');
        final sample = content.length > 100 ? content.substring(0, 100) : content;
        print('Debug: Converted sample: ${sample.replaceAll('\n', '\\n').replaceAll('\r', '\\r')}');
        return content;
      } else {
        print('Debug: iconv conversion failed: ${result.stderr}');
        throw Exception('iconv conversion failed: ${result.stderr}');
      }
    } catch (e) {
      print('Debug: Error during iconv conversion: $e');
      // フォールバック：UTF-8エラー許容読み込み
      final bytes = await originalFile.readAsBytes();
      return utf8.decode(bytes, allowMalformed: true);
    }
  }

  // CSVファイル選択とインポート処理
  Future<CsvImportResult> importPaymentsFromCsv() async {
    try {
      // ファイル選択
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv'],
        allowMultiple: false,
      );

      if (result == null || result.files.isEmpty) {
        return CsvImportResult.cancelled();
      }

      final file = File(result.files.first.path!);
      final csvContent = await _readCsvWithEncodingDetection(file);
      
      // CSVパース
      final List<List<dynamic>> rows = const CsvToListConverter().convert(csvContent);
      
      if (rows.isEmpty) {
        return CsvImportResult.error('CSVファイルが空です');
      }

      // ヘッダー行を取得（既存のPythonコードのマッピングを参考）
      final headerMapping = {
        'おもて情報.件名': 'subject',
        '明細情報.明細項目': 'project_name',
        'おもて情報.請求元': 'payee',
        'おもて情報.支払先コード': 'payee_code',
        '明細情報.金額': 'amount',
        'おもて情報.自社支払期限': 'payment_date',
        '状態': 'status',
      };

      final headers = rows.first.map((header) => header.toString()).toList();
      final dataRows = rows.skip(1).toList();

      int successCount = 0;
      int errorCount = 0;
      final List<String> errors = [];

      for (int i = 0; i < dataRows.length; i++) {
        try {
          final row = dataRows[i];
          final payment = _parsePaymentFromRow(headers, row, headerMapping);
          
          if (payment != null) {
            await _databaseService.insertPayment(payment);
            successCount++;
          } else {
            errorCount++;
            errors.add('行 ${i + 2}: データが不完全です');
          }
        } catch (e) {
          errorCount++;
          errors.add('行 ${i + 2}: $e');
        }
      }

      return CsvImportResult.success(
        successCount: successCount,
        errorCount: errorCount,
        errors: errors,
      );
    } catch (e) {
      return CsvImportResult.error('インポート処理中にエラーが発生しました: $e');
    }
  }

  // 費用データのCSVインポート
  Future<CsvImportResult> importExpensesFromCsv() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv'],
        allowMultiple: false,
      );

      if (result == null || result.files.isEmpty) {
        return CsvImportResult.cancelled();
      }

      final file = File(result.files.first.path!);
      final csvContent = await _readCsvWithEncodingDetection(file);
      
      final List<List<dynamic>> rows = const CsvToListConverter().convert(csvContent);
      
      if (rows.isEmpty) {
        return CsvImportResult.error('CSVファイルが空です');
      }

      // 費用データ用のヘッダーマッピング
      final headerMapping = {
        '日付': 'date',
        'プロジェクト名': 'project_name',
        'カテゴリ': 'category',
        '説明': 'description',
        '金額': 'amount',
        '支払方法': 'payment_method',
        'レシート番号': 'receipt_number',
        '承認状況': 'approval_status',
        '承認者': 'approver',
        '備考': 'notes',
        'クライアント名': 'client_name',
        '部署': 'department',
      };

      final headers = rows.first.map((header) => header.toString()).toList();
      final dataRows = rows.skip(1).toList();

      int successCount = 0;
      int errorCount = 0;
      final List<String> errors = [];

      for (int i = 0; i < dataRows.length; i++) {
        try {
          final row = dataRows[i];
          final expense = _parseExpenseFromRow(headers, row, headerMapping);
          
          if (expense != null) {
            await _databaseService.insertExpense(expense);
            successCount++;
          } else {
            errorCount++;
            errors.add('行 ${i + 2}: データが不完全です');
          }
        } catch (e) {
          errorCount++;
          errors.add('行 ${i + 2}: $e');
        }
      }

      return CsvImportResult.success(
        successCount: successCount,
        errorCount: errorCount,
        errors: errors,
      );
    } catch (e) {
      return CsvImportResult.error('インポート処理中にエラーが発生しました: $e');
    }
  }

  // 支払いデータの行パース
  Payment? _parsePaymentFromRow(
    List<String> headers,
    List<dynamic> row,
    Map<String, String> headerMapping,
  ) {
    try {
      final Map<String, String> data = {};
      
      for (int i = 0; i < headers.length && i < row.length; i++) {
        final headerKey = headers[i];
        final mappedKey = headerMapping[headerKey] ?? headerKey.toLowerCase();
        data[mappedKey] = row[i]?.toString() ?? '';
      }

      // 必須フィールドのチェック
      if (data['subject']?.isEmpty != false ||
          data['project_name']?.isEmpty != false ||
          data['payee']?.isEmpty != false) {
        return null;
      }

      return Payment(
        subject: data['subject']!,
        projectName: data['project_name']!,
        payee: data['payee']!,
        payeeCode: data['payee_code'] ?? '',
        amount: double.tryParse(data['amount']?.replaceAll(',', '') ?? '0') ?? 0,
        paymentDate: _formatDate(data['payment_date'] ?? ''),
        status: data['status'] ?? '未処理',
        type: data['type'] ?? '',
        clientName: data['client_name'] ?? '',
        department: data['department'] ?? '',
        projectStatus: data['project_status'] ?? '進行中',
        projectStartDate: _formatDate(data['project_start_date'] ?? ''),
        projectEndDate: _formatDate(data['project_end_date'] ?? ''),
        budget: double.tryParse(data['budget']?.replaceAll(',', '') ?? '0') ?? 0,
        approver: data['approver'] ?? '',
        urgencyLevel: data['urgency_level'] ?? '通常',
      );
    } catch (e) {
      return null;
    }
  }

  // 費用データの行パース
  Expense? _parseExpenseFromRow(
    List<String> headers,
    List<dynamic> row,
    Map<String, String> headerMapping,
  ) {
    try {
      final Map<String, String> data = {};
      
      for (int i = 0; i < headers.length && i < row.length; i++) {
        final headerKey = headers[i];
        final mappedKey = headerMapping[headerKey] ?? headerKey.toLowerCase();
        data[mappedKey] = row[i]?.toString() ?? '';
      }

      // 必須フィールドのチェック
      if (data['date']?.isEmpty != false ||
          data['project_name']?.isEmpty != false ||
          data['description']?.isEmpty != false) {
        return null;
      }

      return Expense(
        date: _formatDate(data['date']!),
        projectName: data['project_name']!,
        category: data['category'] ?? '其他',
        description: data['description']!,
        amount: double.tryParse(data['amount']?.replaceAll(',', '') ?? '0') ?? 0,
        paymentMethod: data['payment_method'] ?? '',
        receiptNumber: data['receipt_number'] ?? '',
        approvalStatus: data['approval_status'] ?? '未承認',
        approver: data['approver'] ?? '',
        notes: data['notes'] ?? '',
        clientName: data['client_name'] ?? '',
        department: data['department'] ?? '',
      );
    } catch (e) {
      return null;
    }
  }

  // マスター費用データのCSVインポート
  Future<CsvImportResult> importMasterExpensesFromCsv() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv'],
        allowMultiple: false,
      );

      if (result == null || result.files.isEmpty) {
        return CsvImportResult.cancelled();
      }

      final file = File(result.files.first.path!);
      final csvContent = await _readCsvWithEncodingDetection(file);
      
      final List<List<dynamic>> rows = const CsvToListConverter().convert(csvContent);
      
      if (rows.isEmpty) {
        return CsvImportResult.error('CSVファイルが空です');
      }

      // マスター費用データ用のヘッダーマッピング（既存の支払いデータ形式に対応）
      final headerMapping = {
        // 既存の支払いデータ形式のマッピング
        '費目名': 'name',
        '支払先名': 'payee_name',
        '支払先コード': 'payee_code', 
        '金額': 'amount',
        '頻度': 'frequency',
        '開始日': 'start_date',
        '終了日': 'end_date',
        '備考月日': 'notes',
        
        // 従来のマスター費用形式のマッピング（下位互換性）
        'カテゴリ': 'category',
        '支払日': 'day_of_month',
        '説明': 'description',
        'アクティブ': 'is_active',
        'プロジェクト名': 'project_name',
        '部署': 'department',
        '支払方法': 'payment_method',
        'タグ': 'tags',
      };

      final headers = rows.first.map((header) => header.toString()).toList();
      final dataRows = rows.skip(1).toList();

      int successCount = 0;
      int errorCount = 0;
      final List<String> errors = [];

      for (int i = 0; i < dataRows.length; i++) {
        try {
          final row = dataRows[i];
          final masterExpense = _parseMasterExpenseFromRow(headers, row, headerMapping);
          
          if (masterExpense != null) {
            await _databaseService.insertMasterExpense(masterExpense);
            successCount++;
          } else {
            errorCount++;
            errors.add('行 ${i + 2}: データが不完全です');
          }
        } catch (e) {
          errorCount++;
          errors.add('行 ${i + 2}: $e');
        }
      }

      return CsvImportResult.success(
        successCount: successCount,
        errorCount: errorCount,
        errors: errors,
      );
    } catch (e) {
      return CsvImportResult.error('インポート処理中にエラーが発生しました: $e');
    }
  }

  // マスター費用データの行パース
  MasterExpenseModel? _parseMasterExpenseFromRow(
    List<String> headers,
    List<dynamic> row,
    Map<String, String> headerMapping,
  ) {
    try {
      // デバッグログ出力
      print('Debug: Headers = $headers');
      print('Debug: Raw row = $row');
      
      // 位置ベースで直接データを取得（Mapを使わずに）
      String? name, payeeName, payeeCode, amountStr, frequencyStr;
      
      if (row.length >= 2) name = row[1]?.toString();           // 2番目：名前（費目名）
      if (row.length >= 3) payeeName = row[2]?.toString();      // 3番目：支払先名
      if (row.length >= 4) payeeCode = row[3]?.toString();      // 4番目：支払先コード  
      if (row.length >= 5) amountStr = row[4]?.toString();      // 5番目：金額
      if (row.length >= 6) frequencyStr = row[5]?.toString();   // 6番目：頻度
      
      print('Debug: Name (index 1) = $name');
      print('Debug: PayeeName (index 2) = $payeeName');
      print('Debug: Amount (index 4) = $amountStr');

      // 必須フィールドのチェック（支払いデータ形式では費目名のみ必須）
      if (name?.trim().isEmpty != false) {
        print('Debug: Name field is empty or null');
        return null;
      }

      // カテゴリの決定（支払先名を使用、なければ'一般'）
      String category = payeeName ?? '一般';
      
      // 支払方法の決定（支払先コードを使用、なければ'銀行振込'）
      String paymentMethod = (payeeCode?.isNotEmpty == true ? '銀行振込' : '現金');

      // 頻度の正規化（支払いデータ形式に対応）
      String frequency = frequencyStr?.toLowerCase() ?? 'monthly';
      switch (frequency) {
        case '月額定額':
        case '月次':
        case '毎月':
        case 'monthly':
          frequency = 'monthly';
          break;
        case '回数ベース':
          // 回数ベースはデフォルトで月次とする
          frequency = 'monthly';
          break;
        case '四半期':
        case '3ヶ月':
        case 'quarterly':
          frequency = 'quarterly';
          break;
        case '半期':
        case '6ヶ月':
        case 'semi_annually':
          frequency = 'semi_annually';
          break;
        case '年次':
        case '毎年':
        case 'yearly':
          frequency = 'yearly';
          break;
        default:
          frequency = 'monthly';
      }

      final now = DateTime.now();
      return MasterExpenseModel(
        name: name!,
        category: category,
        amount: double.tryParse((amountStr ?? '0').replaceAll(',', '')) ?? 0,
        frequency: frequency,
        dayOfMonth: 1,
        description: payeeName ?? name,
        isActive: true,
        projectName: null,
        department: null,
        paymentMethod: paymentMethod,
        tags: payeeCode,
        createdAt: now,
        updatedAt: now,
      );
    } catch (e) {
      return null;
    }
  }

  // Boolean値のパース
  bool _parseBoolean(String value) {
    final lowerValue = value.toLowerCase().trim();
    return lowerValue == 'true' || 
           lowerValue == '1' || 
           lowerValue == 'はい' || 
           lowerValue == 'yes' || 
           lowerValue == 'アクティブ' ||
           lowerValue == '有効';
  }

  // 日付フォーマット統一
  String _formatDate(String dateStr) {
    if (dateStr.isEmpty) return '';
    
    try {
      // 様々な日付フォーマットに対応
      final cleanDate = dateStr.replaceAll(RegExp(r'[^\d-/]'), '');
      
      if (cleanDate.contains('/')) {
        final parts = cleanDate.split('/');
        if (parts.length == 3) {
          final year = parts[0].length == 4 ? parts[0] : '20${parts[2].padLeft(2, '0')}';
          final month = parts[1].padLeft(2, '0');
          final day = parts[2].length == 4 ? parts[0] : parts[2].padLeft(2, '0');
          return '$year-$month-$day';
        }
      } else if (cleanDate.contains('-')) {
        return cleanDate; // 既にYYYY-MM-DD形式
      }
      
      return cleanDate;
    } catch (e) {
      return dateStr;
    }
  }
}

// インポート結果クラス
class CsvImportResult {
  final bool success;
  final bool cancelled;
  final String? errorMessage;
  final int successCount;
  final int errorCount;
  final List<String> errors;

  CsvImportResult._({
    required this.success,
    required this.cancelled,
    this.errorMessage,
    required this.successCount,
    required this.errorCount,
    required this.errors,
  });

  factory CsvImportResult.success({
    required int successCount,
    required int errorCount,
    required List<String> errors,
  }) {
    return CsvImportResult._(
      success: true,
      cancelled: false,
      successCount: successCount,
      errorCount: errorCount,
      errors: errors,
    );
  }

  factory CsvImportResult.error(String message) {
    return CsvImportResult._(
      success: false,
      cancelled: false,
      errorMessage: message,
      successCount: 0,
      errorCount: 0,
      errors: [],
    );
  }

  factory CsvImportResult.cancelled() {
    return CsvImportResult._(
      success: false,
      cancelled: true,
      successCount: 0,
      errorCount: 0,
      errors: [],
    );
  }
}