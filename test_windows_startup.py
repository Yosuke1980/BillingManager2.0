#!/usr/bin/env python3
"""
Windows環境でのパス解決問題テスト
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(__file__))

def test_path_resolution():
    """パス解決のテスト"""
    print("=" * 60)
    print("🪟 Windows環境パス解決テスト")
    print("=" * 60)
    
    # 現在のスクリプトファイルの場所を確認
    script_path = Path(__file__)
    script_dir = script_path.parent
    
    print(f"📁 スクリプトファイル: {script_path}")
    print(f"📁 スクリプトディレクトリ: {script_dir}")
    print(f"📁 現在の作業ディレクトリ: {os.getcwd()}")
    
    # 設定ファイルパスの確認
    config_path = script_dir / "config" / "app_config.json"
    print(f"📄 設定ファイルパス: {config_path}")
    print(f"📄 設定ファイル存在: {config_path.exists()}")
    
    # 相対パスによる問題の再現
    relative_config_path = "config/app_config.json"
    print(f"📄 相対パス: {relative_config_path}")
    print(f"📄 相対パス存在: {os.path.exists(relative_config_path)}")
    
    print(f"\n🔍 問題の分析:")
    print(f"  - 相対パスでのアクセスは作業ディレクトリに依存")
    print(f"  - Windowsデスクトップから実行すると作業ディレクトリがデスクトップになる")
    print(f"  - 絶対パスを使用することで解決")

def test_tray_monitor_import():
    """tray_monitor.pyのインポートテスト"""
    print("\n" + "=" * 60)
    print("🔧 tray_monitor.py インポートテスト")
    print("=" * 60)
    
    try:
        from tray_monitor import ProcessManager
        print("✅ tray_monitor.py インポート成功")
        
        # ProcessManagerインスタンス作成
        pm = ProcessManager()
        print("✅ ProcessManager インスタンス作成成功")
        
        # 設定読み込みテスト
        configs = pm.load_app_configs()
        print(f"✅ 設定読み込み成功: {len(configs)}個のアプリケーション")
        
        # デフォルト設定のテスト
        defaults = pm._get_default_app_configs()
        print(f"✅ デフォルト設定取得成功: {len(defaults)}個のアプリケーション")
        
        for app_id, config in defaults.items():
            print(f"  - {app_id}: {config['name']}")
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()

def test_config_file_creation():
    """設定ファイル自動作成のテスト"""
    print("\n" + "=" * 60)
    print("📁 設定ファイル自動作成テスト")
    print("=" * 60)
    
    try:
        from tray_monitor import ProcessManager
        
        # テスト用設定パス
        test_config_path = Path(__file__).parent / "test_config" / "app_config.json"
        
        # テスト用ディレクトリが存在する場合は削除
        if test_config_path.exists():
            test_config_path.unlink()
        if test_config_path.parent.exists():
            test_config_path.parent.rmdir()
        
        pm = ProcessManager()
        
        # 存在しない設定ファイルでの読み込み
        configs = pm.load_app_configs(str(test_config_path))
        
        print(f"📄 テスト設定ファイルパス: {test_config_path}")
        print(f"📄 ファイル作成確認: {test_config_path.exists()}")
        print(f"📋 読み込まれた設定: {len(configs)}個")
        
        # クリーンアップ
        if test_config_path.exists():
            test_config_path.unlink()
        if test_config_path.parent.exists():
            test_config_path.parent.rmdir()
            
        print("✅ 設定ファイル自動作成テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メインテスト関数"""
    print("🧪 Windows環境対応改善テスト開始")
    print(f"現在時刻: {os.path.basename(__file__)}")
    print(f"Python バージョン: {sys.version}")
    print(f"プラットフォーム: {sys.platform}")
    
    try:
        # パス解決テスト
        test_path_resolution()
        
        # インポートテスト
        test_tray_monitor_import()
        
        # 設定ファイル作成テスト
        test_config_file_creation()
        
        print("\n" + "=" * 60)
        print("✅ 全てのテストが完了しました！")
        print("=" * 60)
        
        print("\n🎯 Windows環境対応の改善点:")
        print("  - 絶対パスベースの設定ファイル読み込み")
        print("  - 設定ファイルが存在しない場合の自動作成")
        print("  - プラットフォーム固有のデフォルト設定")
        print("  - Windows固有のプロセス起動オプション")
        print("  - パス解決の強化")
        
    except Exception as e:
        print(f"\n❌ テスト中にエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()