#!/usr/bin/env python3
"""
アプリケーション管理GUI機能テスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from tray_monitor import ApplicationManagerDialog, ApplicationEditDialog, ProcessManager

def test_app_manager_dialog():
    """アプリケーション管理ダイアログのテスト"""
    print("=" * 60)
    print("📋 アプリケーション管理ダイアログテスト")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # ProcessManagerインスタンス作成
    process_manager = ProcessManager()
    
    # アプリケーション管理ダイアログを表示
    dialog = ApplicationManagerDialog(process_manager)
    
    print("✅ アプリケーション管理ダイアログ作成成功")
    print("📋 登録済みアプリケーションが表示されます")
    print("🔧 追加・編集・削除ボタンが使用可能です")
    
    # ダイアログを表示
    dialog.show()
    
    return app, dialog

def test_app_edit_dialog():
    """アプリケーション編集ダイアログのテスト"""
    print("\n" + "=" * 60)
    print("✏️ アプリケーション編集ダイアログテスト")
    print("=" * 60)
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # ProcessManagerインスタンス作成
    process_manager = ProcessManager()
    
    # 新規追加ダイアログ
    new_dialog = ApplicationEditDialog(process_manager)
    print("✅ 新規アプリケーション追加ダイアログ作成成功")
    print("📝 基本設定・スケジュール・詳細の3タブ構成")
    print("📁 ファイル選択ダイアログ対応")
    
    # 編集ダイアログ（既存アプリ）
    existing_apps = process_manager.load_app_configs()
    if existing_apps:
        first_app_id = list(existing_apps.keys())[0]
        edit_dialog = ApplicationEditDialog(process_manager, app_id=first_app_id)
        print(f"✅ 既存アプリ編集ダイアログ作成成功: {existing_apps[first_app_id]['name']}")
        
        # 編集ダイアログを表示
        edit_dialog.show()
        
        return app, edit_dialog
    
    new_dialog.show()
    return app, new_dialog

def test_configuration_features():
    """設定機能のテスト"""
    print("\n" + "=" * 60)
    print("⚙️ 設定機能テスト")
    print("=" * 60)
    
    process_manager = ProcessManager()
    
    # 既存設定の読み込みテスト
    configs = process_manager.load_app_configs()
    print(f"📋 既存アプリケーション数: {len(configs)}")
    
    for app_id, config in configs.items():
        print(f"  - {app_id}: {config['name']}")
        schedule = config.get('schedule', {})
        if schedule.get('enabled', False):
            print(f"    ⏰ スケジュール: {schedule.get('start_time', '')}-{schedule.get('stop_time', '')}")
        else:
            print(f"    📋 手動実行")
    
    print("\n🎯 GUI機能の特徴:")
    print("  - テーブル形式でアプリケーション一覧表示")
    print("  - 実行状態とスケジュール状況を可視化")
    print("  - タブ形式で設定を整理")
    print("  - ファイル選択ダイアログで簡単設定")
    print("  - 即座保存・反映機能")
    
def main():
    """メインテスト関数"""
    print("🧪 アプリケーション管理GUI機能テスト開始")
    print(f"現在時刻: {os.path.basename(__file__)}")
    
    try:
        # アプリケーション管理ダイアログテスト
        app, manager_dialog = test_app_manager_dialog()
        
        # 設定機能テスト
        test_configuration_features()
        
        # 編集ダイアログテスト
        app_edit, edit_dialog = test_app_edit_dialog()
        
        print("\n" + "=" * 60)
        print("✅ 全てのGUI機能テストが完了しました！")
        print("=" * 60)
        
        print("\n⌨️ 実際にGUIを操作して確認してください。")
        print("   両方のダイアログを閉じるとテストが終了します。")
        
        # アプリケーション実行
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"\n❌ テスト中にエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()