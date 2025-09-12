# ラジオ局支払い・費用管理システム Flutter版 - Windows版

## 必要な環境
- Windows 10/11
- Flutter SDK (3.10.0以上)
- Visual Studio 2019/2022 (C++開発ツール)

## インストール手順

### 1. Flutter SDKのインストール
1. https://docs.flutter.dev/get-started/install/windows からFlutter SDKをダウンロード
2. C:lutter または C:	oolslutter に展開
3. 環境変数PATHにFlutterのbinディレクトリを追加

### 2. Visual Studioの設定
1. Visual Studio Installer から「C++によるデスクトップ開発」ワークロードをインストール
2. Windows 10/11 SDKを含める

### 3. 必要な設定
```cmd
flutter config --enable-windows-desktop
flutter doctor
```

## 起動方法

### 方法1: バッチファイル実行
1. `run_windows.bat` をダブルクリック
2. 自動的にFlutterアプリが起動します

### 方法2: コマンドライン実行
```cmd
flutter run -d windows
```

## トラブルシューティング

### 文字化け問題
- Windows版では PowerShell を使用したShift_JIS変換を実装
- CSV ファイルのエンコーディングは自動判定・変換されます

### ビルドエラー
```cmd
flutter clean
flutter pub get
flutter run -d windows --verbose
```

### Visual Studio関連エラー
- Visual Studio 2019/2022 の C++ 開発ツールが必要
- Windows SDKが正しくインストールされているか確認

## 機能
- 支払い管理（個別・一括選択削除対応）
- 費用管理（個別・一括選択削除対応）
- マスター費用管理（個別・一括選択削除対応）
- 照合管理
- CSV インポート（Shift_JIS自動変換対応）
- プロジェクトフィルタ
- モニタリング機能

