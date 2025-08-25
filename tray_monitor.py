#!/usr/bin/env python3
"""
システムトレイ常駐型ファイル監視アプリ
"""

import sys
import os
import json
import subprocess
import psutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import threading
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QCheckBox, QTextEdit,
    QGroupBox, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QWidget, QFileDialog, QComboBox,
    QTimeEdit, QListWidget, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont

from file_watcher_gui import FileWatcherManager


class TraySettingsDialog(QDialog):
    """トレイ用設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("監視設定")
        self.resize(500, 450)
        self.setMinimumSize(450, 400)
        self.setMaximumSize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        self.config_file = "monitoring_config.json"
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 基本設定
        basic_group = QGroupBox("基本設定")
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(10)
        
        self.folder_edit = QLineEdit()
        self.folder_edit.setMinimumWidth(250)
        self.folder_edit.setPlaceholderText("監視するフォルダパスを入力...")
        form_layout.addRow("監視フォルダ:", self.folder_edit)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" 秒")
        self.interval_spin.setMinimumWidth(100)
        form_layout.addRow("監視間隔:", self.interval_spin)
        
        self.auto_process_check = QCheckBox("ファイル検出時に自動処理")
        form_layout.addRow(self.auto_process_check)
        
        self.duplicate_spin = QSpinBox()
        self.duplicate_spin.setRange(1, 300)
        self.duplicate_spin.setSuffix(" 秒")
        self.duplicate_spin.setMinimumWidth(100)
        form_layout.addRow("重複処理防止:", self.duplicate_spin)
        
        basic_group.setLayout(form_layout)
        layout.addWidget(basic_group)
        
        # 通知設定
        notify_group = QGroupBox("通知設定")
        notify_layout = QVBoxLayout()
        notify_layout.setContentsMargins(10, 10, 10, 10)
        notify_layout.setSpacing(8)
        
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
        
        # ボタン用のスペーサー
        layout.addStretch(1)
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


class ApplicationManagerDialog(QDialog):
    """アプリケーション管理メインダイアログ"""
    
    def __init__(self, process_manager, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager
        self.setWindowTitle("アプリケーション管理")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.load_applications()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # タイトル
        title = QLabel("登録済みアプリケーション")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # アプリケーション一覧テーブル
        self.app_table = QTableWidget()
        self.app_table.setColumnCount(5)
        self.app_table.setHorizontalHeaderLabels(['名前', '実行ファイル', '状態', '有効', 'スケジュール'])
        
        # テーブルの設定
        header = self.app_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 名前列を伸縮
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 実行ファイル列を伸縮
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 状態列は内容に合わせる
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 有効列は内容に合わせる
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # スケジュール列は内容に合わせる
        
        self.app_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.app_table.setAlternatingRowColors(True)
        layout.addWidget(self.app_table)
        
        # ボタン類
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ 新規追加")
        self.add_button.clicked.connect(self.add_application)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("✏️ 編集")
        self.edit_button.clicked.connect(self.edit_application)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("🗑️ 削除")
        self.delete_button.clicked.connect(self.delete_application)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("🔄 更新")
        self.refresh_button.clicked.connect(self.load_applications)
        button_layout.addWidget(self.refresh_button)
        
        layout.addLayout(button_layout)
        
        # 閉じるボタン
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.close)
        close_layout.addWidget(close_button)
        
        layout.addLayout(close_layout)
        
        self.setLayout(layout)
    
    def load_applications(self):
        """アプリケーション一覧を読み込み"""
        app_configs = self.process_manager.load_app_configs()
        
        self.app_table.setRowCount(len(app_configs))
        
        for row, (app_id, config) in enumerate(app_configs.items()):
            # 名前
            name_item = QTableWidgetItem(config.get('name', app_id))
            self.app_table.setItem(row, 0, name_item)
            
            # 実行ファイル
            executable = config.get('executable', '')
            args = config.get('args', [])
            full_command = f"{executable} {' '.join(args)}" if args else executable
            exec_item = QTableWidgetItem(full_command)
            self.app_table.setItem(row, 1, exec_item)
            
            # 状態
            is_running = self.process_manager.is_process_running(app_id)
            status_item = QTableWidgetItem("🟢 実行中" if is_running else "⚪ 停止中")
            self.app_table.setItem(row, 2, status_item)
            
            # 有効
            enabled = config.get('enabled', True)
            enabled_item = QTableWidgetItem("✅ 有効" if enabled else "❌ 無効")
            self.app_table.setItem(row, 3, enabled_item)
            
            # スケジュール
            schedule = config.get('schedule', {})
            if schedule.get('enabled', False):
                start_time = schedule.get('start_time', '')
                stop_time = schedule.get('stop_time', '')
                schedule_text = f"⏰ {start_time}-{stop_time}"
            else:
                schedule_text = "📋 手動"
            schedule_item = QTableWidgetItem(schedule_text)
            self.app_table.setItem(row, 4, schedule_item)
            
            # 行データにapp_idを保存
            name_item.setData(Qt.UserRole, app_id)
    
    def add_application(self):
        """新規アプリケーション追加"""
        dialog = ApplicationEditDialog(self.process_manager, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_applications()
    
    def edit_application(self):
        """選択したアプリケーションを編集"""
        current_row = self.app_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "情報", "編集するアプリケーションを選択してください。")
            return
        
        name_item = self.app_table.item(current_row, 0)
        app_id = name_item.data(Qt.UserRole)
        
        dialog = ApplicationEditDialog(self.process_manager, app_id=app_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_applications()
    
    def delete_application(self):
        """選択したアプリケーションを削除"""
        current_row = self.app_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "情報", "削除するアプリケーションを選択してください。")
            return
        
        name_item = self.app_table.item(current_row, 0)
        app_id = name_item.data(Qt.UserRole)
        app_name = name_item.text()
        
        reply = QMessageBox.question(
            self, "確認", 
            f"アプリケーション '{app_name}' を削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.process_manager.delete_app_config(app_id)
            self.load_applications()


class ApplicationEditDialog(QDialog):
    """個別アプリケーション設定ダイアログ"""
    
    def __init__(self, process_manager, app_id=None, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager
        self.app_id = app_id
        self.is_editing = app_id is not None
        
        title = "アプリケーション編集" if self.is_editing else "新規アプリケーション追加"
        self.setWindowTitle(title)
        self.resize(600, 500)
        self.setMinimumSize(500, 400)
        
        self.setup_ui()
        
        if self.is_editing:
            self.load_app_config()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 基本設定タブ
        basic_tab = QWidget()
        self.setup_basic_tab(basic_tab)
        self.tab_widget.addTab(basic_tab, "⚙️ 基本設定")
        
        # スケジュールタブ
        schedule_tab = QWidget()
        self.setup_schedule_tab(schedule_tab)
        self.tab_widget.addTab(schedule_tab, "⏰ スケジュール")
        
        # 詳細タブ
        advanced_tab = QWidget()
        self.setup_advanced_tab(advanced_tab)
        self.tab_widget.addTab(advanced_tab, "🔧 詳細")
        
        layout.addWidget(self.tab_widget)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("💾 保存")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        cancel_button = QPushButton("❌ キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def setup_basic_tab(self, tab):
        layout = QFormLayout()
        layout.setSpacing(15)
        
        # アプリケーション名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: Chrome ブラウザ")
        layout.addRow("アプリケーション名:", self.name_edit)
        
        # 実行ファイル
        exe_layout = QHBoxLayout()
        self.executable_edit = QLineEdit()
        self.executable_edit.setPlaceholderText("例: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        
        browse_button = QPushButton("📁 参照")
        browse_button.clicked.connect(self.browse_executable)
        
        exe_layout.addWidget(self.executable_edit)
        exe_layout.addWidget(browse_button)
        
        layout.addRow("実行ファイル:", exe_layout)
        
        # 引数
        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("例: --new-window --profile-directory=Default")
        layout.addRow("コマンドライン引数:", self.args_edit)
        
        # 作業ディレクトリ
        work_layout = QHBoxLayout()
        self.working_dir_edit = QLineEdit()
        self.working_dir_edit.setText(".")
        
        work_browse_button = QPushButton("📁 参照")
        work_browse_button.clicked.connect(self.browse_working_dir)
        
        work_layout.addWidget(self.working_dir_edit)
        work_layout.addWidget(work_browse_button)
        
        layout.addRow("作業ディレクトリ:", work_layout)
        
        # 有効/無効
        self.enabled_checkbox = QCheckBox("このアプリケーションを有効にする")
        self.enabled_checkbox.setChecked(True)
        layout.addRow("", self.enabled_checkbox)
        
        tab.setLayout(layout)
    
    def setup_schedule_tab(self, tab):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # スケジュール有効化
        self.schedule_enabled_checkbox = QCheckBox("スケジュール機能を有効にする")
        self.schedule_enabled_checkbox.toggled.connect(self.toggle_schedule_options)
        layout.addWidget(self.schedule_enabled_checkbox)
        
        # スケジュール設定グループ
        self.schedule_group = QGroupBox("スケジュール設定")
        schedule_layout = QFormLayout()
        
        # 開始時刻
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        schedule_layout.addRow("開始時刻:", self.start_time_edit)
        
        # 終了時刻
        self.stop_time_edit = QTimeEdit()
        self.stop_time_edit.setDisplayFormat("HH:mm")
        schedule_layout.addRow("終了時刻:", self.stop_time_edit)
        
        # 実行曜日
        days_layout = QHBoxLayout()
        self.day_checkboxes = {}
        days = [
            ('Monday', '月'), ('Tuesday', '火'), ('Wednesday', '水'),
            ('Thursday', '木'), ('Friday', '金'), ('Saturday', '土'), ('Sunday', '日')
        ]
        
        for day_en, day_jp in days:
            checkbox = QCheckBox(day_jp)
            self.day_checkboxes[day_en] = checkbox
            days_layout.addWidget(checkbox)
        
        schedule_layout.addRow("実行曜日:", days_layout)
        
        # 起動遅延
        self.startup_delay_spin = QSpinBox()
        self.startup_delay_spin.setRange(0, 3600)  # 0秒～1時間
        self.startup_delay_spin.setSuffix(" 秒")
        schedule_layout.addRow("起動遅延:", self.startup_delay_spin)
        
        self.schedule_group.setLayout(schedule_layout)
        layout.addWidget(self.schedule_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # 初期状態でスケジュール設定を無効化
        self.schedule_group.setEnabled(False)
    
    def setup_advanced_tab(self, tab):
        layout = QFormLayout()
        layout.setSpacing(15)
        
        # 自動再起動
        self.auto_restart_checkbox = QCheckBox("プロセス終了時に自動再起動する")
        layout.addRow("", self.auto_restart_checkbox)
        
        # 自動再起動間隔
        self.restart_interval_spin = QSpinBox()
        self.restart_interval_spin.setRange(0, 168)  # 0時間～1週間
        self.restart_interval_spin.setSuffix(" 時間")
        self.restart_interval_spin.setSpecialValueText("無制限")
        layout.addRow("定期再起動間隔:", self.restart_interval_spin)
        
        layout.addItem(QVBoxLayout())  # スペーサー
        tab.setLayout(layout)
    
    def toggle_schedule_options(self, enabled):
        """スケジュール設定の有効/無効切り替え"""
        self.schedule_group.setEnabled(enabled)
    
    def browse_executable(self):
        """実行ファイルを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "実行ファイルを選択", "", 
            "実行ファイル (*.exe *.app);;全てのファイル (*)"
        )
        if file_path:
            self.executable_edit.setText(file_path)
            
            # ファイル名から推測してアプリ名を設定
            if not self.name_edit.text():
                app_name = Path(file_path).stem
                self.name_edit.setText(app_name)
    
    def browse_working_dir(self):
        """作業ディレクトリを選択"""
        dir_path = QFileDialog.getExistingDirectory(self, "作業ディレクトリを選択")
        if dir_path:
            self.working_dir_edit.setText(dir_path)
    
    def load_app_config(self):
        """既存の設定を読み込み"""
        if not self.app_id:
            return
            
        app_configs = self.process_manager.load_app_configs()
        if self.app_id not in app_configs:
            return
            
        config = app_configs[self.app_id]
        
        # 基本設定
        self.name_edit.setText(config.get('name', ''))
        self.executable_edit.setText(config.get('executable', ''))
        
        args = config.get('args', [])
        self.args_edit.setText(' '.join(args) if args else '')
        
        self.working_dir_edit.setText(config.get('working_directory', '.'))
        self.enabled_checkbox.setChecked(config.get('enabled', True))
        
        # スケジュール設定
        schedule = config.get('schedule', {})
        schedule_enabled = schedule.get('enabled', False)
        self.schedule_enabled_checkbox.setChecked(schedule_enabled)
        
        if 'start_time' in schedule and schedule['start_time']:
            start_time = datetime.strptime(schedule['start_time'], '%H:%M').time()
            self.start_time_edit.setTime(start_time)
        
        if 'stop_time' in schedule and schedule['stop_time']:
            stop_time = datetime.strptime(schedule['stop_time'], '%H:%M').time()
            self.stop_time_edit.setTime(stop_time)
        
        # 曜日設定
        days = schedule.get('days', [])
        for day_en, checkbox in self.day_checkboxes.items():
            checkbox.setChecked(day_en in days)
        
        self.startup_delay_spin.setValue(schedule.get('startup_delay', 0))
        
        # 詳細設定
        self.auto_restart_checkbox.setChecked(config.get('auto_restart', False))
        self.restart_interval_spin.setValue(schedule.get('auto_restart_interval', 0))
    
    def save_config(self):
        """設定を保存"""
        # バリデーション
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "アプリケーション名を入力してください。")
            return
        
        if not self.executable_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "実行ファイルを指定してください。")
            return
        
        # 設定を構築
        config = {
            'name': self.name_edit.text().strip(),
            'executable': self.executable_edit.text().strip(),
            'args': self.args_edit.text().split() if self.args_edit.text().strip() else [],
            'working_directory': self.working_dir_edit.text().strip() or '.',
            'enabled': self.enabled_checkbox.isChecked(),
            'auto_restart': self.auto_restart_checkbox.isChecked(),
            'schedule': {
                'enabled': self.schedule_enabled_checkbox.isChecked(),
                'start_time': self.start_time_edit.time().toString('HH:mm') if self.schedule_enabled_checkbox.isChecked() else '',
                'stop_time': self.stop_time_edit.time().toString('HH:mm') if self.schedule_enabled_checkbox.isChecked() else '',
                'days': [day_en for day_en, checkbox in self.day_checkboxes.items() if checkbox.isChecked()],
                'startup_delay': self.startup_delay_spin.value(),
                'auto_restart_interval': self.restart_interval_spin.value()
            }
        }
        
        # アプリIDを生成または使用
        if self.app_id is None:
            # 新規の場合、名前からIDを生成
            import re
            app_id = re.sub(r'[^\w\-]', '_', config['name'].lower())
            app_id = re.sub(r'_+', '_', app_id).strip('_')
        else:
            app_id = self.app_id
        
        # 設定を保存
        try:
            self.process_manager.save_app_config(app_id, config)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "保存エラー", f"設定の保存に失敗しました: {e}")


