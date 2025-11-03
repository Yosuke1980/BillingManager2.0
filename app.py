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
from order_management.database_manager import OrderManagementDB
from payment_tab import PaymentTab
from payment_order_check_tab import PaymentOrderCheckTab
from order_management.ui.order_contract_widget import OrderContractWidget
from master_management_tab import MasterManagementTab
from data_management_tab import DataManagementTab
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

        # 発注管理データベースの初期化
        self.order_db = OrderManagementDB()

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
        # メインタブ1: 支払い情報（毎日使う）
        self.payment_tab = PaymentTab(tab_control, self)
        tab_control.addTab(self.payment_tab, self.config.TAB_NAMES['payment'])

        # メインタブ2: 支払い・発注チェック（毎日使う）
        self.payment_order_check_tab = PaymentOrderCheckTab()
        self.payment_check_tab_index = tab_control.addTab(self.payment_order_check_tab, self.config.TAB_NAMES['payment_order_check'])

        # メインタブ3: 発注管理（旧「発注書マスタ」を独立）
        self.order_contract_widget = OrderContractWidget()
        self.order_management_tab_index = tab_control.addTab(self.order_contract_widget, self.config.TAB_NAMES['order_management'])

        # メインタブ4: マスター管理（新設）
        self.master_management_tab = MasterManagementTab(tab_control, self)
        tab_control.addTab(self.master_management_tab, self.config.TAB_NAMES['master_management'])

        # メインタブ5: データ管理（たまに使う、サブタブあり）
        self.data_management_tab = DataManagementTab(tab_control, self)
        tab_control.addTab(self.data_management_tab, self.config.TAB_NAMES['data_management'])

        # シグナル接続：発注追加時に発注書マスタを更新
        self.data_management_tab.order_check_tab.order_added.connect(
            self.order_contract_widget.load_contracts
        )

        # Phase 4.2: データ更新時にバッジを更新するシグナル接続
        self.data_management_tab.order_check_tab.order_added.connect(
            self.update_tab_badges
        )

    def _load_initial_data(self):
        """初期データの読み込み"""
        self.import_latest_csv()
        self.payment_tab.refresh_data()
        # データ管理タブ内のサブタブのデータを更新
        self.data_management_tab.expense_tab.refresh_data()
        self.data_management_tab.master_tab.refresh_data()

        # 起動時アラートとバッジ更新を統合（パフォーマンス最適化）
        self._check_and_update_urgent_status()

    def _check_and_update_urgent_status(self):
        """起動時アラートとバッジ更新を統合（パフォーマンス最適化版）

        データ取得を1回だけ行い、アラート表示とバッジ更新の両方で使用することで
        起動時のパフォーマンスを向上させる。
        """
        try:
            # データを一度だけ取得
            contracts = self.order_db.get_order_contracts()
            current_month = datetime.now().strftime("%Y-%m")
            payment_check_data = self.db_manager.check_payments_against_schedule(current_month)

            # 発注契約の緊急件数を計算
            urgent_contracts = 0
            for contract in contracts:
                end_date_str = contract[7] if len(contract) > 7 else None
                if end_date_str:
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                        days_until_expiry = (end_date - datetime.now()).days
                        if days_until_expiry <= 7 or days_until_expiry < 0:
                            urgent_contracts += 1
                    except:
                        pass

            # 支払いチェックの問題件数を計算
            unpaid_count = sum(1 for item in payment_check_data if item['payment_status'] != "✓")

            # 1. 緊急アラート表示
            if urgent_contracts > 0 or unpaid_count > 0:
                alert_message = "🚨 <b>緊急対応が必要な項目があります</b><br><br>"

                if urgent_contracts > 0:
                    alert_message += f"📝 <b>発注契約:</b> {urgent_contracts}件（期限切れ・間近）<br>"

                if unpaid_count > 0:
                    alert_message += f"💰 <b>支払未完了:</b> {unpaid_count}件<br>"

                alert_message += "<br>詳細は各タブで確認してください。"

                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("起動時アラート")
                msg_box.setText(alert_message)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec_()

            # 2. タブバッジを更新
            self._update_tab_badges_with_counts(urgent_contracts, unpaid_count)

        except Exception as e:
            log_message(f"起動時チェックでエラー: {e}")

    def _update_tab_badges_with_counts(self, urgent_contracts: int, unpaid_count: int):
        """タブタイトルのバッジを更新（計算済みの件数を使用）

        Args:
            urgent_contracts: 緊急対応が必要な発注契約の件数
            unpaid_count: 支払未完了の件数
        """
        try:
            base_payment_check_title = self.config.TAB_NAMES['payment_order_check']
            base_order_management_title = self.config.TAB_NAMES['order_management']

            # 支払いチェックタブのバッジ
            if unpaid_count > 0:
                self.tab_control.setTabText(
                    self.payment_check_tab_index,
                    f"{base_payment_check_title} 🚨 {unpaid_count}"
                )
            else:
                self.tab_control.setTabText(self.payment_check_tab_index, base_payment_check_title)

            # 発注管理タブのバッジ
            if urgent_contracts > 0:
                self.tab_control.setTabText(
                    self.order_management_tab_index,
                    f"{base_order_management_title} ⚠️ {urgent_contracts}"
                )
            else:
                self.tab_control.setTabText(self.order_management_tab_index, base_order_management_title)

        except Exception as e:
            log_message(f"タブバッジ更新でエラー: {e}")

    def update_tab_badges(self):
        """タブバッジを更新（外部から呼ばれる用）

        データ更新時などに呼ばれる。起動時は _check_and_update_urgent_status() を使用。
        """
        try:
            # データを取得して件数を計算
            contracts = self.order_db.get_order_contracts()
            urgent_contracts = 0
            for contract in contracts:
                end_date_str = contract[7] if len(contract) > 7 else None
                if end_date_str:
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                        days_until_expiry = (end_date - datetime.now()).days
                        if days_until_expiry <= 7 or days_until_expiry < 0:
                            urgent_contracts += 1
                    except:
                        pass

            current_month = datetime.now().strftime("%Y-%m")
            payment_check_data = self.db_manager.check_payments_against_schedule(current_month)
            unpaid_count = sum(1 for item in payment_check_data if item['payment_status'] != "✓")

            # バッジを更新
            self._update_tab_badges_with_counts(urgent_contracts, unpaid_count)

        except Exception as e:
            log_message(f"タブバッジ更新でエラー: {e}")

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
            # 上書き/追記の選択ダイアログを表示
            reply = QMessageBox.question(
                self,
                'インポート方法の選択',
                '既存のデータをどうしますか？\n\n'
                '「はい」: 上書き（既存データを削除して新規データのみ）\n'
                '「いいえ」: 追記（既存データを保持して追加）',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Cancel:
                return False

            overwrite = (reply == QMessageBox.Yes)

            # CSVファイルの情報を更新
            file_size = os.path.getsize(csv_file) // 1024
            file_name = os.path.basename(csv_file)
            self.payment_tab.csv_info_label.setText(f"CSV: {file_name} ({file_size}KB)")

            # データをインポート
            row_count = self.db_manager.import_csv_data(csv_file, self.header_mapping, overwrite)
            mode_text = "上書きで" if overwrite else "追記で"
            log_message(f"{row_count}件のデータをCSVから{mode_text}インポートしました: {file_name}")

            # データを表示
            self.payment_tab.refresh_data()
            self.status_label.setText(f"{row_count}件のデータをCSVから{mode_text}インポートしました")

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
                row_count = window.db_manager.import_csv_data(args.import_csv, window.header_mapping, overwrite=True)
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
