"""メニューバー構築モジュール

このモジュールはアプリケーションのメニューバーを構築します。
"""
from PyQt5.QtWidgets import QAction


class MenuBuilder:
    """メニューバー構築クラス

    メインウィンドウのメニューバーを構築し、アクションを設定します。
    """

    @staticmethod
    def create_menu_bar(main_window):
        """メニューバーを作成

        Args:
            main_window: メインウィンドウのインスタンス
        """
        menubar = main_window.menuBar()

        # ファイルメニュー
        MenuBuilder._create_file_menu(menubar, main_window)

        # 編集メニュー
        MenuBuilder._create_edit_menu(menubar, main_window)

        # 表示メニュー
        MenuBuilder._create_view_menu(menubar, main_window)

        # ツールメニュー
        MenuBuilder._create_tools_menu(menubar, main_window)

        # ヘルプメニュー
        MenuBuilder._create_help_menu(menubar, main_window)

    @staticmethod
    def _create_file_menu(menubar, main_window):
        """ファイルメニューを作成"""
        file_menu = menubar.addMenu('ファイル(&F)')

        # CSV読み込み
        csv_import_action = QAction('CSV読み込み(&I)', main_window)
        csv_import_action.setShortcut('Ctrl+I')
        csv_import_action.setStatusTip('CSVファイルからデータを読み込み')
        csv_import_action.triggered.connect(main_window.import_latest_csv)
        file_menu.addAction(csv_import_action)

        # データ再読み込み
        reload_action = QAction('データ再読み込み(&R)', main_window)
        reload_action.setShortcut('F5')
        reload_action.setStatusTip('データを再読み込み')
        reload_action.triggered.connect(main_window.reload_data)
        file_menu.addAction(reload_action)

        file_menu.addSeparator()

        # CSV出力
        csv_export_action = QAction('CSV出力(&E)', main_window)
        csv_export_action.setShortcut('Ctrl+E')
        csv_export_action.setStatusTip('データをCSV形式で出力')
        csv_export_action.triggered.connect(main_window.export_csv)
        file_menu.addAction(csv_export_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction('終了(&X)', main_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('アプリケーションを終了')
        exit_action.triggered.connect(main_window.close)
        file_menu.addAction(exit_action)

    @staticmethod
    def _create_edit_menu(menubar, main_window):
        """編集メニューを作成"""
        edit_menu = menubar.addMenu('編集(&E)')

        # 新規作成
        new_action = QAction('新規作成(&N)', main_window)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('新しいエントリを作成')
        new_action.triggered.connect(main_window.create_new_entry)
        edit_menu.addAction(new_action)

        # 削除
        delete_action = QAction('削除(&D)', main_window)
        delete_action.setShortcut('Delete')
        delete_action.setStatusTip('選択したエントリを削除')
        delete_action.triggered.connect(main_window.delete_selected)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        # 検索
        search_action = QAction('検索(&S)', main_window)
        search_action.setShortcut('Ctrl+F')
        search_action.setStatusTip('データを検索')
        search_action.triggered.connect(main_window.show_search)
        edit_menu.addAction(search_action)

        # リセット
        reset_action = QAction('リセット(&C)', main_window)
        reset_action.setShortcut('Ctrl+R')
        reset_action.setStatusTip('フィルターをリセット')
        reset_action.triggered.connect(main_window.reset_filters)
        edit_menu.addAction(reset_action)

    @staticmethod
    def _create_view_menu(menubar, main_window):
        """表示メニューを作成"""
        view_menu = menubar.addMenu('表示(&V)')

        # フィルター表示
        filter_action = QAction('フィルター表示(&F)', main_window)
        filter_action.setCheckable(True)
        filter_action.setChecked(True)
        filter_action.setStatusTip('フィルターパネルの表示/非表示')
        filter_action.triggered.connect(main_window.toggle_filter_panel)
        view_menu.addAction(filter_action)

    @staticmethod
    def _create_tools_menu(menubar, main_window):
        """ツールメニューを作成"""
        tools_menu = menubar.addMenu('ツール(&T)')

        # 照合実行
        match_action = QAction('照合実行(&M)', main_window)
        match_action.setShortcut('Ctrl+M')
        match_action.setStatusTip('データの照合を実行')
        match_action.triggered.connect(main_window.run_matching)
        tools_menu.addAction(match_action)

        # マスター生成
        generate_master_action = QAction('マスター生成(&G)', main_window)
        generate_master_action.setStatusTip('マスターデータを生成')
        generate_master_action.triggered.connect(main_window.generate_master_data)
        tools_menu.addAction(generate_master_action)

    @staticmethod
    def _create_help_menu(menubar, main_window):
        """ヘルプメニューを作成"""
        help_menu = menubar.addMenu('ヘルプ(&H)')

        # バージョン情報
        about_action = QAction('バージョン情報(&A)', main_window)
        about_action.setStatusTip('アプリケーションのバージョン情報')
        about_action.triggered.connect(main_window.show_about)
        help_menu.addAction(about_action)