class TrayLogDialog(QDialog):
    """ログ表示ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("監視ログ")
        self.resize(700, 500)
        self.setMinimumSize(500, 350)
        self.setMaximumSize(1200, 800)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # macOS/Windows対応のフォント設定
        import platform
        if platform.system() == "Darwin":  # macOS
            font = QFont("Monaco", 10)
        elif platform.system() == "Windows":
            font = QFont("Consolas", 10)
        else:  # Linux
            font = QFont("DejaVu Sans Mono", 10)
        self.log_text.setFont(font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; 
                color: #dcdcdc;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # スペーサーを追加してボタンを右寄せ
        button_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ クリア")
        clear_btn.setMinimumSize(100, 32)
        clear_btn.clicked.connect(self.log_text.clear)
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("❌ 閉じる")
        close_btn.setMinimumSize(100, 32)
        close_btn.setDefault(True)
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


class ApplicationScheduler:
    """アプリケーションスケジュール管理クラス"""
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, dict] = {}
        self.running = False
        self.scheduler_thread = None
        
    def add_scheduled_app(self, app_id: str, app_config: dict, process_manager):
        """スケジュール対象アプリケーションを追加"""
        schedule_config = app_config.get('schedule', {})
        if not schedule_config.get('enabled', False):
            return
            
        self.scheduled_tasks[app_id] = {
            'config': app_config,
            'schedule': schedule_config,
            'process_manager': process_manager,
            'last_start': None,
            'last_stop': None,
            'next_start': None,
            'next_stop': None
        }
        
        # 次回実行時刻を計算
        self._calculate_next_times(app_id)
        
    def start_scheduler(self):
        """スケジューラーを開始"""
        if self.running:
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
    def stop_scheduler(self):
        """スケジューラーを停止"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1)
            
    def _scheduler_loop(self):
        """スケジューラーのメインループ"""
        while self.running:
            current_time = datetime.now()
            
            for app_id, task_info in self.scheduled_tasks.items():
                self._check_and_execute_task(app_id, task_info, current_time)
                
            time.sleep(30)  # 30秒ごとにチェック
            
    def _check_and_execute_task(self, app_id: str, task_info: dict, current_time: datetime):
        """タスクの実行時刻をチェックして実行"""
        schedule = task_info['schedule']
        process_manager = task_info['process_manager']
        
        # 曜日チェック
        current_day = current_time.strftime('%A')
        if schedule['days'] and current_day not in schedule['days']:
            return
            
        # 起動時刻チェック
        if (schedule['start_time'] and task_info['next_start'] and 
            current_time >= task_info['next_start']):
            
            if not process_manager.is_process_running(app_id):
                print(f"スケジュール起動: {task_info['config']['name']}")
                success, message = process_manager.start_application(app_id, task_info['config'])
                if success:
                    task_info['last_start'] = current_time
                    self._calculate_next_start_time(app_id, task_info)
                    
        # 停止時刻チェック
        if (schedule['stop_time'] and task_info['next_stop'] and 
            current_time >= task_info['next_stop']):
            
            if process_manager.is_process_running(app_id):
                print(f"スケジュール停止: {task_info['config']['name']}")
                success, message = process_manager.stop_application(app_id)
                if success:
                    task_info['last_stop'] = current_time
                    self._calculate_next_stop_time(app_id, task_info)
                    
        # 自動再起動チェック
        restart_interval = schedule.get('auto_restart_interval', 0)
        if (restart_interval > 0 and task_info['last_start'] and
            current_time >= task_info['last_start'] + timedelta(hours=restart_interval)):
            
            if process_manager.is_process_running(app_id):
                print(f"自動再起動: {task_info['config']['name']}")
                process_manager.restart_application(app_id)
                task_info['last_start'] = current_time
                
    def _calculate_next_times(self, app_id: str):
        """次回実行時刻を計算"""
        self._calculate_next_start_time(app_id, self.scheduled_tasks[app_id])
        self._calculate_next_stop_time(app_id, self.scheduled_tasks[app_id])
        
    def _calculate_next_start_time(self, app_id: str, task_info: dict):
        """次回起動時刻を計算"""
        schedule = task_info['schedule']
        start_time_str = schedule.get('start_time')
        
        if not start_time_str or not schedule.get('days'):
            task_info['next_start'] = None
            return
            
        try:
            current_time = datetime.now()
            start_hour, start_minute = map(int, start_time_str.split(':'))
            
            # 今日以降で最初に該当する曜日を見つける
            for days_ahead in range(8):  # 最大1週間先まで
                target_date = current_time + timedelta(days=days_ahead)
                target_day = target_date.strftime('%A')
                
                if target_day in schedule['days']:
                    next_start = target_date.replace(
                        hour=start_hour, minute=start_minute, second=0, microsecond=0
                    )
                    
                    if next_start > current_time:
                        task_info['next_start'] = next_start
                        return
                        
            task_info['next_start'] = None
            
        except (ValueError, IndexError):
            task_info['next_start'] = None
            
    def _calculate_next_stop_time(self, app_id: str, task_info: dict):
        """次回停止時刻を計算"""
        schedule = task_info['schedule']
        stop_time_str = schedule.get('stop_time')
        
        if not stop_time_str or not schedule.get('days'):
            task_info['next_stop'] = None
            return
            
        try:
            current_time = datetime.now()
            stop_hour, stop_minute = map(int, stop_time_str.split(':'))
            
            # 今日以降で最初に該当する曜日を見つける
            for days_ahead in range(8):  # 最大1週間先まで
                target_date = current_time + timedelta(days=days_ahead)
                target_day = target_date.strftime('%A')
                
                if target_day in schedule['days']:
                    next_stop = target_date.replace(
                        hour=stop_hour, minute=stop_minute, second=0, microsecond=0
                    )
                    
                    if next_stop > current_time:
                        task_info['next_stop'] = next_stop
                        return
                        
            task_info['next_stop'] = None
            
        except (ValueError, IndexError):
            task_info['next_stop'] = None
            
    def get_schedule_info(self, app_id: str) -> Optional[dict]:
        """アプリケーションのスケジュール情報を取得"""
        if app_id not in self.scheduled_tasks:
            return None
            
        task_info = self.scheduled_tasks[app_id]
        return {
            'next_start': task_info.get('next_start'),
            'next_stop': task_info.get('next_stop'),
            'last_start': task_info.get('last_start'),
            'last_stop': task_info.get('last_stop'),
            'enabled': task_info['schedule'].get('enabled', False)
        }
        
    def get_all_schedules(self) -> Dict[str, dict]:
        """全アプリケーションのスケジュール情報を取得"""
        schedules = {}
        for app_id in self.scheduled_tasks:
            schedules[app_id] = self.get_schedule_info(app_id)
        return schedules


