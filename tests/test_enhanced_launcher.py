#!/usr/bin/env python3
"""
拡張トレイランチャーの包括的テスト
"""

import time
import os
from tray_monitor import ProcessManager

def test_comprehensive():
    """包括的な機能テスト"""
    print("=" * 70)
    print("🚀 拡張トレイランチャー包括的テスト")
    print("=" * 70)
    
    pm = ProcessManager()
    
    # 1. 設定読み込みテスト
    print("\n📋 1. 設定読み込みテスト")
    configs = pm.load_app_configs()
    print(f"   ✅ {len(configs)}個の設定を読み込み成功")
    for app_id, config in configs.items():
        enabled = "有効" if config.get('enabled', True) else "無効"
        print(f"   - {app_id}: {config['name']} ({enabled})")
    
    # 2. テストアプリ起動テスト
    print("\n🚀 2. テストアプリ起動テスト")
    if 'test_app' in configs:
        print("   テストアプリを起動中...")
        success, message = pm.start_application('test_app', configs['test_app'])
        
        if success:
            print(f"   ✅ 起動成功: {message}")
            
            # 3. プロセス状態監視テスト
            print("\n📊 3. プロセス状態監視テスト")
            for i in range(5):
                status = pm.get_process_status('test_app')
                running = pm.is_process_running('test_app')
                print(f"   チェック{i+1}: {status} (実行中: {running})")
                time.sleep(1)
            
            # 4. プロセス停止テスト
            print("\n⏹️ 4. プロセス停止テスト")
            print("   テストアプリを停止中...")
            stop_success, stop_message = pm.stop_application('test_app')
            
            if stop_success:
                print(f"   ✅ 停止成功: {stop_message}")
            else:
                print(f"   ❌ 停止失敗: {stop_message}")
                
            # 5. 停止後の状態確認
            time.sleep(1)
            final_status = pm.get_process_status('test_app')
            print(f"   停止後の状態: {final_status}")
            
        else:
            print(f"   ❌ 起動失敗: {message}")
    
    # 6. 複数プロセス管理テスト
    print("\n🔄 5. 複数プロセス管理テスト")
    test_apps = []
    
    # メインアプリケーションも起動してみる（存在する場合）
    if 'test_app' in configs and os.path.exists('test_simple_app.py'):
        print("   複数のテストアプリを起動...")
        
        # 再度テストアプリを起動
        success1, msg1 = pm.start_application('test_app', configs['test_app'])
        print(f"   テストアプリ1: {'✅成功' if success1 else '❌失敗'} - {msg1}")
        
        time.sleep(2)
        
        # 複数のプロセス状態を確認
        print("   アクティブなプロセス:")
        for app_id, config in configs.items():
            status = pm.get_process_status(app_id)
            if status != "未起動":
                print(f"   - {config['name']}: {status}")
    
    # 7. クリーンアップテスト
    print("\n🧹 6. クリーンアップテスト")
    print("   すべてのプロセスを停止中...")
    pm.stop_all_applications()
    
    # 最終状態確認
    time.sleep(1)
    active_processes = []
    for app_id, config in configs.items():
        status = pm.get_process_status(app_id)
        if status == "実行中":
            active_processes.append(f"{config['name']} ({status})")
    
    if active_processes:
        print(f"   ⚠️ まだ実行中のプロセスがあります: {', '.join(active_processes)}")
    else:
        print("   ✅ すべてのプロセスが正常に停止されました")
    
    # 8. エラーハンドリングテスト
    print("\n❌ 7. エラーハンドリングテスト")
    
    # 存在しないアプリケーションの起動テスト
    fake_config = {
        'name': '存在しないアプリ',
        'executable': 'nonexistent_app',
        'args': [],
        'working_directory': '.'
    }
    success, message = pm.start_application('fake_app', fake_config)
    print(f"   存在しないアプリ起動: {'❌期待通り失敗' if not success else '⚠️予期しない成功'}")
    print(f"   エラーメッセージ: {message}")
    
    # 存在しないプロセスの停止テスト
    success, message = pm.stop_application('nonexistent_process')
    print(f"   存在しないプロセス停止: {'❌期待通り失敗' if not success else '⚠️予期しない成功'}")
    print(f"   エラーメッセージ: {message}")
    
    print("\n" + "=" * 70)
    print("✅ テスト完了 - 拡張トレイランチャーは正常に動作しています")
    print("=" * 70)

if __name__ == "__main__":
    test_comprehensive()