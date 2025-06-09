import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
from datetime import datetime

from database import DatabaseManager
from payment_tab import PaymentTab
from expense_tab import ExpenseTab
from master_tab import MasterTab
from utils import get_latest_csv_file, log_message


class RadioBillingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ラジオ局支払い・費用管理システム")
        # ウィンドウサイズを大きくする
        self.setGeometry(100, 100, 1400, 1600)  # x, y, width, height を調整

        # CSVデータフォルダを相対パスに変更
        self.csv_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data"
        )

        self.header_mapping = {
            "おもて情報.件名": "subject",
            "明細情報.明細項目": "project_name",
            "おもて情報.請求元": "payee",
            "おもて情報.支払先コード": "payee_code",
            "明細情報.金額": "amount",
            "おもて情報.自社支払期限": "payment_date",
            "状態": "status",
        }

        # メインウィジェットの作成
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 上部フレーム - 説明ラベル
        label_frame = QFrame()
        label_layout = QVBoxLayout(label_frame)

        title_label = QLabel("支払い・費用データ管理システム")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("", 14, QFont.Bold))
        label_layout.addWidget(title_label)

        main_layout.addWidget(label_frame)

        # タブコントロールの作成
        self.tab_control = QTabWidget()
        self.tab_control.setDocumentMode(True)  # よりモダンな外観にする
        self.tab_control.setTabPosition(QTabWidget.North)  # タブの位置を上部に
        self.tab_control.setMovable(False)  # タブの移動を禁止
        self.tab_control.setTabsClosable(False)  # 閉じるボタンなし

        # タブバーに余分なスペースを確保
        self.tab_control.tabBar().setExpanding(False)  # タブが等幅にならないようにする
        self.tab_control.tabBar().setElideMode(Qt.ElideNone)  # テキストの省略を無効化

        main_layout.addWidget(self.tab_control)

        # ステータスフレーム
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 5, 0, 0)

        self.status_label = QLabel("読み込み中...")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setFont(QFont("", 10))
        status_layout.addWidget(self.status_label)

        # 余白を追加
        status_layout.addStretch()

        # 最後に更新表示用
        self.last_update_label = QLabel("")
        self.last_update_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.last_update_label.setFont(QFont("", 10))
        status_layout.addWidget(self.last_update_label)

        main_layout.addWidget(status_frame)

        # データベースマネージャーの初期化
        self.db_manager = DatabaseManager()
        self.db_manager.init_db()

        # タブの作成
        self.payment_tab = PaymentTab(self.tab_control, self)
        self.tab_control.addTab(self.payment_tab, "支払い情報 (閲覧専用)")

        self.expense_tab = ExpenseTab(self.tab_control, self)
        self.tab_control.addTab(self.expense_tab, "費用管理")

        self.master_tab = MasterTab(self.tab_control, self)
        self.tab_control.addTab(self.master_tab, "費用マスター")

        # データを読み込み
        self.import_latest_csv()
        self.expense_tab.refresh_data()
        self.master_tab.refresh_data()

        self.apply_stylesheet()

    def apply_stylesheet(self):
        style = """
            QTreeWidget {
                font-size: 9pt;
                gridline-color: #d0d0d0;
                selection-background-color: #CDEFFF;
                /* alternate-background-colorを削除またはコメントアウト */
                /* alternate-background-color: #f8f8f8; */
            }
            QTreeWidget::item {
                padding: 2px;
                border-bottom: 1px solid #e8e8e8;
                height: 20px;
            }
            QTreeWidget::item:selected {
                background-color: #CDEFFF !important;
                color: #000000;
            }
            QTreeWidget::header {
                font-size: 9pt;
                font-weight: bold;
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 3px;
            }
            QGroupBox {
                font-size: 10pt;
                border: 2px solid #a0a0a0;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                background-color: #fafafa;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                font-weight: bold;
                color: #2c3e50;
                background-color: white;
            }
            QPushButton {
                font-size: 9pt;
                padding: 8px 16px;
                min-height: 18px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
                border-color: #85929e;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
            QLabel {
                font-size: 9pt;
            }
            QLineEdit {
                font-size: 9pt;
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QComboBox {
                font-size: 9pt;
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QDateEdit {
                font-size: 9pt;
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
            }
            QDateEdit:focus {
                border-color: #3498db;
            }
            QFrame {
                border: 1px solid #e8e8e8;
                border-radius: 4px;
                background-color: white;
                margin: 2px;
            }
            QTabBar::tab {
                font-size: 11pt;
                font-weight: bold;
                padding-top: 18px;      
                padding-bottom: 18px;   
                padding-left: 25px;
                padding-right: 25px;
                min-width: 220px;  
                border: 1px solid #C4C4C3;
                border-bottom-color: transparent;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                background-color: #F0F0F0;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom-color: #FFFFFF;
                color: #0066CC;
            }
            QTabBar::tab:hover {
                background-color: #E8E8E8;
            }
            QTabWidget::pane {
                border: 1px solid gray;
                border-radius: 3px;
            }
        """
        self.setStyleSheet(style)

    def import_latest_csv(self):
        """最新のCSVファイルからデータをインポート"""
        csv_file = get_latest_csv_file(self.csv_folder)

        if not csv_file:
            self.status_label.setText("CSVファイルが見つかりません")
            return False

        try:
            # CSVファイルの情報を更新
            file_size = os.path.getsize(csv_file) // 1024  # KBに変換
            file_time = datetime.fromtimestamp(os.path.getmtime(csv_file)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            file_name = os.path.basename(csv_file)

            self.payment_tab.csv_info_label.setText(f"CSV: {file_name} ({file_size}KB)")

            # データをインポート
            row_count = self.db_manager.import_csv_data(csv_file, self.header_mapping)

            log_message(
                f"{row_count}件のデータをCSVからインポートしました: {file_name}"
            )

            # データを表示
            self.payment_tab.refresh_data()
            self.status_label.setText(
                f"{row_count}件のデータをCSVからインポートしました"
            )

            return True

        except Exception as e:
            log_message(f"CSVファイルのインポート中にエラー: {e}")
            import traceback

            log_message(traceback.format_exc())
            self.status_label.setText(f"CSVファイルの読み込みに失敗しました: {str(e)}")
            return False

    def reload_data(self):
        """データの再読み込み"""
        success = self.import_latest_csv()
        if success:
            self.status_label.setText("データを再読み込みしました")
        else:
            self.status_label.setText("データの再読み込みに失敗しました")


def main():
    app = QApplication(sys.argv)
    window = RadioBillingApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# ファイル終了確認用のコメント - app.py完了
