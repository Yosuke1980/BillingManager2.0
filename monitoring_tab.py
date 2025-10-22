import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QLineEdit, QFormLayout, QSpinBox,
    QCheckBox, QFrame, QSplitter, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QIcon
from file_watcher_gui import FileWatcherManager


class MonitoringTab(QWidget):
    """ファイル監視機能のGUIタブ"""
    
    def __init__(self):
        super().__init__()
        self.file_watcher = FileWatcherManager()
        self.config_file = "monitoring_config.json"
        
        # ログ更新用タイマー
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.update_log_display)
        self.log_timer.start(1000)  # 1秒ごとに更新
        
        self.setup_ui()
        self.load_config()
        self.connect_signals()
        
    def setup_ui(self):
        """UIをセットアップ"""
        layout = QVBoxLayout()
        
        # ステータス表示
        self.create_status_section()
        layout.addWidget(self.status_group)
        
        # 制御ボタン
        self.create_control_section()
        layout.addWidget(self.control_group)
        
        # スプリッター（設定とログを横分割）
        splitter = QSplitter(Qt.Horizontal)
        
        # 設定パネル
        self.create_settings_section()
        splitter.addWidget(self.settings_group)
        
        # ログとファイル履歴
        self.create_log_section()
        splitter.addWidget(self.log_group)
        
        # スプリッターの比率設定
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        
    def create_status_section(self):
        """ステータス表示セクション"""
        self.status_group = QGroupBox("監視ステータス")
        layout = QHBoxLayout()
        
        # ステータスインジケータ
        self.status_label = QLabel("停止中")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #ff6b6b;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 監視フォルダ表示
        layout.addWidget(QLabel("監視フォルダ:"))
        self.folder_display = QLabel("data/")
        self.folder_display.setStyleSheet("font-family: monospace; background-color: #f0f0f0; padding: 4px;")
        layout.addWidget(self.folder_display)
        
        layout.addStretch()
        
        # 統計情報
        self.stats_label = QLabel("処理済み: 0件")
        layout.addWidget(self.stats_label)
        
        self.status_group.setLayout(layout)
        
    def create_control_section(self):
        """制御ボタンセクション"""
        self.control_group = QGroupBox("監視制御")
        layout = QHBoxLayout()
        
        self.start_btn = QPushButton("監視開始")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("監視停止")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("再起動")
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        self.restart_btn.clicked.connect(self.restart_monitoring)
        layout.addWidget(self.restart_btn)
        
        layout.addStretch()
        self.control_group.setLayout(layout)
        
    def create_settings_section(self):
        """設定パネル"""
        self.settings_group = QGroupBox("監視設定")
        layout = QFormLayout()
        
        # 監視フォルダ
        self.folder_edit = QLineEdit("data")
        layout.addRow("監視フォルダ:", self.folder_edit)
        
        # 監視間隔
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(1)
        self.interval_spin.setSuffix(" 秒")
        layout.addRow("監視間隔:", self.interval_spin)
        
        # 自動処理
        self.auto_process_check = QCheckBox("ファイル検出時に自動処理")
        self.auto_process_check.setChecked(True)
        layout.addRow(self.auto_process_check)
        
        # 重複処理防止
        self.duplicate_spin = QSpinBox()
        self.duplicate_spin.setRange(1, 300)
        self.duplicate_spin.setValue(5)
        self.duplicate_spin.setSuffix(" 秒")
        layout.addRow("重複処理防止間隔:", self.duplicate_spin)
        
        # 設定保存ボタン
        save_btn = QPushButton("設定保存")
        save_btn.clicked.connect(self.save_config)
        layout.addRow(save_btn)
        
        self.settings_group.setLayout(layout)
        
    def create_log_section(self):
        """ログとファイル履歴セクション"""
        self.log_group = QGroupBox("ログ・履歴")
        layout = QVBoxLayout()
        
        # ログ表示
        log_label = QLabel("監視ログ")
        log_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc;")
        layout.addWidget(self.log_text)
        
        # ファイル処理履歴
        history_label = QLabel("ファイル処理履歴")
        history_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["時刻", "ファイル名", "サイズ", "ステータス"])
        
        # テーブルの列幅を調整
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.history_table)
        
        # ログクリアボタン
        clear_btn = QPushButton("ログクリア")
        clear_btn.clicked.connect(self.clear_logs)
        layout.addWidget(clear_btn)
        
        self.log_group.setLayout(layout)
        
    def connect_signals(self):
        """シグナル接続"""
        self.file_watcher.status_changed.connect(self.update_status)
        self.file_watcher.file_processed.connect(self.add_file_history)
        self.file_watcher.log_message.connect(self.add_log_message)
        
    def start_monitoring(self):
        """監視開始"""
        folder_path = self.folder_edit.text().strip()
        if not folder_path:
            QMessageBox.warning(self, "エラー", "監視フォルダを指定してください")
            return
            
        config = {
            'folder_path': folder_path,
            'interval': self.interval_spin.value(),
            'auto_process': self.auto_process_check.isChecked(),
            'duplicate_interval': self.duplicate_spin.value()
        }
        
        success = self.file_watcher.start_monitoring(config)
        if success:
            self.add_log_message("監視を開始しました")
        else:
            QMessageBox.critical(self, "エラー", "監視の開始に失敗しました")
            
    def stop_monitoring(self):
        """監視停止"""
        self.file_watcher.stop_monitoring()
        self.add_log_message("監視を停止しました")
        
    def restart_monitoring(self):
        """監視再起動"""
        self.stop_monitoring()
        QTimer.singleShot(1000, self.start_monitoring)  # 1秒後に開始
        
    def update_status(self, is_running, stats):
        """ステータス更新"""
        if is_running:
            self.status_label.setText("監視中")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
        else:
            self.status_label.setText("停止中")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #ff6b6b;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            
        self.stats_label.setText(f"処理済み: {stats.get('processed_count', 0)}件")
        
    def add_file_history(self, file_info):
        """ファイル処理履歴を追加"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        self.history_table.setItem(row, 0, QTableWidgetItem(file_info['timestamp']))
        self.history_table.setItem(row, 1, QTableWidgetItem(file_info['filename']))
        self.history_table.setItem(row, 2, QTableWidgetItem(file_info['size']))
        self.history_table.setItem(row, 3, QTableWidgetItem(file_info['status']))
        
        # 最新の行を表示
        self.history_table.scrollToBottom()
        
    def add_log_message(self, message):
        """ログメッセージを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # 最新のログを表示
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def update_log_display(self):
        """ログ表示を更新（必要に応じて）"""
        pass
        
    def clear_logs(self):
        """ログと履歴をクリア"""
        self.log_text.clear()
        self.history_table.setRowCount(0)
        
    def save_config(self):
        """設定を保存"""
        config = {
            'folder_path': self.folder_edit.text(),
            'interval': self.interval_spin.value(),
            'auto_process': self.auto_process_check.isChecked(),
            'duplicate_interval': self.duplicate_spin.value()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "設定保存", "設定を保存しました")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました: {str(e)}")
            
    def load_config(self):
        """設定を読み込み"""
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.folder_edit.setText(config.get('folder_path', 'data'))
            self.interval_spin.setValue(config.get('interval', 1))
            self.auto_process_check.setChecked(config.get('auto_process', True))
            self.duplicate_spin.setValue(config.get('duplicate_interval', 5))
            
            self.folder_display.setText(config.get('folder_path', 'data/'))
            
        except Exception as e:
            self.add_log_message(f"設定の読み込みに失敗: {str(e)}")