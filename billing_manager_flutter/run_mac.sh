#!/bin/bash

# ラジオ局支払い・費用管理システム (Flutter版) - macOS起動スクリプト

echo "=================================================="
echo "  ラジオ局支払い・費用管理システム (Flutter版)"
echo "=================================================="
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Flutter環境のチェック
check_flutter() {
    if ! command -v flutter &> /dev/null; then
        echo "❌ Flutterが見つかりません。"
        echo ""
        echo "Flutterをインストールするには："
        echo "1. https://flutter.dev/docs/get-started/install/macos にアクセス"
        echo "2. Flutter SDKをダウンロードして展開"
        echo "3. PATHに追加: export PATH=\"\$PATH:[PATH_TO_FLUTTER_GIT_DIRECTORY]/flutter/bin\""
        echo ""
        read -p "Enterキーを押して終了..."
        exit 1
    fi
}

# 依存関係のチェック
check_dependencies() {
    echo "📦 依存関係をチェック中..."
    
    if [ ! -f "pubspec.yaml" ]; then
        echo "❌ pubspec.yamlが見つかりません。"
        echo "正しいプロジェクトディレクトリで実行してください。"
        exit 1
    fi
    
    # pub get実行
    echo "📥 パッケージをインストール中..."
    flutter pub get
    
    if [ $? -eq 0 ]; then
        echo "✅ 依存関係のインストール完了"
    else
        echo "❌ 依存関係のインストールに失敗しました"
        exit 1
    fi
}

# アプリケーション起動
start_app() {
    echo ""
    echo "🚀 アプリケーションを起動中..."
    echo "   ※初回起動は時間がかかる場合があります"
    echo ""
    
    # macOSアプリとして起動
    flutter run -d macos
}

# メイン処理
main() {
    echo "🔍 Flutter環境をチェック中..."
    check_flutter
    echo "✅ Flutter環境を確認しました"
    
    echo ""
    check_dependencies
    
    echo ""
    echo "🎯 macOSアプリケーションとして起動します..."
    echo ""
    
    start_app
}

# エラーハンドリング
handle_error() {
    echo ""
    echo "❌ エラーが発生しました"
    echo "以下を確認してください："
    echo "- Flutterが正しくインストールされている"
    echo "- macOS開発環境が設定されている (Xcode)"
    echo "- ネットワーク接続が正常"
    echo ""
    echo "問題が解決しない場合は、以下のコマンドを実行してください："
    echo "flutter doctor"
    echo ""
    read -p "Enterキーを押して終了..."
    exit 1
}

# エラートラップ設定
trap handle_error ERR

# スクリプト実行
main

echo ""
echo "✅ アプリケーションが終了しました"
echo "またのご利用をお待ちしています！"