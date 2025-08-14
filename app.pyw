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
    QMenuBar,
    QToolBar,
    QAction,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
import os
from datetime import datetime

from database import DatabaseManager
from payment_tab import PaymentTab
from expense_tab import ExpenseTab
from master_tab import MasterTab
from project_filter_tab import ProjectFilterTab
from monitoring_tab import MonitoringTab
from utils import get_latest_csv_file, log_message


class RadioBillingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ラジオ局支払い・費用管理システム")
        
        # フォントサイズを動的に計算
        self.base_font_size = self.calculate_optimal_font_size()
        
        # UI要素用のサイズも計算
        self.title_font_size = max(14, int(self.base_font_size * 1.2))
        self.small_font_size = max(10, int(self.base_font_size * 0.85))
        
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

        # 案件絞込みタブを追加
        self.project_filter_tab = ProjectFilterTab(self.tab_control, self)
        self.tab_control.addTab(self.project_filter_tab, "案件絞込み・管理")

        # 監視機能タブを追加
        self.monitoring_tab = MonitoringTab()
        self.tab_control.addTab(self.monitoring_tab, "📁 ファイル監視")

        # メニューバーとツールバーを作成
        self.create_menu_bar()
        self.create_toolbar()
        
        # データを読み込み
        self.import_latest_csv()
        self.payment_tab.refresh_data()
        self.expense_tab.refresh_data()
        self.master_tab.refresh_data()

        self.apply_stylesheet()  # 基本的な視認性を確保
    
    def create_menu_bar(self):
        """メニューバーを作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('ファイル(&F)')
        
        # CSV読み込みアクション
        csv_import_action = QAction('CSV読み込み(&I)', self)
        csv_import_action.setShortcut('Ctrl+I')
        csv_import_action.setStatusTip('CSVファイルからデータを読み込み')
        csv_import_action.triggered.connect(self.import_latest_csv)
        file_menu.addAction(csv_import_action)
        
        # データ再読み込みアクション
        reload_action = QAction('データ再読み込み(&R)', self)
        reload_action.setShortcut('F5')
        reload_action.setStatusTip('データを再読み込み')
        reload_action.triggered.connect(self.reload_data)
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        # CSV出力アクション
        csv_export_action = QAction('CSV出力(&E)', self)
        csv_export_action.setShortcut('Ctrl+E')
        csv_export_action.setStatusTip('データをCSV形式で出力')
        csv_export_action.triggered.connect(self.export_csv)
        file_menu.addAction(csv_export_action)
        
        file_menu.addSeparator()
        
        # 終了アクション
        exit_action = QAction('終了(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('アプリケーションを終了')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 編集メニュー
        edit_menu = menubar.addMenu('編集(&E)')
        
        # 新規作成アクション
        new_action = QAction('新規作成(&N)', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('新しいエントリを作成')
        new_action.triggered.connect(self.create_new_entry)
        edit_menu.addAction(new_action)
        
        # 削除アクション
        delete_action = QAction('削除(&D)', self)
        delete_action.setShortcut('Delete')
        delete_action.setStatusTip('選択したエントリを削除')
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        # 検索アクション
        search_action = QAction('検索(&S)', self)
        search_action.setShortcut('Ctrl+F')
        search_action.setStatusTip('データを検索')
        search_action.triggered.connect(self.show_search)
        edit_menu.addAction(search_action)
        
        # リセットアクション
        reset_action = QAction('リセット(&C)', self)
        reset_action.setShortcut('Ctrl+R')
        reset_action.setStatusTip('フィルターをリセット')
        reset_action.triggered.connect(self.reset_filters)
        edit_menu.addAction(reset_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu('表示(&V)')
        
        # フィルター表示アクション
        filter_action = QAction('フィルター表示(&F)', self)
        filter_action.setCheckable(True)
        filter_action.setChecked(True)
        filter_action.setStatusTip('フィルターパネルの表示/非表示')
        filter_action.triggered.connect(self.toggle_filter_panel)
        view_menu.addAction(filter_action)
        
        # ツールメニュー
        tools_menu = menubar.addMenu('ツール(&T)')
        
        # 照合実行アクション
        match_action = QAction('照合実行(&M)', self)
        match_action.setShortcut('Ctrl+M')
        match_action.setStatusTip('データの照合を実行')
        match_action.triggered.connect(self.run_matching)
        tools_menu.addAction(match_action)
        
        # マスター生成アクション
        generate_master_action = QAction('マスター生成(&G)', self)
        generate_master_action.setStatusTip('マスターデータを生成')
        generate_master_action.triggered.connect(self.generate_master_data)
        tools_menu.addAction(generate_master_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu('ヘルプ(&H)')
        
        # バージョン情報アクション
        about_action = QAction('バージョン情報(&A)', self)
        about_action.setStatusTip('アプリケーションのバージョン情報')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """ツールバーを作成"""
        toolbar = self.addToolBar('メイン')
        toolbar.setMovable(False)
        
        # よく使う機能をツールバーに追加
        # データ再読み込み
        reload_action = QAction('再読み込み', self)
        reload_action.setShortcut('F5')
        reload_action.triggered.connect(self.reload_data)
        toolbar.addAction(reload_action)
        
        toolbar.addSeparator()
        
        # 新規作成
        new_action = QAction('新規', self)
        new_action.triggered.connect(self.create_new_entry)
        toolbar.addAction(new_action)
        
        # 削除
        delete_action = QAction('削除', self)
        delete_action.triggered.connect(self.delete_selected)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        # 検索
        search_action = QAction('検索', self)
        search_action.triggered.connect(self.show_search)
        toolbar.addAction(search_action)
        
        # リセット
        reset_action = QAction('リセット', self)
        reset_action.triggered.connect(self.reset_filters)
        toolbar.addAction(reset_action)
        
        toolbar.addSeparator()
        
        # CSV出力
        export_action = QAction('CSV出力', self)
        export_action.triggered.connect(self.export_csv)
        toolbar.addAction(export_action)
    
    # メニューとツールバーのアクション実装
    def export_csv(self):
        """CSV出力処理"""
        current_tab = self.tab_control.currentWidget()
        if hasattr(current_tab, 'export_csv'):
            current_tab.export_csv()
        else:
            QMessageBox.information(self, 'CSV出力', '現在のタブではCSV出力は利用できません。')
    
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
        QMessageBox.about(self, 'バージョン情報', 
                         'ラジオ局支払い・費用管理システム\n'
                         'Version 1.0\n\n'
                         'PyQt5ベースの業務管理アプリケーション')
    
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
            
            # 基本フォントサイズ（12px）にスケールファクターを適用
            base_size = 12
            calculated_size = int(base_size * scale_factor)
            
            # 最小・最大値を設定（可読性を確保）
            min_size = 10
            max_size = 18
            font_size = max(min_size, min(max_size, calculated_size))
            
            log_message(f"フォントサイズ計算: DPI={dpi}, scale={scale_factor:.2f}, 結果={font_size}px")
            return font_size
            
        except Exception as e:
            log_message(f"フォントサイズ計算でエラー: {e}")
            return 13  # エラー時はデフォルト値

    def apply_stylesheet(self):
        # 包括的なスタイルシート（改善版）
        font_size = self.base_font_size
        title_font_size = self.title_font_size
        small_font_size = self.small_font_size
        
        # サイズ計算の改善
        button_padding_v = max(6, int(font_size * 0.4))
        button_padding_h = max(12, int(font_size * 0.8))
        button_min_height = max(32, int(font_size * 2.4))
        button_min_width = max(80, int(font_size * 6))
        
        input_padding = max(4, int(font_size * 0.3))
        input_min_height = max(28, int(font_size * 2.0))
        input_min_width = max(120, int(font_size * 8))
        
        # スプリッターのサイズ
        splitter_width = max(6, int(font_size * 0.4))
        
        style = f"""
            /* 基本フォント設定 */
            QWidget {{
                font-family: "Segoe UI", "Meiryo", sans-serif;
                font-size: {font_size}px;
            }}
            
            /* ラベル */
            QLabel {{
                font-size: {font_size}px;
                color: #2c3e50;
            }}
            
            /* 小さなラベル */
            QLabel[small="true"] {{
                font-size: {small_font_size}px;
                color: #6c757d;
            }}
            
            /* タイトル用ラベル */
            QLabel[title="true"] {{
                font-size: {title_font_size}px;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            /* グループボックス */
            QGroupBox {{
                font-size: {font_size}px;
                font-weight: bold;
                color: #495057;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                font-size: {font_size}px;
                font-weight: bold;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }}
            
            /* ボタン */
            QPushButton {{
                font-size: {font_size}px;
                padding: {button_padding_v}px {button_padding_h}px;
                min-height: {button_min_height}px;
                min-width: {button_min_width}px;
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
                color: #495057;
            }}
            QPushButton:hover {{
                background-color: #e9ecef;
                border-color: #adb5bd;
            }}
            QPushButton:pressed {{
                background-color: #dee2e6;
                border-color: #6c757d;
            }}
            QPushButton:disabled {{
                background-color: #e9ecef;
                color: #6c757d;
                border-color: #dee2e6;
            }}
            
            /* 入力フィールド */
            QLineEdit {{
                font-size: {font_size}px;
                padding: {input_padding}px;
                min-height: {input_min_height}px;
                min-width: {input_min_width}px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: #495057;
            }}
            QLineEdit:focus {{
                border-color: #80bdff;
                outline: none;
            }}
            
            /* コンボボックス */
            QComboBox {{
                font-size: {font_size}px;
                padding: {input_padding}px;
                min-height: {input_min_height}px;
                min-width: {input_min_width}px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: #495057;
            }}
            QComboBox:focus {{
                border-color: #80bdff;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
                margin-right: 5px;
            }}
            
            /* 日付編集 */
            QDateEdit {{
                font-size: {font_size}px;
                padding: {input_padding}px;
                min-height: {input_min_height}px;
                min-width: {int(input_min_width * 1.2)}px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: #495057;
            }}
            
            /* ツリーウィジェット */
            QTreeWidget {{
                font-size: {font_size}px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
                selection-background-color: #007bff;
                selection-color: white;
            }}
            QTreeWidget::item {{
                padding: 4px;
                min-height: {int(font_size * 1.8)}px;
            }}
            QTreeWidget::item:selected {{
                background-color: #007bff;
                color: white;
            }}
            QTreeWidget::item:hover {{
                background-color: #e3f2fd;
            }}
            QTreeWidget::header {{
                font-size: {font_size}px;
                font-weight: bold;
                background-color: #f8f9fa;
                border: none;
                border-bottom: 2px solid #dee2e6;
            }}
            QTreeWidget::header::section {{
                padding: 8px;
                border-right: 1px solid #dee2e6;
                background-color: #f8f9fa;
            }}
            
            /* タブウィジェット */
            QTabWidget::pane {{
                border: 1px solid #dee2e6;
                background-color: white;
            }}
            QTabBar::tab {{
                font-size: {font_size}px;
                padding: 8px 16px;
                margin-right: 2px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 1px solid white;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
            }}
            
            /* フレーム */
            QFrame {{
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }}
            
            /* スプリッター */
            QSplitter::handle {{
                background-color: #dee2e6;
                width: {splitter_width}px;
                height: {splitter_width}px;
            }}
            QSplitter::handle:horizontal {{
                width: {splitter_width}px;
            }}
            QSplitter::handle:vertical {{
                height: {splitter_width}px;
            }}
            QSplitter::handle:hover {{
                background-color: #adb5bd;
            }}
            
            /* チェックボックス */
            QCheckBox {{
                font-size: {font_size}px;
                color: #495057;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: {int(font_size * 1.2)}px;
                height: {int(font_size * 1.2)}px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: #007bff;
                border-color: #007bff;
            }}
            
            /* スクロールエリア */
            QScrollArea {{
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }}
            
            /* スクロールバー */
            QScrollBar:vertical {{
                background-color: #f8f9fa;
                width: 16px;
                border-radius: 8px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #ced4da;
                border-radius: 8px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #adb5bd;
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
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='ラジオ局支払い・費用管理システム')
    parser.add_argument('--import-csv', type=str, help='指定されたCSVファイルをインポートしてアプリを起動')
    args = parser.parse_args()
    
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
    
    # コマンドライン引数でCSVファイルが指定された場合の処理
    if args.import_csv:
        try:
            if os.path.exists(args.import_csv):
                log_message(f"コマンドライン引数で指定されたCSVファイルをインポート: {args.import_csv}")
                # 指定されたCSVファイルをインポート
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