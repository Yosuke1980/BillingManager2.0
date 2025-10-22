#!/usr/bin/env python3
"""
Windows環境でのtray_monitor.py起動問題診断スクリプト
"""

import sys
import os
import json
import platform
from pathlib import Path

def print_header(title):
    """ヘッダーを表示"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def check_python_environment():
    """Python環境の確認"""
    print_header("Python環境確認")
    
    print(f"Python バージョン: {sys.version}")
    print(f"Python 実行パス: {sys.executable}")
    print(f"プラットフォーム: {platform.system()} {platform.release()}")
    print(f"アーキテクチャ: {platform.machine()}")
    
    # 現在のディレクトリ
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent
    print(f"現在のディレクトリ: {current_dir}")
    print(f"スクリプトディレクトリ: {script_dir}")
    
    return True

def check_dependencies():
    """依存関係の確認"""
    print_header("依存関係確認")
    
    dependencies = [
        ('PyQt5', 'PyQt5.QtWidgets'),
        ('PyQt5.QtCore', 'PyQt5.QtCore'),
        ('PyQt5.QtGui', 'PyQt5.QtGui'),
        ('psutil', 'psutil'),
        ('watchdog', 'watchdog'),
        ('pathlib', 'pathlib')
    ]
    
    missing_deps = []
    
    for dep_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {dep_name}: インストール済み")
        except ImportError as e:
            print(f"❌ {dep_name}: 未インストール - {e}")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n⚠️  不足している依存関係: {', '.join(missing_deps)}")
        print("以下のコマンドでインストールしてください:")
        for dep in missing_deps:
            if dep == 'PyQt5':
                print(f"  pip install PyQt5")
            elif dep == 'watchdog':
                print(f"  pip install watchdog")
            elif dep == 'psutil':
                print(f"  pip install psutil")
        return False
    
    return True

def check_project_files():
    """プロジェクトファイルの確認"""
    print_header("プロジェクトファイル確認")
    
    required_files = [
        'tray_monitor.py',
        'file_watcher_gui.py', 
        'utils.py',
        'config/app_config.json'
    ]
    
    script_dir = Path(__file__).parent
    missing_files = []
    
    for file_path in required_files:
        full_path = script_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}: 存在")
            # ファイルサイズも表示
            size = full_path.stat().st_size
            print(f"   サイズ: {size} bytes")
        else:
            print(f"❌ {file_path}: 不存在")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  不足しているファイル: {', '.join(missing_files)}")
        return False
    
    return True

def check_system_tray():
    """システムトレイ利用可能性の確認"""
    print_header("システムトレイ確認")
    
    try:
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
        from PyQt5.QtGui import QIcon
        
        # QApplicationを作成（必要）
        app = QApplication(sys.argv)
        
        # システムトレイが利用可能か確認
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("✅ システムトレイ: 利用可能")
            
            # 簡単なテストアイコンを作成
            try:
                icon = QIcon()  # 空のアイコン
                tray = QSystemTrayIcon(icon)
                print("✅ システムトレイアイコン: 作成可能")
                
                # アイコン表示テスト
                try:
                    tray.show()
                    print("✅ システムトレイアイコン表示: 成功")
                    tray.hide()  # テスト後は非表示
                except Exception as e:
                    print(f"⚠️  アイコン表示テストエラー: {e}")
                
                return True
            except Exception as e:
                print(f"❌ システムトレイアイコン作成エラー: {e}")
                return False
        else:
            print("❌ システムトレイ: 利用不可能")
            print("   システムトレイ機能が有効になっていない可能性があります")
            print("\n🔧 Windows環境での対処法:")
            print("   1. タスクバー右クリック → 'タスクバーの設定'")
            print("   2. '通知領域' → 'システムアイコンのオン/オフの切り替え'")
            print("   3. '通知' をオンにする")
            print("   4. または --gui オプションで直接起動")
            return False
            
    except ImportError as e:
        print(f"❌ PyQt5インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ システムトレイテストエラー: {e}")
        return False

def check_config_file():
    """設定ファイルの確認"""
    print_header("設定ファイル確認")
    
    script_dir = Path(__file__).parent
    config_path = script_dir / "config" / "app_config.json"
    
    try:
        if config_path.exists():
            print(f"✅ 設定ファイル: {config_path}")
            
            # JSON形式の確認
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("✅ JSON形式: 正常")
            
            # 主要キーの確認
            if 'tray_applications' in config:
                apps = config['tray_applications']
                print(f"✅ アプリケーション設定: {len(apps)}個")
                
                for app_id, app_config in apps.items():
                    name = app_config.get('name', '不明')
                    enabled = app_config.get('enabled', False)
                    status = "有効" if enabled else "無効"
                    print(f"  - {app_id}: {name} ({status})")
            else:
                print("⚠️  'tray_applications'キーが見つかりません")
                
            return True
        else:
            print(f"❌ 設定ファイルが見つかりません: {config_path}")
            print("   初回実行時に自動作成されるはずです")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析エラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 設定ファイル確認エラー: {e}")
        return False

def test_import_modules():
    """プロジェクト内モジュールのインポートテスト"""
    print_header("プロジェクトモジュールインポートテスト")
    
    script_dir = Path(__file__).parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    modules = [
        ('file_watcher_gui', 'FileWatcherManager'),
        ('utils', 'log_message'),
        ('tray_monitor', 'ProcessManager'),
        ('tray_monitor', 'ApplicationScheduler'),
        ('tray_monitor', 'FileMonitorTray')
    ]
    
    import_errors = []
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name}: インポート成功")
            else:
                print(f"❌ {module_name}.{class_name}: クラスが見つかりません")
                import_errors.append(f"{module_name}.{class_name}")
        except ImportError as e:
            print(f"❌ {module_name}: インポートエラー - {e}")
            import_errors.append(module_name)
        except Exception as e:
            print(f"❌ {module_name}: 予期しないエラー - {e}")
            import_errors.append(module_name)
    
    if import_errors:
        print(f"\n⚠️  インポートエラーがあるモジュール: {', '.join(import_errors)}")
        return False
    
    return True

def run_minimal_startup_test():
    """最小限の起動テスト"""
    print_header("最小限起動テスト")
    
    try:
        script_dir = Path(__file__).parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
        from PyQt5.QtGui import QIcon
        
        print("✅ PyQt5インポート: 成功")
        
        # QApplicationを作成
        app = QApplication(sys.argv)
        print("✅ QApplication作成: 成功")
        
        # システムトレイアイコンを作成
        icon = QIcon()
        tray = QSystemTrayIcon(icon)
        print("✅ QSystemTrayIcon作成: 成功")
        
        # ProcessManagerのテスト
        try:
            from tray_monitor import ProcessManager
            pm = ProcessManager()
            print("✅ ProcessManager作成: 成功")
        except Exception as e:
            print(f"❌ ProcessManager作成エラー: {e}")
            return False
        
        print("✅ 最小限の起動テスト: 成功")
        return True
        
    except Exception as e:
        print(f"❌ 最小限の起動テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン診断関数"""
    print("🧪 Windows環境 tray_monitor.py 起動問題診断開始")
    print(f"診断日時: {os.path.basename(__file__)}")
    
    results = []
    
    # 各チェックを実行
    results.append(("Python環境", check_python_environment()))
    results.append(("依存関係", check_dependencies()))
    results.append(("プロジェクトファイル", check_project_files()))
    results.append(("システムトレイ", check_system_tray()))
    results.append(("設定ファイル", check_config_file()))
    results.append(("モジュールインポート", test_import_modules()))
    results.append(("最小限起動テスト", run_minimal_startup_test()))
    
    # 結果サマリー
    print_header("診断結果サマリー")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 正常" if result else "❌ 問題あり"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 結果: {passed}個成功, {failed}個失敗")
    
    if failed == 0:
        print("🎉 全てのチェックが成功しました！tray_monitor.pyは正常に起動するはずです。")
        print("\n🚀 起動方法:")
        print("  1. トレイ常駐モード:")
        print("     python tray_monitor.py")
        print("  2. GUI直接起動:")  
        print("     python tray_monitor.py --gui")
        print("  3. アプリ管理画面:")
        print("     python tray_monitor.py --app-manager")
        print("  4. 専用GUIランチャー:")
        print("     python gui_launcher.py")
    else:
        print("⚠️  問題が検出されました。上記のエラーを修正してから再度お試しください。")
        
        # 修正のための推奨事項
        print("\n🔧 推奨される修正手順:")
        if any("依存関係" in r[0] and not r[1] for r in results):
            print("1. 不足している依存関係をインストール")
        if any("プロジェクトファイル" in r[0] and not r[1] for r in results):
            print("2. 不足しているプロジェクトファイルを配置")
        if any("システムトレイ" in r[0] and not r[1] for r in results):
            print("3. システムトレイ機能を有効化（または --gui オプション使用）")
        if any("設定ファイル" in r[0] and not r[1] for r in results):
            print("4. 設定ファイルの修正または再作成")
            
        print("\n💡 システムトレイに問題がある場合でも以下で起動可能:")
        print("   python tray_monitor.py --gui")
        print("   python gui_launcher.py")

if __name__ == "__main__":
    main()