#!/usr/bin/env python3
"""
ファイル監視スクリプト - dataフォルダのCSVファイル追加を監視して自動でアプリを起動
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import signal
import psutil

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("エラー: watchdogライブラリがインストールされていません")
    print("以下のコマンドでインストールしてください: pip install watchdog")
    sys.exit(1)

from utils import log_message


class CSVFileHandler(FileSystemEventHandler):
    """CSVファイルの変更を監視するハンドラー"""
    
    def __init__(self, app_path, data_folder):
        self.app_path = app_path
        self.data_folder = data_folder
        self.last_processed = {}
        self.processing_lock = threading.Lock()
        
    def on_created(self, event):
        """新しいファイルが作成されたときの処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.csv':
            log_message(f"新しいCSVファイルを検出: {file_path.name}")
            self._process_csv_file(file_path)
    
    def on_modified(self, event):
        """ファイルが更新されたときの処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.csv':
            # ファイルの更新完了を待つ（書き込み中でない状態まで待機）
            if self._wait_for_file_completion(file_path):
                log_message(f"CSVファイルの更新を検出: {file_path.name}")
                self._process_csv_file(file_path)
    
    def _wait_for_file_completion(self, file_path, max_wait=10):
        """ファイルの書き込み完了を待つ"""
        last_size = -1
        wait_count = 0
        
        while wait_count < max_wait:
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    # ファイルサイズが変わらなくなったら完了
                    time.sleep(0.5)  # 念のため少し待つ
                    return True
                last_size = current_size
                time.sleep(1)
                wait_count += 1
            except (OSError, FileNotFoundError):
                time.sleep(1)
                wait_count += 1
                
        return True  # タイムアウトしても処理を続行
    
    def _process_csv_file(self, file_path):
        """CSVファイルを処理する"""
        with self.processing_lock:
            # 重複処理を防ぐ
            file_key = str(file_path)
            current_time = time.time()
            
            if file_key in self.last_processed:
                if current_time - self.last_processed[file_key] < 5.0:  # 5秒以内の重複は無視
                    log_message(f"重複処理をスキップ: {file_path.name}")
                    return
            
            self.last_processed[file_key] = current_time
            
            # アプリを起動
            self._launch_app(file_path)
    
    def _launch_app(self, csv_file_path):
        """アプリを起動してCSVファイルをインポート"""
        try:
            # 既にアプリが起動中かチェック
            if self._is_app_running():
                log_message("アプリは既に実行中です。新しいインスタンスの起動をスキップします。")
                return
            
            log_message(f"アプリを起動します: {csv_file_path}")
            
            # Pythonスクリプトとして実行
            cmd = [sys.executable, self.app_path, "--import-csv", str(csv_file_path)]
            
            # プロセスを起動（デタッチモード）
            if os.name == 'nt':  # Windows
                subprocess.Popen(cmd, 
                               creationflags=subprocess.CREATE_NEW_CONSOLE,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:  # macOS/Linux
                subprocess.Popen(cmd,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               start_new_session=True)
            
            log_message(f"アプリを起動しました: {csv_file_path.name}")
            
        except Exception as e:
            log_message(f"アプリ起動エラー: {e}")
    
    def _is_app_running(self):
        """アプリが既に実行中かチェック"""
        try:
            app_name = Path(self.app_path).stem
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if proc_info['cmdline']:
                        for cmd_part in proc_info['cmdline']:
                            if app_name in cmd_part and 'python' in str(proc_info['cmdline']):
                                # 自分自身は除外
                                if proc.pid != os.getpid():
                                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            log_message(f"プロセスチェックエラー: {e}")
        
        return False


class FileWatcher:
    """ファイル監視クラス"""
    
    def __init__(self, data_folder, app_path):
        self.data_folder = Path(data_folder)
        self.app_path = Path(app_path)
        self.observer = None
        self.running = False
        
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """監視を開始"""
        if not self.data_folder.exists():
            log_message(f"エラー: 監視フォルダが見つかりません: {self.data_folder}")
            return False
        
        if not self.app_path.exists():
            log_message(f"エラー: アプリファイルが見つかりません: {self.app_path}")
            return False
        
        try:
            self.observer = Observer()
            event_handler = CSVFileHandler(str(self.app_path), str(self.data_folder))
            self.observer.schedule(event_handler, str(self.data_folder), recursive=False)
            
            self.observer.start()
            self.running = True
            
            log_message(f"ファイル監視を開始しました: {self.data_folder}")
            log_message(f"監視対象: CSVファイル")
            log_message(f"起動アプリ: {self.app_path}")
            log_message("Ctrl+C で監視を停止します")
            
            return True
            
        except Exception as e:
            log_message(f"監視開始エラー: {e}")
            return False
    
    def stop(self):
        """監視を停止"""
        if self.observer and self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            log_message("ファイル監視を停止しました")
    
    def wait(self):
        """監視が停止されるまで待機"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        log_message(f"シグナル {signum} を受信しました")
        self.stop()


def create_pid_file(pid_file_path):
    """PIDファイルを作成"""
    try:
        with open(pid_file_path, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        log_message(f"PIDファイル作成エラー: {e}")
        return False


def remove_pid_file(pid_file_path):
    """PIDファイルを削除"""
    try:
        if os.path.exists(pid_file_path):
            os.remove(pid_file_path)
    except Exception as e:
        log_message(f"PIDファイル削除エラー: {e}")


def is_already_running(pid_file_path):
    """既に監視プロセスが実行中かチェック"""
    if not os.path.exists(pid_file_path):
        return False
    
    try:
        with open(pid_file_path, 'r') as f:
            pid = int(f.read().strip())
        
        # プロセスが存在するかチェック
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            if 'file_watcher' in ' '.join(proc.cmdline()):
                return True
        
        # PIDファイルがあるがプロセスが存在しない場合は削除
        os.remove(pid_file_path)
        return False
        
    except (ValueError, psutil.NoSuchProcess, FileNotFoundError):
        # PIDファイルが不正な場合は削除
        try:
            os.remove(pid_file_path)
        except:
            pass
        return False


def main():
    """メイン関数"""
    # 基本パスの設定
    script_dir = Path(__file__).parent
    data_folder = script_dir / "data"
    app_path = script_dir / "app.py"
    pid_file_path = script_dir / "file_watcher.pid"
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stop":
            # 監視停止
            if is_already_running(pid_file_path):
                try:
                    with open(pid_file_path, 'r') as f:
                        pid = int(f.read().strip())
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait(timeout=10)
                    log_message("ファイル監視を停止しました")
                except Exception as e:
                    log_message(f"監視停止エラー: {e}")
            else:
                log_message("監視プロセスは実行されていません")
            return
        
        elif sys.argv[1] == "--status":
            # ステータス確認
            if is_already_running(pid_file_path):
                log_message("ファイル監視は実行中です")
            else:
                log_message("ファイル監視は停止しています")
            return
    
    # 重複起動チェック
    if is_already_running(pid_file_path):
        log_message("ファイル監視は既に実行中です")
        return
    
    # PIDファイル作成
    if not create_pid_file(pid_file_path):
        log_message("PIDファイルの作成に失敗しました")
        return
    
    try:
        watcher = FileWatcher(data_folder, app_path)
        
        if watcher.start():
            # 正常に開始された場合は待機
            watcher.wait()
        
    except Exception as e:
        log_message(f"予期しないエラー: {e}")
    
    finally:
        # 終了処理
        if 'watcher' in locals():
            watcher.stop()
        remove_pid_file(pid_file_path)
        log_message("ファイル監視プロセスを終了しました")


if __name__ == "__main__":
    main()