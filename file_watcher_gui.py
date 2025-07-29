import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import psutil
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils import log_message


class CSVFileHandlerGUI(FileSystemEventHandler):
    """GUI用CSVファイルハンドラー"""
    
    def __init__(self, callback_func, config):
        self.callback_func = callback_func
        self.config = config
        self.last_processed = {}
        self.processing_lock = threading.Lock()
        
    def on_created(self, event):
        """新しいファイルが作成されたときの処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.csv':
            self.callback_func('file_detected', {
                'action': 'created',
                'file_path': str(file_path),
                'filename': file_path.name
            })
            self._process_csv_file(file_path)
    
    def on_modified(self, event):
        """ファイルが更新されたときの処理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.csv':
            if self._wait_for_file_completion(file_path):
                self.callback_func('file_detected', {
                    'action': 'modified',
                    'file_path': str(file_path),
                    'filename': file_path.name
                })
                self._process_csv_file(file_path)
    
    def _wait_for_file_completion(self, file_path, max_wait=10):
        """ファイルの書き込み完了を待つ"""
        last_size = -1
        wait_count = 0
        
        while wait_count < max_wait:
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    time.sleep(0.5)
                    return True
                last_size = current_size
                time.sleep(1)
                wait_count += 1
            except (OSError, FileNotFoundError):
                time.sleep(1)
                wait_count += 1
                
        return True
    
    def _process_csv_file(self, file_path):
        """CSVファイルを処理する"""
        with self.processing_lock:
            file_key = str(file_path)
            current_time = time.time()
            
            # 重複処理防止
            duplicate_interval = self.config.get('duplicate_interval', 5.0)
            if file_key in self.last_processed:
                if current_time - self.last_processed[file_key] < duplicate_interval:
                    self.callback_func('log', f"重複処理をスキップ: {file_path.name}")
                    return
            
            self.last_processed[file_key] = current_time
            
            # ファイル情報を取得
            try:
                file_stat = file_path.stat()
                file_size = f"{file_stat.st_size:,} bytes"
            except:
                file_size = "不明"
            
            # 自動処理が有効な場合のみアプリを起動
            if self.config.get('auto_process', True):
                success = self._launch_app(file_path)
                status = "処理完了" if success else "処理失敗"
            else:
                status = "検出のみ"
                success = True
            
            # ファイル処理履歴を通知
            self.callback_func('file_processed', {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': file_path.name,
                'size': file_size,
                'status': status
            })
    
    def _launch_app(self, csv_file_path):
        """アプリを起動してCSVファイルをインポート"""
        try:
            if self._is_app_running():
                self.callback_func('log', f"アプリが既に起動中のため、{csv_file_path.name}の処理をスキップ")
                return False
            
            app_path = Path(__file__).parent / "app.py"
            cmd = [sys.executable, str(app_path), "--import-csv", str(csv_file_path)]
            
            self.callback_func('log', f"アプリを起動: {csv_file_path.name}")
            
            # バックグラウンドでアプリを起動
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            return True
            
        except Exception as e:
            self.callback_func('log', f"アプリ起動エラー: {str(e)}")
            return False
    
    def _is_app_running(self):
        """アプリが起動中かチェック"""
        try:
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == current_pid:
                        continue
                    
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('app.py' in arg for arg in cmdline):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
        except Exception:
            return False


class FileWatcherManager(QObject):
    """GUI用ファイル監視マネージャー"""
    
    status_changed = pyqtSignal(bool, dict)  # (is_running, stats)
    file_processed = pyqtSignal(dict)  # file_info
    log_message = pyqtSignal(str)  # message
    
    def __init__(self):
        super().__init__()
        self.observer = None
        self.handler = None
        self.is_running = False
        self.config = {}
        self.stats = {
            'processed_count': 0,
            'start_time': None
        }
        
        # 定期的にステータスを更新
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.emit_status)
        self.status_timer.start(2000)  # 2秒ごと
    
    def start_monitoring(self, config):
        """監視を開始"""
        if self.is_running:
            self.log_message.emit("既に監視中です")
            return False
        
        self.config = config
        folder_path = config.get('folder_path', 'data')
        
        # フォルダの存在確認
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.log_message.emit(f"監視フォルダを作成しました: {folder_path}")
            except Exception as e:
                self.log_message.emit(f"フォルダ作成エラー: {str(e)}")
                return False
        
        try:
            # ハンドラーとオブザーバーを作成
            self.handler = CSVFileHandlerGUI(self._handle_callback, config)
            self.observer = Observer()
            self.observer.schedule(self.handler, folder_path, recursive=False)
            
            # 監視開始
            self.observer.start()
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            self.log_message.emit(f"監視を開始しました: {folder_path}")
            self.emit_status()
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"監視開始エラー: {str(e)}")
            return False
    
    def stop_monitoring(self):
        """監視を停止"""
        if not self.is_running:
            return
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.handler = None
            self.is_running = False
            
            self.log_message.emit("監視を停止しました")
            self.emit_status()
            
        except Exception as e:
            self.log_message.emit(f"監視停止エラー: {str(e)}")
    
    def _handle_callback(self, event_type, data):
        """ハンドラーからのコールバックを処理"""
        if event_type == 'log':
            self.log_message.emit(data)
        elif event_type == 'file_processed':
            self.stats['processed_count'] += 1
            self.file_processed.emit(data)
            self.log_message.emit(f"ファイルを処理しました: {data['filename']}")
        elif event_type == 'file_detected':
            self.log_message.emit(f"CSVファイルを検出: {data['filename']} ({data['action']})")
    
    def emit_status(self):
        """ステータスシグナルを発信"""
        self.status_changed.emit(self.is_running, self.stats.copy())
    
    def get_stats(self):
        """統計情報を取得"""
        stats = self.stats.copy()
        if self.is_running and stats['start_time']:
            uptime = datetime.now() - stats['start_time']
            stats['uptime'] = str(uptime).split('.')[0]  # マイクロ秒を除去
        return stats