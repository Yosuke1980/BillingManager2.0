"""ラジオ局支払い・費用管理システム

メインアプリケーションモジュール
"""
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config import AppConfig
from styles import ApplicationStyleManager
from ui import MenuBuilder, ToolbarBuilder, StatusBarManager
from database import DatabaseManager
from payment_tab import PaymentTab
from expense_tab import ExpenseTab
from master_tab import MasterTab
from order_management_tab import OrderManagementTab
from order_payment_reconciliation_tab import OrderPaymentReconciliationTab
from order_check_tab import OrderCheckTab
from utils import get_latest_csv_file, log_message


class RadioBillingApp(QMainWindow):
    """ラジオ局支払い・費用管理システムのメインウィンドウクラス"""

    def __init__(self):
        super().__init__()

        # 設定の初期化
        self.config = AppConfig()
        self.style_manager = ApplicationStyleManager()

        # フォントサイズを公開（既存タブが参照するため）
        self.base_font_size = self.style_manager.base_font_size
        self.title_font_size = self.style_manager.title_font_size
        self.small_font_size = self.style_manager.small_font_size

        # ウィンドウの基本設定
        self._setup_window()

        # CSVデータフォルダ設定
        self.csv_folder = self.config.get_data_folder()
        self.header_mapping = self.config.HEADER_MAPPING

        # データベースマネージャーの初期化
        self.db_manager = DatabaseManager()
        self.db_manager.init_db()

        # UIの構築
        self._setup_ui()

        # データの初期ロード
        self._load_initial_data()

    def _setup_window(self):
        """ウィンドウの基本設定"""
        self.setWindowTitle(self.config.WINDOW_TITLE)
        x, y, width, height = self.config.WINDOW_GEOMETRY
        self.setGeometry(x, y, width, height)

    def _setup_ui(self):
        """UIコンポーネントのセットアップ"""
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # タイトルラベル
        main_layout.addWidget(self._create_title_label())

        # ステータスバー（タブより先に初期化）
        self.status_bar_manager = StatusBarManager()
        self.status_label = self.status_bar_manager.get_status_label()
        self.last_update_label = self.status_bar_manager.get_last_update_label()

        # タブコントロール
        self.tab_control = self._create_tab_control()
        main_layout.addWidget(self.tab_control)

        # ステータスバーフレームを追加
        main_layout.addWidget(self.status_bar_manager.get_frame())

        # メニューとツールバー
        MenuBuilder.create_menu_bar(self)
        ToolbarBuilder.create_toolbar(self)

        # スタイルシート適用
        self.setStyleSheet(self.style_manager.generate_stylesheet())

    def _create_title_label(self):
        """タイトルラベルを作成"""
        label_frame = QFrame()
        label_layout = QVBoxLayout(label_frame)

        title_label = QLabel(self.config.TITLE_LABEL_TEXT)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("", self.config.TITLE_FONT_SIZE, QFont.Bold))
        label_layout.addWidget(title_label)

        return label_frame

    def _create_tab_control(self):
        """タブコントロールを作成"""
        tab_control = QTabWidget()
        tab_control.setDocumentMode(True)
        tab_control.setTabPosition(QTabWidget.North)
        tab_control.setMovable(False)
        tab_control.setTabsClosable(False)
        tab_control.tabBar().setExpanding(False)
        tab_control.tabBar().setElideMode(Qt.ElideNone)

        # タブの追加
        self._add_tabs(tab_control)

        return tab_control

    def _add_tabs(self, tab_control):
        """各タブを追加"""
        # 支払いタブ
        self.payment_tab = PaymentTab(tab_control, self)
        tab_control.addTab(self.payment_tab, self.config.TAB_NAMES['payment'])

        # 費用管理タブ
        self.expense_tab = ExpenseTab(tab_control, self)
        tab_control.addTab(self.expense_tab, self.config.TAB_NAMES['expense'])

        # 費用マスタータブ
        self.master_tab = MasterTab(tab_control, self)
        tab_control.addTab(self.master_tab, self.config.TAB_NAMES['master'])

        # 発注管理タブ
        self.order_management_tab = OrderManagementTab(tab_control, self)
        tab_control.addTab(self.order_management_tab, self.config.TAB_NAMES['order_management'])

        # 発注チェックタブ
        self.order_check_tab = OrderCheckTab()
        tab_control.addTab(self.order_check_tab, "発注チェック")

        # シグナル接続：発注追加時に発注書マスタを更新
        self.order_check_tab.order_added.connect(
            self.order_management_tab.order_contract_widget.load_contracts
        )

        # 発注・支払照合タブ
        self.reconciliation_tab = OrderPaymentReconciliationTab()
        tab_control.addTab(self.reconciliation_tab, "発注・支払照合")

    def _load_initial_data(self):
        """初期データの読み込み"""
        self.import_latest_csv()
        self.payment_tab.refresh_data()
        self.expense_tab.refresh_data()
        self.master_tab.refresh_data()

    # ========================================
    # データ管理メソッド
    # ========================================

    def import_latest_csv(self):
        """最新のCSVファイルからデータをインポート"""
        csv_file = get_latest_csv_file(self.csv_folder)

        if not csv_file:
            self.status_label.setText(self.config.STATUS_NO_CSV)
            return False

        try:
            # CSVファイルの情報を更新
            file_size = os.path.getsize(csv_file) // 1024
            file_name = os.path.basename(csv_file)
            self.payment_tab.csv_info_label.setText(f"CSV: {file_name} ({file_size}KB)")

            # データをインポート
            row_count = self.db_manager.import_csv_data(csv_file, self.header_mapping)
            log_message(f"{row_count}件のデータをCSVからインポートしました: {file_name}")

            # データを表示
            self.payment_tab.refresh_data()
            self.status_label.setText(f"{row_count}件のデータをCSVからインポートしました")

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
            self.status_label.setText(self.config.STATUS_RELOAD_SUCCESS)
        else:
            self.status_label.setText(self.config.STATUS_RELOAD_FAILED)

    # ========================================
    # メニュー・ツールバーアクション実装
    # ========================================

    def save_current(self):
        """現在のタブの内容を保存"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'save_direct_edit'):
            # Master Tabの保存
            current_tab.save_direct_edit()
        elif hasattr(current_tab, 'save_payment_details'):
            # Project Filter Tabの保存
            current_tab.save_payment_details()
        else:
            QMessageBox.information(self, '保存', '現在のタブでは保存機能は利用できません。')

    def export_csv(self):
        """CSV出力処理"""
        current_tab = self.tab_control.currentWidget()

        # Master Tabの場合
        if hasattr(current_tab, 'export_to_csv'):
            current_tab.export_to_csv()
        # その他のタブで export_csv メソッドを持つ場合
        elif hasattr(current_tab, 'export_csv'):
            current_tab.export_csv()
        else:
            QMessageBox.information(self, 'CSV出力', '現在のタブではCSV出力は利用できません。')

    def import_csv(self):
        """CSVインポート処理"""
        current_tab = self.tab_control.currentWidget()

        # Master Tabの場合
        if hasattr(current_tab, 'import_from_csv'):
            current_tab.import_from_csv()
        else:
            QMessageBox.information(self, 'CSVインポート', '現在のタブではCSVインポートは利用できません。')

    def create_new_entry(self):
        """新規エントリ作成"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'create_new_entry'):
            current_tab.create_new_entry()
        else:
            QMessageBox.information(self, '新規作成', '現在のタブでは新規作成は利用できません。')

    def delete_selected(self):
        """選択項目の削除"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'delete_selected'):
            current_tab.delete_selected()
        else:
            QMessageBox.information(self, '削除', '現在のタブでは削除は利用できません。')

    def show_search(self):
        """検索機能の表示"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'show_search'):
            current_tab.show_search()
        else:
            QMessageBox.information(self, '検索', '現在のタブでは検索は利用できません。')

    def reset_filters(self):
        """フィルターのリセット"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'reset_filters'):
            current_tab.reset_filters()
        else:
            QMessageBox.information(self, 'リセット', '現在のタブではリセットは利用できません。')

    def toggle_filter_panel(self, checked):
        """フィルターパネルの表示/非表示切り替え"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'toggle_filter_panel'):
            current_tab.toggle_filter_panel(checked)

    def run_matching(self):
        """照合実行"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'run_matching'):
            current_tab.run_matching()
        else:
            QMessageBox.information(self, '照合実行', '現在のタブでは照合機能は利用できません。')

    def generate_master_data(self):
        """マスターデータ生成"""
        if hasattr(self.master_tab, 'generate_master_data'):
            self.master_tab.generate_master_data()
        else:
            QMessageBox.information(self, 'マスター生成', 'マスター生成機能は利用できません。')

    def show_about(self):
        """バージョン情報表示"""
        QMessageBox.about(self, 'バージョン情報', self.config.APP_DESCRIPTION)


def main():
    """メイン関数"""
    import argparse
    import platform

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description=AppConfig.WINDOW_TITLE)
    parser.add_argument('--import-csv', type=str, help='指定されたCSVファイルをインポートしてアプリを起動')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    # 高DPI対応
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Windows向けの追加設定
    if platform.system() == "Windows":
        try:
            app.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass

    window = RadioBillingApp()

    # コマンドライン引数でCSVファイルが指定された場合の処理
    if args.import_csv:
        try:
            if os.path.exists(args.import_csv):
                log_message(f"コマンドライン引数で指定されたCSVファイルをインポート: {args.import_csv}")
                row_count = window.db_manager.import_csv_data(args.import_csv, window.header_mapping)
                window.payment_tab.refresh_data()
                window.status_label.setText(f"{row_count}件のデータをCSVからインポートしました")

                # CSVファイル情報を更新
                file_size = os.path.getsize(args.import_csv) // 1024
                file_name = os.path.basename(args.import_csv)
                window.payment_tab.csv_info_label.setText(f"CSV: {file_name} ({file_size}KB)")

                log_message(f"CSVファイルのインポートが完了しました: {row_count}件")
            else:
                log_message(f"エラー: 指定されたCSVファイルが見つかりません: {args.import_csv}")
                window.status_label.setText(f"CSVファイルが見つかりません: {args.import_csv}")
        except Exception as e:
            log_message(f"CSVインポートエラー: {e}")
            window.status_label.setText(f"CSVインポートに失敗しました: {str(e)}")

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
