#!/usr/bin/env python3
"""
テスト用のシンプルなアプリケーション
トレイランチャーのテスト用
"""

import time
import sys
import signal

def signal_handler(sig, frame):
    print('\nシグナルを受信しました。アプリケーションを終了します...')
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 テストアプリケーションが起動しました")
    print("PID:", sys.argv[0] if len(sys.argv) > 1 else "Unknown")
    print("10秒間動作してから自動終了します...")
    
    for i in range(10):
        print(f"⏰ 実行中... {i+1}/10")
        time.sleep(1)
    
    print("✅ テストアプリケーションを正常終了します")

if __name__ == "__main__":
    main()