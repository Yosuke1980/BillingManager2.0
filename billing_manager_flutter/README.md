# ラジオ局支払い・費用管理システム (Flutter版)

PyQt5からFlutterに移行したクロスプラットフォーム対応の支払い・費用管理システムです。

## 特徴

### ✨ 主な機能
- **支払い管理**: 請求書の支払い情報を管理
- **費用管理**: 経費データの登録・承認管理
- **CSVインポート**: 既存データの一括インポート機能
- **検索・フィルター**: 柔軟な条件による データ検索
- **統計表示**: 支払い・費用の統計情報表示
- **マスターデータ管理**: 支払い先・費用カテゴリの管理

### 🖥️ クロスプラットフォーム対応
- Windows
- macOS  
- Linux
- 将来的にiOS/Android対応可能

### 🎨 モダンなUI/UX
- Material Design採用
- レスポンシブデザイン
- 直感的な操作性
- ダークモード対応（今後実装予定）

## セットアップ

### 必要な環境
- Flutter SDK 3.10.0以上
- Dart SDK 3.0.0以上

### インストール手順

1. **リポジトリをクローン**
   ```bash
   git clone <repository-url>
   cd billing_manager_flutter
   ```

2. **依存関係をインストール**
   ```bash
   flutter pub get
   ```

3. **アプリケーションを実行**
   ```bash
   flutter run
   ```

## プロジェクト構造

```
lib/
├── main.dart                 # エントリーポイント
├── models/                   # データモデル
│   ├── payment_model.dart
│   └── expense_model.dart
├── services/                 # ビジネスロジック
│   ├── database_service.dart
│   └── csv_import_service.dart
├── screens/                  # 画面
│   ├── home_screen.dart
│   ├── payments_screen.dart
│   ├── expenses_screen.dart
│   ├── master_data_screen.dart
│   ├── project_filter_screen.dart
│   └── monitoring_screen.dart
└── widgets/                  # 共通ウィジェット
    ├── payment_form_dialog.dart
    ├── payment_list_item.dart
    ├── expense_form_dialog.dart
    ├── expense_list_item.dart
    ├── search_filter_bar.dart
    └── expense_search_filter_bar.dart
```

## 使い方

### 1. 支払い管理
- 「支払い管理」タブで支払い情報の登録・編集
- ステータス（未処理/処理中/完了/保留）による管理
- 金額、支払い先、プロジェクトによる検索・フィルタ

### 2. 費用管理  
- 「費用管理」タブで経費情報の登録・編集
- カテゴリ別の費用分類
- 承認ワークフロー（未承認/承認済み/却下）

### 3. データインポート
- メニューから「データインポート」を選択
- 支払いデータまたは費用データのCSVファイルを選択
- エラー報告機能付きの安全なインポート

### 4. 検索・フィルタリング
- 各画面の検索バーでテキスト検索
- フィルターアイコンで詳細条件設定
- 日付範囲、ステータス、カテゴリによる絞り込み

## CSVフォーマット

### 支払いデータCSV
```csv
おもて情報.件名,明細情報.明細項目,おもて情報.請求元,おもて情報.支払先コード,明細情報.金額,おもて情報.自社支払期限,状態
番組制作費,ラジオ番組A,制作会社A,P001,100000,2024-01-31,未処理
```

### 費用データCSV
```csv
日付,プロジェクト名,カテゴリ,説明,金額,支払方法,承認状況
2024-01-15,プロジェクトA,交通費,出張費,5000,現金,未承認
```

## 技術仕様

### 使用技術
- **Flutter**: UI フレームワーク
- **SQLite**: ローカルデータベース
- **Provider**: 状態管理
- **Material Design**: デザインシステム

### 主要パッケージ
- `sqflite`: SQLiteデータベース操作
- `provider`: 状態管理
- `file_picker`: ファイル選択
- `csv`: CSV処理
- `intl`: 国際化・日付フォーマット

## PyQt5版からの移行

### 移行された機能
✅ 基本的なCRUD操作  
✅ CSVインポート機能  
✅ 検索・フィルター機能  
✅ データベース操作  
✅ 統計表示  

### 今後実装予定
⏳ ファイル監視機能  
⏳ 詳細レポート機能  
⏳ データエクスポート機能  
⏳ マスターデータ完全実装  

## 開発・コントリビューション

### 開発環境セットアップ
```bash
# 開発用依存関係のインストール
flutter pub get

# コード品質チェック
flutter analyze

# テスト実行  
flutter test

# ビルド
flutter build windows
flutter build macos
flutter build linux
```

### コードスタイル
- Dart公式コーディング規約に従う
- Effective Dart ガイドラインを適用

## ライセンス

このプロジェクトは元のPyQt5版と同じライセンスを適用します。

## サポート・問い合わせ

問題や提案がある場合は、Issueを作成してください。