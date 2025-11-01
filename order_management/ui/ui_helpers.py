"""UI共通ヘルパー関数（Mac対応）

このモジュールはMacで背景と文字色が同じになる問題を防ぐため、
全てのUIコンポーネントに明示的な色設定を提供します。
"""
from PyQt5.QtWidgets import QTableWidgetItem, QListWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


# 標準色定義（アプリケーション全体で統一）
TEXT_COLOR = QColor("#2c3e50")  # 濃いグレー（読みやすい）
BACKGROUND_COLOR = "white"
SELECTION_BG_COLOR = "#007bff"  # 青
SELECTION_TEXT_COLOR = "white"
HOVER_BG_COLOR = "#e3f2fd"  # 薄い青


def create_readonly_table_item(text: str) -> QTableWidgetItem:
    """読み取り専用テーブルアイテムを作成（色設定済み）

    Args:
        text: 表示テキスト

    Returns:
        QTableWidgetItem: 色設定済みの読み取り専用アイテム
    """
    item = QTableWidgetItem(str(text) if text is not None else "")
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    item.setForeground(TEXT_COLOR)
    return item


def create_list_item(text: str, data=None) -> QListWidgetItem:
    """リストアイテムを作成（色設定済み）

    Args:
        text: 表示テキスト
        data: UserRoleに設定するデータ（任意）

    Returns:
        QListWidgetItem: 色設定済みのリストアイテム
    """
    item = QListWidgetItem(str(text) if text is not None else "")
    item.setForeground(TEXT_COLOR)
    if data is not None:
        item.setData(Qt.UserRole, data)
    return item


def apply_mac_safe_style(widget, additional_style: str = ""):
    """Mac対応の安全なスタイルを適用

    Args:
        widget: スタイルを適用するウィジェット
        additional_style: 追加のスタイル文字列（任意）
    """
    base_style = f"background-color: {BACKGROUND_COLOR}; color: #2c3e50;"
    if additional_style:
        style = base_style + " " + additional_style
    else:
        style = base_style
    widget.setStyleSheet(style)


def set_table_item_color(item: QTableWidgetItem):
    """テーブルアイテムに標準色を設定

    Args:
        item: 色を設定するテーブルアイテム
    """
    if item:
        item.setForeground(TEXT_COLOR)


def set_list_item_color(item: QListWidgetItem):
    """リストアイテムに標準色を設定

    Args:
        item: 色を設定するリストアイテム
    """
    if item:
        item.setForeground(TEXT_COLOR)
