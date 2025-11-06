"""改善された日付入力ウィジェット

QDateEditを継承し、使いやすい日付選択UIを提供します。
- 大きく見やすいカレンダー表示
- 日本語フォーマット（年月日+曜日）
- グリッド線表示で日付が見やすい
"""
from PyQt5.QtWidgets import QDateEdit, QCalendarWidget
from PyQt5.QtCore import QDate, Qt


class ImprovedDateEdit(QDateEdit):
    """改善された日付入力ウィジェット

    QDateEditの機能をすべて保持しつつ、以下の改善を提供：
    - カレンダーポップアップを大きく表示（400x300px）
    - 日本語表示フォーマット：「2025年01月15日 (水)」
    - グリッド線表示で日付の区切りが明確
    - 年月のナビゲーションボタンが大きく操作しやすい
    """

    def __init__(self, parent=None):
        """初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        # 日本語フォーマットで表示（年月日+曜日）
        self.setDisplayFormat("yyyy年MM月dd日 (ddd)")

        # カレンダーポップアップを有効化
        self.setCalendarPopup(True)

        # カスタムカレンダーウィジェットを作成・設定
        calendar = QCalendarWidget(self)

        # カレンダーのサイズを大きく設定（見やすく）
        calendar.setMinimumSize(400, 300)

        # グリッド線を表示（日付の区切りが明確に）
        calendar.setGridVisible(True)

        # 週の開始日を月曜日に設定（日本の一般的なカレンダー形式）
        calendar.setFirstDayOfWeek(Qt.Monday)

        # ナビゲーションバーを表示（年月の選択が容易に）
        calendar.setNavigationBarVisible(True)

        # 日付選択を有効化
        calendar.setSelectionMode(QCalendarWidget.SingleSelection)

        # カスタムカレンダーを適用
        self.setCalendarWidget(calendar)

        # キーボード入力を有効化（タイピングで日付入力可能）
        self.setKeyboardTracking(True)
