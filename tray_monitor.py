#!/usr/bin/env python3
"""
システムトレイ常駐型ファイル監視アプリ
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QCheckBox, QTextEdit,
    QGroupBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont

from file_watcher_gui import FileWatcherManager


class TraySettingsDialog(QDialog):
    """トレイ用設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("監視設定")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        self.config_file = "monitoring_config.json"
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 基本設定
        basic_group = QGroupBox("基本設定")
        form_layout = QFormLayout()
        
        self.folder_edit = QLineEdit()
        form_layout.addRow("監視フォルダ:", self.folder_edit)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" 秒")
        form_layout.addRow("監視間隔:", self.interval_spin)
        
        self.auto_process_check = QCheckBox("ファイル検出時に自動処理")
        form_layout.addRow(self.auto_process_check)
        
        self.duplicate_spin = QSpinBox()
        self.duplicate_spin.setRange(1, 300)
        self.duplicate_spin.setSuffix(" 秒")
        form_layout.addRow("重複処理防止:", self.duplicate_spin)
        
        basic_group.setLayout(form_layout)
        layout.addWidget(basic_group)
        
        # 通知設定
        notify_group = QGroupBox("通知設定")
        notify_layout = QVBoxLayout()
        
        self.show_notifications = QCheckBox("ファイル検出時に通知表示")
        self.show_notifications.setChecked(True)
        notify_layout.addWidget(self.show_notifications)
        
        self.show_completion = QCheckBox("処理完了時に通知表示")
        self.show_completion.setChecked(True)
        notify_layout.addWidget(self.show_completion)
        
        notify_group.setLayout(notify_layout)
        layout.addWidget(notify_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_config(self):
        """設定を取得"""
        return {
            'folder_path': self.folder_edit.text(),
            'interval': self.interval_spin.value(),
            'auto_process': self.auto_process_check.isChecked(),
            'duplicate_interval': self.duplicate_spin.value(),
            'show_notifications': self.show_notifications.isChecked(),
            'show_completion': self.show_completion.isChecked()
        }
        
    def set_config(self, config):
        """設定を適用"""
        self.folder_edit.setText(config.get('folder_path', 'data'))
        self.interval_spin.setValue(config.get('interval', 1))
        self.auto_process_check.setChecked(config.get('auto_process', True))
        self.duplicate_spin.setValue(config.get('duplicate_interval', 5))
        self.show_notifications.setChecked(config.get('show_notifications', True))
        self.show_completion.setChecked(config.get('show_completion', True))
        
    def load_config(self):
        """設定を読み込み"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.set_config(config)
            except Exception:
                pass
                
    def save_config(self):
        """設定を保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.get_config(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


class TrayLogDialog(QDialog):
    """ログ表示ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("監視ログ")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc;")
        layout.addWidget(self.log_text)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("クリア")
        clear_btn.clicked.connect(self.log_text.clear)
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def add_log(self, message):
        """ログを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # 最新のログを表示
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)


class FileMonitorTray(QSystemTrayIcon):
    """システムトレイ常駐監視アプリ"""
    
    def __init__(self, app):
        # アイコンを作成
        icon = self.create_icon()
        super().__init__(icon, app)
        
        self.app = app
        self.file_watcher = FileWatcherManager()
        self.config = {}
        self.stats = {'processed_count': 0}
        
        # ダイアログ
        self.settings_dialog = None
        self.log_dialog = None
        
        # 右クリックメニューを作成
        self.create_context_menu()
        
        # シグナル接続
        self.activated.connect(self.on_tray_activated)
        self.file_watcher.status_changed.connect(self.on_status_changed)
        self.file_watcher.file_processed.connect(self.on_file_processed)
        self.file_watcher.log_message.connect(self.on_log_message)
        
        # 設定を読み込み
        self.load_config()
        
        # トレイアイコンを表示
        self.show()
        
        # 起動メッセージ
        self.showMessage(
            "BillingManager - ファイル監視",
            "ファイル監視アプリが起動しました",
            QSystemTrayIcon.Information,
            3000
        )
        
    def create_icon(self):
        """トレイアイコンを作成"""
        # 16x16のシンプルなアイコンを作成
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setBrush(Qt.blue)
        painter.setPen(Qt.blue)
        painter.drawEllipse(2, 2, 12, 12)
        
        # 中央に小さな四角を描画
        painter.setBrush(Qt.white)
        painter.setPen(Qt.white)
        painter.drawRect(6, 6, 4, 4)
        
        painter.end()
        
        return QIcon(pixmap)
        
    def create_context_menu(self):
        """右クリックメニューを作成"""
        menu = QMenu()
        
        # 監視開始/停止
        self.start_action = QAction("📁 監視開始", self)
        self.start_action.triggered.connect(self.start_monitoring)
        menu.addAction(self.start_action)
        
        self.stop_action = QAction("⏹️ 監視停止", self)
        self.stop_action.triggered.connect(self.stop_monitoring)
        self.stop_action.setEnabled(False)
        menu.addAction(self.stop_action)
        
        menu.addSeparator()
        
        # 設定
        settings_action = QAction("⚙️ 設定...", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # 統計表示
        self.stats_action = QAction("📊 統計: 0件処理済み", self)
        self.stats_action.triggered.connect(self.show_stats)
        menu.addAction(self.stats_action)
        
        # ログ表示
        log_action = QAction("🔍 ログ表示", self)
        log_action.triggered.connect(self.show_log)
        menu.addAction(log_action)
        
        menu.addSeparator()
        
        # メインアプリを開く
        main_app_action = QAction("📱 メインアプリを開く", self)
        main_app_action.triggered.connect(self.open_main_app)
        menu.addAction(main_app_action)
        
        # スタートアップ設定
        startup_action = QAction("🚀 スタートアップに登録", self)
        startup_action.triggered.connect(self.toggle_startup)
        menu.addAction(startup_action)
        
        menu.addSeparator()
        
        # 終了
        quit_action = QAction("❌ 終了", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
    def on_tray_activated(self, reason):
        """トレイアイコンクリック時の処理"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_settings()
            
    def start_monitoring(self):
        """監視開始"""
        if not self.config:
            self.show_settings()
            return
            
        success = self.file_watcher.start_monitoring(self.config)
        if success:
            self.start_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            
            if self.config.get('show_notifications', True):
                self.showMessage(
                    "監視開始",
                    f"フォルダ '{self.config.get('folder_path', 'data')}' の監視を開始しました",
                    QSystemTrayIcon.Information,
                    3000
                )
        else:
            QMessageBox.critical(None, "エラー", "監視の開始に失敗しました")
            
    def stop_monitoring(self):
        """監視停止"""
        self.file_watcher.stop_monitoring()
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        
        self.showMessage(
            "監視停止",
            "ファイル監視を停止しました",
            QSystemTrayIcon.Information,
            2000
        )
        
    def show_settings(self):
        """設定ダイアログを表示"""
        if not self.settings_dialog:
            self.settings_dialog = TraySettingsDialog()
            
        if self.settings_dialog.exec_() == QDialog.Accepted:
            self.config = self.settings_dialog.get_config()
            self.settings_dialog.save_config()
            
            # 監視中の場合は再起動
            if self.file_watcher.is_running:
                self.stop_monitoring()
                QTimer.singleShot(1000, self.start_monitoring)
                
    def show_stats(self):
        """統計を表示"""
        stats = self.file_watcher.get_stats()
        uptime = stats.get('uptime', '未起動')
        processed = stats.get('processed_count', 0)
        
        QMessageBox.information(
            None,
            "監視統計",
            f"処理済みファイル: {processed}件\n稼働時間: {uptime}"
        )
        
    def show_log(self):
        """ログダイアログを表示"""
        if not self.log_dialog:
            self.log_dialog = TrayLogDialog()
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()
        
    def open_main_app(self):
        """メインアプリを開く"""
        try:
            app_path = Path(__file__).parent / "app.py"
            subprocess.Popen([sys.executable, str(app_path)])
        except Exception as e:
            QMessageBox.critical(None, "エラー", f"メインアプリの起動に失敗しました: {str(e)}")
            
    def toggle_startup(self):
        """スタートアップ登録/解除を切り替え"""
        import platform
        
        try:
            if platform.system() == "Windows":
                self._toggle_startup_windows()
            elif platform.system() == "Darwin":  # macOS
                self._toggle_startup_macos()
            else:  # Linux
                self._toggle_startup_linux()
        except Exception as e:
            QMessageBox.critical(None, "エラー", f"スタートアップ設定に失敗しました: {str(e)}")
            
    def _toggle_startup_windows(self):
        """Windows用スタートアップ設定"""
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "BillingManagerTray"
        script_path = Path(__file__).parent / "start_tray_monitor.bat"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            # 既に登録されているかチェック
            try:
                winreg.QueryValueEx(key, app_name)
                # 登録されている場合は削除
                winreg.DeleteValue(key, app_name)
                QMessageBox.information(None, "スタートアップ", "スタートアップから削除しました")
            except FileNotFoundError:
                # 登録されていない場合は追加
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, str(script_path))
                QMessageBox.information(None, "スタートアップ", "スタートアップに登録しました")
                
            winreg.CloseKey(key)
            
        except Exception as e:
            raise Exception(f"Windowsレジストリ操作エラー: {str(e)}")
            
    def _toggle_startup_macos(self):
        """macOS用スタートアップ設定"""
        plist_dir = Path.home() / "Library" / "LaunchAgents"
        plist_file = plist_dir / "com.billingmanager.tray.plist"
        script_path = Path(__file__).parent / "start_tray_monitor.sh"
        
        if plist_file.exists():
            # 既に登録されている場合は削除
            plist_file.unlink()
            subprocess.run(["launchctl", "unload", str(plist_file)], capture_output=True)
            QMessageBox.information(None, "スタートアップ", "スタートアップから削除しました")
        else:
            # 登録されていない場合は追加
            plist_dir.mkdir(parents=True, exist_ok=True)
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.billingmanager.tray</string>
    <key>ProgramArguments</key>
    <array>
        <string>{script_path}</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
            
            with open(plist_file, 'w') as f:
                f.write(plist_content)
                
            subprocess.run(["launchctl", "load", str(plist_file)], capture_output=True)
            QMessageBox.information(None, "スタートアップ", "スタートアップに登録しました")
            
    def _toggle_startup_linux(self):
        """Linux用スタートアップ設定"""
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / "billingmanager-tray.desktop"
        script_path = Path(__file__).parent / "start_tray_monitor.sh"
        
        if desktop_file.exists():
            # 既に登録されている場合は削除
            desktop_file.unlink()
            QMessageBox.information(None, "スタートアップ", "スタートアップから削除しました")
        else:
            # 登録されていない場合は追加
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=BillingManager Tray Monitor
Comment=CSV file monitoring for BillingManager
Exec={script_path} start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
                
            QMessageBox.information(None, "スタートアップ", "スタートアップに登録しました")
            
    def quit_app(self):
        """アプリを終了"""
        reply = QMessageBox.question(
            None,
            "終了確認",
            "ファイル監視を終了しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.file_watcher.is_running:
                self.file_watcher.stop_monitoring()
            self.app.quit()
            
    def on_status_changed(self, is_running, stats):
        """ステータス変更時の処理"""
        self.stats = stats
        processed = stats.get('processed_count', 0)
        self.stats_action.setText(f"📊 統計: {processed}件処理済み")
        
    def on_file_processed(self, file_info):
        """ファイル処理時の処理"""
        filename = file_info.get('filename', '')
        status = file_info.get('status', '')
        
        if self.config.get('show_completion', True):
            self.showMessage(
                "ファイル処理完了",
                f"{filename}\n{status}",
                QSystemTrayIcon.Information,
                3000
            )
            
    def on_log_message(self, message):
        """ログメッセージ受信時の処理"""
        if self.log_dialog:
            self.log_dialog.add_log(message)
            
        # CSVファイル検出時の通知
        if "CSVファイルを検出" in message and self.config.get('show_notifications', True):
            parts = message.split(': ')
            if len(parts) > 1:
                filename = parts[1].split(' ')[0]
                self.showMessage(
                    "CSVファイル検出",
                    f"新しいファイル: {filename}",
                    QSystemTrayIcon.Information,
                    2000
                )
                
    def load_config(self):
        """設定を読み込み"""
        config_file = "monitoring_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {
                    'folder_path': 'data',
                    'interval': 1,
                    'auto_process': True,
                    'duplicate_interval': 5,
                    'show_notifications': True,
                    'show_completion': True
                }
        else:
            self.config = {
                'folder_path': 'data',
                'interval': 1,
                'auto_process': True,
                'duplicate_interval': 5,
                'show_notifications': True,
                'show_completion': True
            }


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # システムトレイが利用可能かチェック
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "システムトレイ",
            "システムトレイが利用できません。"
        )
        sys.exit(1)
        
    # アプリケーション終了時の設定
    app.setQuitOnLastWindowClosed(False)
    
    # トレイアプリを作成
    tray = FileMonitorTray(app)
    
    # アプリケーション実行
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()