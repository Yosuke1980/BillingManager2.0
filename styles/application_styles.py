"""アプリケーションのスタイル管理

このモジュールはアプリケーション全体のスタイルシートとDPI設定を管理します。
"""
import platform
from PyQt5.QtWidgets import QApplication
from utils import log_message


class ApplicationStyleManager:
    """アプリケーションスタイルマネージャー

    DPI検出とスタイルシート生成を担当します。
    """

    def __init__(self):
        """初期化"""
        self.base_font_size = self.calculate_optimal_font_size()
        self.title_font_size = max(14, int(self.base_font_size * 1.2))
        self.small_font_size = max(10, int(self.base_font_size * 0.85))

    @staticmethod
    def calculate_optimal_font_size():
        """システムのDPI設定に基づいて最適なフォントサイズを計算

        Returns:
            int: 計算されたフォントサイズ (12-18の範囲)
        """
        try:
            app = QApplication.instance()
            if app is None:
                return 13

            screen = app.primaryScreen()
            if screen is None:
                return 13

            dpi = screen.logicalDotsPerInch()
            scale_factor = dpi / 96.0

            # macOS向けの補正（DPIが低い環境でも適切なサイズを確保）
            if platform.system() == "Darwin":
                if scale_factor < 1.0:
                    scale_factor = 1.0  # 最低でも1.0にする

            # Windows向けの追加補正
            if platform.system() == "Windows":
                scale_factor *= 1.05
                device_pixel_ratio = screen.devicePixelRatio()
                if device_pixel_ratio > 1.0:
                    scale_factor *= device_pixel_ratio * 0.8

            base_size = 13  # macOS/Windows標準に合わせて13pxに変更
            calculated_size = int(base_size * scale_factor)

            # 可読性を確保するための最小・最大値
            min_size = 12  # 最小値を12pxに引き上げ
            max_size = 18
            font_size = max(min_size, min(max_size, calculated_size))

            log_message(f"フォントサイズ計算: DPI={dpi}, scale={scale_factor:.2f}, 結果={font_size}px")
            return font_size

        except Exception as e:
            log_message(f"フォントサイズ計算でエラー: {e}")
            return 13

    def generate_stylesheet(self):
        """アプリケーション全体のスタイルシートを生成

        Returns:
            str: 完全なCSSスタイルシート
        """
        font_size = self.base_font_size
        title_font_size = self.title_font_size
        small_font_size = self.small_font_size

        # サイズ計算（余白を縮小）
        button_padding_v = max(4, int(font_size * 0.3))
        button_padding_h = max(10, int(font_size * 0.7))
        button_min_height = max(28, int(font_size * 2.2))
        button_min_width = max(80, int(font_size * 6))

        input_padding = max(4, int(font_size * 0.3))
        input_min_height = max(26, int(font_size * 1.9))
        input_min_width = max(120, int(font_size * 8))

        splitter_width = max(6, int(font_size * 0.4))

        return f"""
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
                margin-top: 6px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                font-size: {font_size}px;
                font-weight: bold;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
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
                padding: 3px;
                min-height: {int(font_size * 1.5)}px;
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
                padding: 6px;
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
                padding: 6px 12px;
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
                spacing: 6px;
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
