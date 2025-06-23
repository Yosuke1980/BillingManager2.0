import sys
import platform
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
from PyQt5.QtGui import QFont, QFontMetrics
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
        
        # フォントサイズを動的に計算
        self.base_font_size = self.calculate_optimal_font_size()
        
        # UI要素用のサイズも計算
        self.title_font_size = max(10, int(self.base_font_size * 1.1))
        self.small_font_size = max(9, int(self.base_font_size * 0.9))
        
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

        self.apply_stylesheet()  # 基本的な視認性を確保
    
    def calculate_optimal_font_size(self):
        """システムのDPI設定に基づいて最適なフォントサイズを計算"""
        try:
            # アプリケーションのインスタンスを取得
            app = QApplication.instance()
            if app is None:
                return 13  # デフォルト値
            
            # プライマリスクリーンのDPIを取得
            screen = app.primaryScreen()
            if screen is None:
                return 13
                
            dpi = screen.logicalDotsPerInch()
            
            # 基準DPI（96 DPI）に対する倍率を計算
            scale_factor = dpi / 96.0
            
            # Windowsの場合は追加の補正を適用
            if platform.system() == "Windows":
                # Windows環境では文字が小さく見える傾向があるため補正（微調整）
                scale_factor *= 1.05
                
                # Windows DPIスケーリング設定も考慮
                device_pixel_ratio = screen.devicePixelRatio()
                if device_pixel_ratio > 1.0:
                    scale_factor *= device_pixel_ratio * 0.8  # 過度な拡大を抑制
            
            # 基本フォントサイズ（11px）にスケールファクターを適用（全体縮小）
            base_size = 11
            calculated_size = int(base_size * scale_factor)
            
            # 最小・最大値を設定（可読性を確保）
            min_size = 9
            max_size = 20
            font_size = max(min_size, min(max_size, calculated_size))
            
            log_message(f"フォントサイズ計算: DPI={dpi}, scale={scale_factor:.2f}, 結果={font_size}px")
            return font_size
            
        except Exception as e:
            log_message(f"フォントサイズ計算でエラー: {e}")
            return 13  # エラー時はデフォルト値

    def apply_stylesheet(self):
        # PC標準の配色でシンプルに（バランス修正版）
        font_size = self.base_font_size
        button_padding_v = max(3, int(font_size * 0.3))
        button_padding_h = max(8, int(font_size * 0.8))
        button_min_height = max(24, int(font_size * 2.2))
        input_padding = max(3, int(font_size * 0.3))
        input_min_height = button_min_height  # 統一
        
        style = f"""
            QTreeWidget {{
                font-size: {font_size}px;
                gridline-color: #d0d0d0;
                alternate-background-color: #f5f5f5;
            }}
            QTreeWidget::item:selected {{
                background-color: #3399ff;
                color: white;
            }}
            QLabel {{
                font-size: {font_size}px;
            }}
            QPushButton {{
                font-size: {font_size}px;
                padding: {button_padding_v}px {button_padding_h}px;
                min-height: {button_min_height}px;
                min-width: {int(font_size * 3)}px;
            }}
            QLineEdit {{
                font-size: {font_size}px;
                padding: {input_padding}px;
                min-height: {input_min_height}px;
            }}
            QComboBox {{
                font-size: {font_size}px;
                padding: {input_padding}px;
                min-height: {input_min_height}px;
                min-width: {int(font_size * 4)}px;
            }}
            QDateEdit {{
                font-size: {font_size}px;
                padding: {input_padding}px;
                min-height: {input_min_height}px;
                min-width: {int(font_size * 6)}px;
            }}
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
    
    # Windows高DPI対応（強化版）
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Windowsでの追加DPI対応設定
    if platform.system() == "Windows":
        try:
            # Qt 5.14以降で利用可能
            app.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)
            # スケーリング動作を改善
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass  # 古いバージョンでは無視
    
    window = RadioBillingApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# ファイル終了確認用のコメント - app.py完了
