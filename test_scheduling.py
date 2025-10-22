#!/usr/bin/env python3
"""
スケジューリング機能テストスクリプト
"""

import sys
import os
import time
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(__file__))

from tray_monitor import ApplicationScheduler, ProcessManager

def test_scheduler_basic():
    """基本的なスケジューラーテスト"""
    print("=" * 60)
    print("🕒 スケジューラー基本機能テスト")
    print("=" * 60)
    
    # スケジューラーとプロセスマネージャーを作成
    scheduler = ApplicationScheduler()
    process_manager = ProcessManager()
    
    # テスト用のアプリケーション設定
    current_time = datetime.now()
    start_time = (current_time + timedelta(minutes=1)).strftime("%H:%M")
    stop_time = (current_time + timedelta(minutes=2)).strftime("%H:%M")
    
    test_app_config = {
        'name': 'テストアプリケーション',
        'executable': 'python3',
        'args': ['tests/test_simple_app.py'],
        'working_directory': '.',
        'enabled': True,
        'auto_restart': False,
        'schedule': {
            'enabled': True,
            'start_time': start_time,
            'stop_time': stop_time,
            'days': [current_time.strftime('%A')],  # 今日の曜日
            'startup_delay': 0,
            'auto_restart_interval': 0
        }
    }
    
    print(f"📅 テスト設定:")
    print(f"  今日の曜日: {current_time.strftime('%A')}")
    print(f"  起動予定時刻: {start_time}")
    print(f"  停止予定時刻: {stop_time}")
    
    # アプリケーションをスケジューラーに追加
    scheduler.add_scheduled_app('test_app', test_app_config, process_manager)
    
    # スケジュール情報を確認
    schedule_info = scheduler.get_schedule_info('test_app')
    if schedule_info:
        print(f"\n🔍 スケジュール情報:")
        print(f"  有効: {schedule_info['enabled']}")
        if schedule_info['next_start']:
            print(f"  次回起動: {schedule_info['next_start'].strftime('%Y-%m-%d %H:%M:%S')}")
        if schedule_info['next_stop']:
            print(f"  次回停止: {schedule_info['next_stop'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n✅ スケジューラー基本機能テスト完了")
    return scheduler, process_manager

def test_schedule_calculation():
    """スケジュール計算テスト"""
    print("\n" + "=" * 60)
    print("📊 スケジュール計算テスト")
    print("=" * 60)
    
    scheduler = ApplicationScheduler()
    process_manager = ProcessManager()
    
    # 複数の曜日設定でテスト
    test_configs = [
        {
            'name': '平日アプリ',
            'schedule': {
                'enabled': True,
                'start_time': '09:00',
                'stop_time': '17:00',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'startup_delay': 30,
                'auto_restart_interval': 0
            }
        },
        {
            'name': '週末アプリ',
            'schedule': {
                'enabled': True,
                'start_time': '10:00',
                'stop_time': '15:00',
                'days': ['Saturday', 'Sunday'],
                'startup_delay': 0,
                'auto_restart_interval': 6
            }
        },
        {
            'name': '毎日アプリ',
            'schedule': {
                'enabled': True,
                'start_time': '08:00',
                'stop_time': '20:00',
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                'startup_delay': 0,
                'auto_restart_interval': 12
            }
        }
    ]
    
    for i, config in enumerate(test_configs):
        app_id = f'test_app_{i}'
        full_config = {
            'name': config['name'],
            'executable': 'echo',
            'args': ['test'],
            'working_directory': '.',
            'enabled': True,
            'auto_restart': False,
            'schedule': config['schedule']
        }
        
        scheduler.add_scheduled_app(app_id, full_config, process_manager)
        schedule_info = scheduler.get_schedule_info(app_id)
        
        print(f"\n📱 {config['name']}:")
        print(f"  実行曜日: {', '.join(config['schedule']['days'])}")
        print(f"  実行時間: {config['schedule']['start_time']} - {config['schedule']['stop_time']}")
        
        if schedule_info and schedule_info['next_start']:
            next_start = schedule_info['next_start']
            print(f"  次回起動: {next_start.strftime('%A %m/%d %H:%M')}")
        
        if schedule_info and schedule_info['next_stop']:
            next_stop = schedule_info['next_stop']
            print(f"  次回停止: {next_stop.strftime('%A %m/%d %H:%M')}")
    
    print("\n✅ スケジュール計算テスト完了")
    return scheduler

def test_config_loading():
    """設定ファイル読み込みテスト"""
    print("\n" + "=" * 60)
    print("📂 設定ファイル読み込みテスト")
    print("=" * 60)
    
    process_manager = ProcessManager()
    scheduler = ApplicationScheduler()
    
    # 実際の設定ファイルを読み込み
    app_configs = process_manager.load_app_configs()
    
    print(f"📋 読み込まれたアプリケーション: {len(app_configs)}個")
    
    scheduled_count = 0
    for app_id, app_config in app_configs.items():
        schedule_config = app_config.get('schedule', {})
        if schedule_config.get('enabled', False):
            scheduled_count += 1
            scheduler.add_scheduled_app(app_id, app_config, process_manager)
            
            print(f"\n📅 {app_config['name']} (スケジュール有効):")
            print(f"  起動時刻: {schedule_config.get('start_time', 'なし')}")
            print(f"  停止時刻: {schedule_config.get('stop_time', 'なし')}")
            print(f"  実行曜日: {', '.join(schedule_config.get('days', []))}")
            
            schedule_info = scheduler.get_schedule_info(app_id)
            if schedule_info and schedule_info['next_start']:
                print(f"  次回起動: {schedule_info['next_start'].strftime('%A %m/%d %H:%M')}")
    
    print(f"\n📊 スケジュール有効なアプリケーション: {scheduled_count}個")
    print("\n✅ 設定ファイル読み込みテスト完了")

def main():
    """メインテスト関数"""
    print("🧪 スケジューリング機能包括テスト開始")
    print(f"現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 基本機能テスト
        scheduler, process_manager = test_scheduler_basic()
        
        # スケジュール計算テスト
        test_scheduler = test_schedule_calculation()
        
        # 設定ファイル読み込みテスト
        test_config_loading()
        
        print("\n" + "=" * 60)
        print("✅ 全てのテストが完了しました！")
        print("=" * 60)
        
        print("\n🎯 スケジューリング機能の特徴:")
        print("  - cron風の時間指定対応")
        print("  - 曜日ベースのスケジューリング")
        print("  - 自動起動・停止機能")
        print("  - 定期再起動機能")
        print("  - Windows/macOS/Linux対応")
        
    except Exception as e:
        print(f"\n❌ テスト中にエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()