class ProcessManager:
    """プロセス管理クラス"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.process_configs: Dict[str, dict] = {}
        
    def load_app_configs(self, config_path=None):
        """アプリケーション設定を読み込み"""
        if config_path is None:
            # スクリプトファイルの場所を基準にした絶対パス
            config_path = Path(__file__).parent / "config" / "app_config.json"
        else:
            config_path = Path(config_path)
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('tray_applications', {})
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {config_path}")
            print("初回実行のため、デフォルト設定ファイルを作成します...")
            
            # デフォルト設定ファイルを作成
            if self.create_default_config_file(config_path):
                # 作成したファイルを再読み込み
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    return config.get('tray_applications', {})
                except Exception as e:
                    print(f"作成した設定ファイルの読み込みエラー: {e}")
            
            # ファイル作成に失敗した場合はデフォルト設定を返す
            return self._get_default_app_configs()
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            return self._get_default_app_configs()
            
    def create_default_config_file(self, config_path):
        """デフォルト設定ファイルを作成"""
        config_dir = config_path.parent
        
        # config ディレクトリが存在しない場合は作成
        config_dir.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "application": {
                "name": "Generic Business Manager",
                "version": "1.0.0",
                "author": "Generic Framework"
            },
            "tray_applications": self._get_default_app_configs()
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"デフォルト設定ファイルを作成しました: {config_path}")
            return True
        except Exception as e:
            print(f"設定ファイル作成エラー: {e}")
            return False
            
    def _get_default_app_configs(self):
        """デフォルトアプリケーション設定を返す"""
        import platform
        
        system = platform.system()
        default_configs = {}
        
        if system == "Windows":
            default_configs = {
                "notepad": {
                    "name": "メモ帳",
                    "executable": "notepad.exe",
                    "args": [],
                    "working_directory": ".",
                    "enabled": True,
                    "auto_restart": False,
                    "schedule": {
                        "enabled": False,
                        "start_time": "",
                        "stop_time": "",
                        "days": [],
                        "startup_delay": 0,
                        "auto_restart_interval": 0
                    }
                },
                "calculator": {
                    "name": "電卓",
                    "executable": "calc.exe", 
                    "args": [],
                    "working_directory": ".",
                    "enabled": True,
                    "auto_restart": False,
                    "schedule": {
                        "enabled": False,
                        "start_time": "",
                        "stop_time": "",
                        "days": [],
                        "startup_delay": 0,
                        "auto_restart_interval": 0
                    }
                }
            }
        elif system == "Darwin":  # macOS
            default_configs = {
                "textedit": {
                    "name": "テキストエディット",
                    "executable": "open",
                    "args": ["-a", "TextEdit"],
                    "working_directory": ".",
                    "enabled": True,
                    "auto_restart": False,
                    "schedule": {
                        "enabled": False,
                        "start_time": "",
                        "stop_time": "",
                        "days": [],
                        "startup_delay": 0,
                        "auto_restart_interval": 0
                    }
                },
                "calculator": {
                    "name": "電卓",
                    "executable": "open",
                    "args": ["-a", "Calculator"],
                    "working_directory": ".",
                    "enabled": True,
                    "auto_restart": False,
                    "schedule": {
                        "enabled": False,
                        "start_time": "",
                        "stop_time": "",
                        "days": [],
                        "startup_delay": 0,
                        "auto_restart_interval": 0
                    }
                }
            }
        else:  # Linux
            default_configs = {
                "gedit": {
                    "name": "テキストエディタ",
                    "executable": "gedit",
                    "args": [],
                    "working_directory": ".",
                    "enabled": True,
                    "auto_restart": False,
                    "schedule": {
                        "enabled": False,
                        "start_time": "",
                        "stop_time": "",
                        "days": [],
                        "startup_delay": 0,
                        "auto_restart_interval": 0
                    }
                },
                "calculator": {
                    "name": "電卓",
                    "executable": "gnome-calculator",
                    "args": [],
                    "working_directory": ".",
                    "enabled": True,
                    "auto_restart": False,
                    "schedule": {
                        "enabled": False,
                        "start_time": "",
                        "stop_time": "",
                        "days": [],
                        "startup_delay": 0,
                        "auto_restart_interval": 0
                    }
                }
            }
            
        return default_configs
    
    def save_app_config(self, app_id: str, config: dict):
        """アプリケーション設定を保存"""
        config_path = Path(__file__).parent / "config" / "app_config.json"
        
        try:
            # 既存の設定ファイルを読み込み
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
            else:
                # ファイルが存在しない場合は新規作成
                full_config = {
                    "application": {
                        "name": "Generic Business Manager",
                        "version": "1.0.0",
                        "author": "Generic Framework"
                    },
                    "tray_applications": {}
                }
            
            # アプリケーション設定を更新
            if "tray_applications" not in full_config:
                full_config["tray_applications"] = {}
            
            full_config["tray_applications"][app_id] = config
            
            # 設定ファイルに保存
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, ensure_ascii=False, indent=2)
            
            print(f"アプリケーション設定を保存しました: {app_id}")
            
        except Exception as e:
            raise Exception(f"設定保存エラー: {e}")
    
    def delete_app_config(self, app_id: str):
        """アプリケーション設定を削除"""
        config_path = Path(__file__).parent / "config" / "app_config.json"
        
        try:
            # 既存の設定ファイルを読み込み
            if not config_path.exists():
                return
                
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = json.load(f)
            
            # アプリケーション設定を削除
            if "tray_applications" in full_config and app_id in full_config["tray_applications"]:
                del full_config["tray_applications"][app_id]
                
                # 設定ファイルに保存
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(full_config, f, ensure_ascii=False, indent=2)
                
                print(f"アプリケーション設定を削除しました: {app_id}")
            
            # プロセスが実行中の場合は停止
            if app_id in self.processes:
                self.stop_application(app_id)
                
        except Exception as e:
            raise Exception(f"設定削除エラー: {e}")
            
    def start_application(self, app_id: str, app_config: dict) -> Tuple[bool, str]:
        """アプリケーションを起動"""
        if app_id in self.processes:
            if self.is_process_running(app_id):
                return False, "既に起動中です"
                
        try:
            executable = app_config['executable']
            args = app_config.get('args', [])
            working_dir = app_config.get('working_directory', '.')
            
            # 作業ディレクトリを絶対パスに変換
            if not os.path.isabs(working_dir):
                working_dir = str(Path(__file__).parent / working_dir)
            
            # Windows固有の実行ファイルパス処理
            import platform
            if platform.system() == "Windows":
                # Windows環境でのパス処理
                if not os.path.isabs(executable) and not executable.endswith('.exe'):
                    # システムコマンドかどうかをチェック
                    import shutil
                    if not shutil.which(executable):
                        return False, f"実行ファイルが見つかりません: {executable}"
                elif executable.endswith('.exe') and not os.path.isabs(executable):
                    # 相対パスの.exeファイルを絶対パスに変換
                    abs_exe = Path(__file__).parent / executable
                    if abs_exe.exists():
                        executable = str(abs_exe)
                    else:
                        # システムPATHからの検索
                        import shutil
                        found_exe = shutil.which(executable)
                        if found_exe:
                            executable = found_exe
                        else:
                            return False, f"実行ファイルが見つかりません: {executable}"
            else:
                # macOS/Linux環境でのパス処理
                if not os.path.isabs(executable):
                    import shutil
                    if not shutil.which(executable):
                        # 相対パスの場合は絶対パスに変換してチェック
                        abs_exe = Path(__file__).parent / executable
                        if abs_exe.exists():
                            executable = str(abs_exe)
                        else:
                            return False, f"実行ファイルが見つかりません: {executable}"
            
            # コマンドライン引数を構築
            cmd = [executable] + args
            
            # プロセスを起動
            creation_flags = 0
            if platform.system() == "Windows":
                # Windows環境でコンソールウィンドウを表示しない
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            
            # 起動が成功したかチェック（少し待つ）
            time.sleep(0.5)
            if process.poll() is not None:
                # プロセスが既に終了している場合
                stderr = process.stderr.read().decode('utf-8', errors='ignore')
                return False, f"起動に失敗しました: {stderr[:100]}"
            
            self.processes[app_id] = process
            self.process_configs[app_id] = app_config
            return True, "起動成功"
            
        except FileNotFoundError:
            return False, f"実行ファイルが見つかりません: {executable}"
        except Exception as e:
            return False, f"起動エラー: {str(e)}"
            
    def stop_application(self, app_id: str) -> Tuple[bool, str]:
        """アプリケーションを停止"""
        if app_id not in self.processes:
            return False, "プロセスが見つかりません"
            
        try:
            process = self.processes[app_id]
            if process.poll() is None:  # プロセスがまだ実行中
                process.terminate()
                
                # 正常終了を待つ
                for _ in range(10):  # 最大10秒待つ
                    time.sleep(1)
                    if process.poll() is not None:
                        break
                
                # まだ終了していない場合は強制終了
                if process.poll() is None:
                    process.kill()
                    time.sleep(1)
                    if process.poll() is None:
                        return False, "プロセスの強制終了に失敗しました"
                    
            del self.processes[app_id]
            return True, "停止成功"
            
        except Exception as e:
            return False, f"停止エラー: {str(e)}"
            
    def restart_application(self, app_id: str) -> Tuple[bool, str]:
        """アプリケーションを再起動"""
        if app_id not in self.process_configs:
            return False, "アプリケーション設定が見つかりません"
            
        # 停止
        if app_id in self.processes:
            stop_success, stop_message = self.stop_application(app_id)
            if not stop_success:
                return False, f"停止に失敗: {stop_message}"
        
        time.sleep(1)
        
        # 起動
        start_success, start_message = self.start_application(app_id, self.process_configs[app_id])
        if start_success:
            return True, "再起動成功"
        else:
            return False, f"起動に失敗: {start_message}"
        
    def is_process_running(self, app_id: str) -> bool:
        """プロセスが実行中かチェック"""
        if app_id not in self.processes:
            return False
            
        try:
            process = self.processes[app_id]
            return process.poll() is None
        except Exception:
            return False
            
    def get_process_status(self, app_id: str) -> str:
        """プロセス状態を取得"""
        if self.is_process_running(app_id):
            return "実行中"
        elif app_id in self.processes:
            return "停止済み"
        else:
            return "未起動"
            
    def cleanup_dead_processes(self):
        """終了したプロセスをクリーンアップ"""
        dead_processes = []
        for app_id, process in self.processes.items():
            if process.poll() is not None:  # プロセスが終了している
                dead_processes.append(app_id)
                
        for app_id in dead_processes:
            if app_id in self.processes:
                del self.processes[app_id]
                
    def stop_all_applications(self):
        """すべてのアプリケーションを停止"""
        app_ids = list(self.processes.keys())
        for app_id in app_ids:
            self.stop_application(app_id)


class FileMonitorTray(QSystemTrayIcon):
    """システムトレイ常駐監視アプリ"""
    
    def __init__(self, app):
        # アイコンを作成
        icon = self.create_icon()
        super().__init__(icon, app)
        
        self.app = app
        self.file_watcher = FileWatcherManager()
        self.process_manager = ProcessManager()
        self.scheduler = ApplicationScheduler()
        self.config = {}
        self.stats = {'processed_count': 0}
        self.app_configs = {}
        
        # ダイアログ
        self.settings_dialog = None
        self.log_dialog = None
        
        # タイマーでプロセス状態を監視
        self.process_monitor_timer = QTimer()
        self.process_monitor_timer.timeout.connect(self.update_process_status)
        self.process_monitor_timer.start(5000)  # 5秒間隔
        
        # アプリケーション設定を読み込み
        self.load_app_configs()
        
        # スケジューラーを初期化・開始
        self.init_scheduler()
        
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
            "BillingManager - アプリケーションランチャー",
            "アプリケーション管理システムが起動しました",
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
        
        # アプリケーション管理セクション
        if self.app_configs:
            app_menu = QMenu("🚀 アプリケーション管理")
            
            for app_id, app_config in self.app_configs.items():
                if not app_config.get('enabled', True):
                    continue
                    
                app_submenu = QMenu(app_config['name'])
                
                # 起動
                start_action = QAction(f"▶️ 起動", self)
                start_action.triggered.connect(lambda checked, aid=app_id: self.start_app(aid))
                app_submenu.addAction(start_action)
                
                # 停止
                stop_action = QAction(f"⏹️ 停止", self)
                stop_action.triggered.connect(lambda checked, aid=app_id: self.stop_app(aid))
                app_submenu.addAction(stop_action)
                
                # 再起動
                restart_action = QAction(f"🔄 再起動", self)
                restart_action.triggered.connect(lambda checked, aid=app_id: self.restart_app(aid))
                app_submenu.addAction(restart_action)
                
                app_submenu.addSeparator()
                
                # ステータス表示
                status = self.process_manager.get_process_status(app_id)
                status_action = QAction(f"📊 状態: {status}", self)
                status_action.setEnabled(False)
                app_submenu.addAction(status_action)
                
                app_menu.addMenu(app_submenu)
                
            menu.addMenu(app_menu)
        
        # アプリケーション管理メニュー
        manage_menu = QMenu("⚙️ アプリケーション設定")
        
        manage_action = QAction("📋 アプリ管理画面", self)
        manage_action.triggered.connect(self.show_app_manager)
        manage_menu.addAction(manage_action)
        
        add_action = QAction("➕ 新規アプリ追加", self)
        add_action.triggered.connect(self.add_new_app)
        manage_menu.addAction(add_action)
        
        menu.addMenu(manage_menu)
        menu.addSeparator()
        
        # ファイル監視セクション
        monitor_menu = QMenu("📁 ファイル監視")
        
        self.start_action = QAction("▶️ 監視開始", self)
        self.start_action.triggered.connect(self.start_monitoring)
        monitor_menu.addAction(self.start_action)
        
        self.stop_action = QAction("⏹️ 監視停止", self)
        self.stop_action.triggered.connect(self.stop_monitoring)
        self.stop_action.setEnabled(False)
        monitor_menu.addAction(self.stop_action)
        
        monitor_menu.addSeparator()
        
        # 統計表示
        self.stats_action = QAction("📊 統計: 0件処理済み", self)
        self.stats_action.triggered.connect(self.show_stats)
        monitor_menu.addAction(self.stats_action)
        
        menu.addMenu(monitor_menu)
        menu.addSeparator()
        
        # スケジュール管理セクション
        schedule_menu = QMenu("📅 スケジュール管理")
        
        # 全スケジュール情報を表示
        all_schedules = self.scheduler.get_all_schedules()
        if all_schedules:
            for app_id, schedule_info in all_schedules.items():
                if schedule_info and schedule_info['enabled']:
                    app_name = self.app_configs[app_id]['name']
                    next_start = schedule_info['next_start']
                    next_stop = schedule_info['next_stop']
                    
                    if next_start:
                        start_str = next_start.strftime("%m/%d %H:%M")
                        schedule_action = QAction(f"▶️ {app_name}: 次回起動 {start_str}", self)
                        schedule_action.setEnabled(False)
                        schedule_menu.addAction(schedule_action)
                        
                    if next_stop:
                        stop_str = next_stop.strftime("%m/%d %H:%M")
                        schedule_action = QAction(f"⏹️ {app_name}: 次回停止 {stop_str}", self)
                        schedule_action.setEnabled(False)
                        schedule_menu.addAction(schedule_action)
        else:
            no_schedule_action = QAction("スケジュールされたアプリはありません", self)
            no_schedule_action.setEnabled(False)
            schedule_menu.addAction(no_schedule_action)
            
        schedule_menu.addSeparator()
        
        # スケジューラー制御
        if self.scheduler.running:
            pause_action = QAction("⏸️ スケジューラー一時停止", self)
            pause_action.triggered.connect(self.pause_scheduler)
            schedule_menu.addAction(pause_action)
        else:
            resume_action = QAction("▶️ スケジューラー再開", self)
            resume_action.triggered.connect(self.resume_scheduler)
            schedule_menu.addAction(resume_action)
            
        menu.addMenu(schedule_menu)
        menu.addSeparator()
        
        # 設定
        settings_action = QAction("⚙️ 設定...", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # ログ表示
        log_action = QAction("🔍 ログ表示", self)
        log_action.triggered.connect(self.show_log)
        menu.addAction(log_action)
        
        menu.addSeparator()
        
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
    
    def show_app_manager(self):
        """アプリケーション管理ダイアログを表示"""
        dialog = ApplicationManagerDialog(self.process_manager, self)
        dialog.finished.connect(self.reload_app_configs)
        dialog.exec_()
    
    def add_new_app(self):
        """新規アプリケーション追加ダイアログを表示"""
        dialog = ApplicationEditDialog(self.process_manager, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.reload_app_configs()
    
    def reload_app_configs(self):
        """アプリケーション設定を再読み込みしてメニューを更新"""
        try:
            # 設定を再読み込み
            self.load_app_configs()
            
            # スケジューラーを再初期化
            self.scheduler.stop_scheduler()
            self.init_scheduler()
            
            # メニューを更新
            self.update_context_menu()
            
            print("アプリケーション設定を更新しました")
            
        except Exception as e:
            print(f"設定更新エラー: {e}")
    
    def update_context_menu(self):
        """コンテキストメニューを更新"""
        try:
            # 既存のメニューを削除
            self.tray_icon.setContextMenu(None)
            
            # 新しいメニューを作成
            context_menu = self.create_context_menu()
            self.tray_icon.setContextMenu(context_menu)
            
        except Exception as e:
            print(f"メニュー更新エラー: {e}")
                
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
        
    def load_app_configs(self):
        """アプリケーション設定を読み込み"""
        self.app_configs = self.process_manager.load_app_configs()
        
    def init_scheduler(self):
        """スケジューラーを初期化"""
        # 各アプリケーションをスケジューラーに追加
        for app_id, app_config in self.app_configs.items():
            self.scheduler.add_scheduled_app(app_id, app_config, self.process_manager)
            
        # スケジューラー開始
        self.scheduler.start_scheduler()
        
        print("🕒 スケジューラーが開始されました")
        
    def start_app(self, app_id: str):
        """アプリケーションを起動"""
        if app_id in self.app_configs:
            config = self.app_configs[app_id]
            success, message = self.process_manager.start_application(app_id, config)
            
            if success:
                self.showMessage(
                    "アプリケーション起動",
                    f"{config['name']} を起動しました",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.update_menu()
            else:
                QMessageBox.critical(None, "起動エラー", f"{config['name']}: {message}")
                    
    def stop_app(self, app_id: str):
        """アプリケーションを停止"""
        if app_id in self.app_configs:
            config = self.app_configs[app_id]
            success, message = self.process_manager.stop_application(app_id)
            
            if success:
                self.showMessage(
                    "アプリケーション停止",
                    f"{config['name']} を停止しました",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.update_menu()
            else:
                QMessageBox.critical(None, "停止エラー", f"{config['name']}: {message}")
                
    def restart_app(self, app_id: str):
        """アプリケーションを再起動"""
        if app_id in self.app_configs:
            config = self.app_configs[app_id]
            success, message = self.process_manager.restart_application(app_id)
            
            if success:
                self.showMessage(
                    "アプリケーション再起動",
                    f"{config['name']} を再起動しました",
                    QSystemTrayIcon.Information,
                    3000
                )
                self.update_menu()
            else:
                QMessageBox.critical(None, "再起動エラー", f"{config['name']}: {message}")
                
    def update_process_status(self):
        """プロセス状態を更新"""
        self.process_manager.cleanup_dead_processes()
        self.update_menu()
        
    def update_menu(self):
        """メニューを更新"""
        self.create_context_menu()
        
    def pause_scheduler(self):
        """スケジューラーを一時停止"""
        self.scheduler.stop_scheduler()
        self.showMessage(
            "スケジューラー停止",
            "スケジューラーを一時停止しました",
            QSystemTrayIcon.Information,
            2000
        )
        self.update_menu()
        
    def resume_scheduler(self):
        """スケジューラーを再開"""
        self.scheduler.start_scheduler()
        self.showMessage(
            "スケジューラー再開",
            "スケジューラーを再開しました",
            QSystemTrayIcon.Information,
            2000
        )
        self.update_menu()
        
    def open_main_app(self):
        """メインアプリを開く"""
        self.start_app('main_app')
            
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
            "アプリケーション管理システムを終了しますか？\n起動中のアプリケーションも停止されます。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # ファイル監視停止
            if self.file_watcher.is_running:
                self.file_watcher.stop_monitoring()
                
            # スケジューラー停止
            self.scheduler.stop_scheduler()
            
            # すべてのプロセスを停止
            self.process_manager.stop_all_applications()
            
            # タイマー停止
            if hasattr(self, 'process_monitor_timer'):
                self.process_monitor_timer.stop()
                
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