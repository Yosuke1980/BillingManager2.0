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
        reload_action.setStatusTip('データを再読み込み')
        reload_action.triggered.connect(main_window.reload_data)
        toolbar.addAction(reload_action)

        toolbar.addSeparator()

        # 新規作成
        new_action = QAction('新規', main_window)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('新しいエントリを作成')
        new_action.triggered.connect(main_window.create_new_entry)
        toolbar.addAction(new_action)

        # 保存
        save_action = QAction('保存', main_window)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('変更を保存')
        save_action.triggered.connect(main_window.save_current)
        toolbar.addAction(save_action)

        # 削除
        delete_action = QAction('削除', main_window)
        delete_action.setShortcut('Delete')
        delete_action.setStatusTip('選択したエントリを削除')
        delete_action.triggered.connect(main_window.delete_selected)
        toolbar.addAction(delete_action)

        return toolbar
