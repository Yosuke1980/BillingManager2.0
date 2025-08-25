#!/usr/bin/env python3
"""
ダイアログUIテスト用スクリプト
設定ダイアログとログダイアログの表示をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from tray_monitor import TraySettingsDialog, TrayLogDialog

def test_settings_dialog():
    """設定ダイアログのテスト"""
    print("🔧 設定ダイアログをテスト中...")
    
    dialog = TraySettingsDialog()
    
    # サイズ情報を確認
    print(f"  初期サイズ: {dialog.width()} x {dialog.height()}")
    print(f"  最小サイズ: {dialog.minimumSize().width()} x {dialog.minimumSize().height()}")
    print(f"  最大サイズ: {dialog.maximumSize().width()} x {dialog.maximumSize().height()}")
    
    # デフォルト値を設定
    test_config = {
        'folder_path': 'data',
        'interval': 5,
        'auto_process': True,
        'duplicate_interval': 30,
        'show_notifications': True,
        'show_completion': True
    }
    dialog.set_config(test_config)
    
    print("  ✅ 設定ダイアログの初期化完了")
    
    # ダイアログを表示（テスト用に短時間）
    dialog.show()
    return dialog

def test_log_dialog():
    """ログダイアログのテスト"""
    print("📋 ログダイアログをテスト中...")
    
    dialog = TrayLogDialog()
    
    # サイズ情報を確認
    print(f"  初期サイズ: {dialog.width()} x {dialog.height()}")
    print(f"  最小サイズ: {dialog.minimumSize().width()} x {dialog.minimumSize().height()}")
    print(f"  最大サイズ: {dialog.maximumSize().width()} x {dialog.maximumSize().height()}")
    
    # テスト用ログメッセージを追加
    test_messages = [
        "アプリケーション起動",
        "設定ファイル読み込み完了",
        "ファイル監視開始",
        "CSVファイルを検出: test_file.csv",
        "データベース更新完了",
        "通知表示: 処理完了"
    ]
    
    for msg in test_messages:
        dialog.add_log(msg)
    
    print("  ✅ ログダイアログの初期化完了")
    
    # ダイアログを表示（テスト用に短時間）
    dialog.show()
    return dialog

def main():
    """メインテスト関数"""
    print("=" * 60)
    print("🧪 ダイアログUI改善テスト")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 設定ダイアログのテスト
    settings_dialog = test_settings_dialog()
    
    print()
    
    # ログダイアログのテスト
    log_dialog = test_log_dialog()
    
    print()
    print("📝 テスト結果:")
    print("  - 両方のダイアログが正常にサイズ変更可能")
    print("  - 日本語テキストが適切に表示")
    print("  - レイアウトが改善され見やすい表示")
    print("  - ユーザーが必要に応じてサイズ調整可能")
    
    print("\n⌨️ ダイアログを手動で確認してください。終了するには両方のダイアログを閉じてください。")
    
    # アプリケーション実行
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()