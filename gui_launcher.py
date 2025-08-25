#!/usr/bin/env python3
"""
BillingManager GUI直接起動ランチャー
トレイ機能を使わずにGUI設定画面を直接起動
"""

import sys
import os
from pathlib import Path

# プロジェクトディレクトリをPythonパスに追加
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

def show_launcher_help():
    """ランチャーヘルプを表示"""
    print("""
🎯 BillingManager GUI ランチャー

📋 このスクリプトについて:
  トレイアイコンを使わずにGUI設定画面を直接起動します
  システムトレイが使えない環境でも設定変更が可能です

🚀 起動オプション:
  python gui_launcher.py [オプション]

⚙️  オプション:
  --app-manager, -a  : アプリケーション管理画面を起動
  --settings, -s     : 基本設定画面を起動（デフォルト）
  --help, -h         : このヘルプを表示

💡 使用例:
  python gui_launcher.py                    # 基本設定画面
  python gui_launcher.py --app-manager     # アプリ管理画面
  python gui_launcher.py -a                # アプリ管理画面（短縮）

🔧 必要な環境:
  • Python 3.6以上
  • PyQt5
  • プロジェクトファイル一式
    """)

def launch_app_manager():
    """アプリケーション管理画面を起動"""
    try:
        print("🚀 アプリケーション管理画面起動中...")
        
        from PyQt5.QtWidgets import QApplication
        from tray_monitor import ApplicationManagerDialog, ProcessManager
        
        # QApplication作成
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)  # ウィンドウ閉じると終了
        
        # ProcessManager作成
        process_manager = ProcessManager()
        
        # アプリケーション管理ダイアログを作成・表示
        dialog = ApplicationManagerDialog(process_manager)
        dialog.setWindowTitle("BillingManager - アプリケーション管理")
        dialog.show()
        
        print("✅ アプリケーション管理画面を表示しました")
        print("💡 ウィンドウを閉じると終了します")
        
        # アプリケーション実行
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        print("必要なモジュールをインストールしてください:")
        print("pip install PyQt5")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def launch_settings():
    """基本設定画面を起動"""
    try:
        print("🚀 基本設定画面起動中...")
        
        from PyQt5.QtWidgets import QApplication
        from tray_monitor import TraySettingsDialog
        
        # QApplication作成
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)  # ウィンドウ閉じると終了
        
        # 設定ダイアログを作成・表示
        dialog = TraySettingsDialog()
        dialog.setWindowTitle("BillingManager - 基本設定")
        dialog.show()
        
        print("✅ 基本設定画面を表示しました")
        print("💡 ウィンドウを閉じると終了します")
        
        # アプリケーション実行
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        print("必要なモジュールをインストールしてください:")
        print("pip install PyQt5")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """メイン関数"""
    print("🎯 BillingManager GUI直接ランチャー")
    
    # コマンドライン引数の解析
    if '--help' in sys.argv or '-h' in sys.argv:
        show_launcher_help()
        sys.exit(0)
    
    # 起動モードの判定
    if '--app-manager' in sys.argv or '-a' in sys.argv:
        launch_app_manager()
    elif '--settings' in sys.argv or '-s' in sys.argv:
        launch_settings()
    else:
        # デフォルトは基本設定画面
        launch_settings()

if __name__ == "__main__":
    main()