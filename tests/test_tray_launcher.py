#!/usr/bin/env python3
"""
拡張トレイアプリケーションの機能テスト
"""

import sys
import time
from tray_monitor import ProcessManager

def test_process_manager():
    """プロセスマネージャーの基本機能をテスト"""
    print("=" * 60)
    print("プロセスマネージャー機能テスト開始")
    print("=" * 60)
    
    pm = ProcessManager()
    
    # 設定読み込みテスト
    print("\n📋 設定読み込みテスト:")
    configs = pm.load_app_configs()
    print(f"  読み込み済み設定: {len(configs)}個")
    for app_id, config in configs.items():
        print(f"    {app_id}: {config['name']} ({config['executable']})")
    
    # 電卓起動テスト（Windows/macOSの場合のみ）
    print("\n🧮 電卓起動テスト:")
    if 'calculator' in configs:
        print("  電卓起動を試行中...")
        success, message = pm.start_application('calculator', configs['calculator'])
        print(f"  結果: {'✅成功' if success else '❌失敗'} - {message}")
        
        if success:
            time.sleep(2)
            
            # ステータス確認
            status = pm.get_process_status('calculator')
            print(f"  ステータス: {status}")
            
            # 停止テスト
            print("  停止を試行中...")
            stop_success, stop_message = pm.stop_application('calculator')
            print(f"  停止結果: {'✅成功' if stop_success else '❌失敗'} - {stop_message}")
    
    # メモ帳テスト（Windowsの場合のみ）
    print("\n📝 メモ帳テスト:")
    if 'notepad' in configs:
        import platform
        if platform.system() == "Windows":
            print("  メモ帳起動を試行中...")
            success, message = pm.start_application('notepad', configs['notepad'])
            print(f"  結果: {'✅成功' if success else '❌失敗'} - {message}")
            
            if success:
                time.sleep(2)
                status = pm.get_process_status('notepad')
                print(f"  ステータス: {status}")
                
                # ユーザーに手動停止を促す
                input("  メモ帳が起動しました。手動で閉じてからEnterを押してください...")
        else:
            print("  Windowsでないためメモ帳テストをスキップ")
    
    # プロセス状態確認
    print("\n📊 最終状態:")
    for app_id in configs.keys():
        status = pm.get_process_status(app_id)
        print(f"  {app_id}: {status}")
    
    # クリーンアップ
    print("\n🧹 クリーンアップ:")
    pm.stop_all_applications()
    print("  すべてのプロセスを停止しました")
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    test_process_manager()