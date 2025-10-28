"""ツールバー構築モジュール

このモジュールはアプリケーションのツールバーを構築します。
"""
from PyQt5.QtWidgets import QAction


class ToolbarBuilder:
    """ツールバー構築クラス

    メインウィンドウのツールバーを構築し、よく使う機能へのショートカットを提供します。
    """

    @staticmethod
    def create_toolbar(main_window):
        """ツールバーを作成

        Args:
            main_window: メインウィンドウのインスタンス

        Returns:
            QToolBar: 作成されたツールバー
        """
        toolbar = main_window.addToolBar('メイン')
        toolbar.setMovable(False)

        # データ再読み込み
        reload_action = QAction('再読み込み', main_window)
        reload_action.setShortcut('F5')
        reload_action.triggered.connect(main_window.reload_data)
        toolbar.addAction(reload_action)

        toolbar.addSeparator()

        # 新規作成
        new_action = QAction('新規', main_window)
        new_action.triggered.connect(main_window.create_new_entry)
        toolbar.addAction(new_action)

        # 削除
        delete_action = QAction('削除', main_window)
        delete_action.triggered.connect(main_window.delete_selected)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        # 検索
        search_action = QAction('検索', main_window)
        search_action.triggered.connect(main_window.show_search)
        toolbar.addAction(search_action)

        # リセット
        reset_action = QAction('リセット', main_window)
        reset_action.triggered.connect(main_window.reset_filters)
        toolbar.addAction(reset_action)

        toolbar.addSeparator()

        # CSV出力
        export_action = QAction('CSV出力', main_window)
        export_action.triggered.connect(main_window.export_csv)
        toolbar.addAction(export_action)

        return toolbar
