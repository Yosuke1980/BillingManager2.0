#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import sqlite3
import os

class BillingManagerTkDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ラジオ局支払い・費用管理システム (Tkinter版デモ)")
        self.root.geometry("1200x800")
        
        # macOSでのネイティブ外観を有効にする
        if tk.TkVersion >= 8.5:
            try:
                self.root.tk.call('tk', 'scaling', 1.0)
            except:
                pass
        
        self.create_widgets()
        self.load_sample_data()
    
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="支払い・費用データ管理システム", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タブ1: 支払い情報
        self.payment_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.payment_frame, text="支払い情報 (閲覧専用)")
        self.create_payment_tab()
        
        # タブ2: 費用管理
        self.expense_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expense_frame, text="費用管理")
        self.create_expense_tab()
        
        # タブ3: 費用マスター
        self.master_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.master_frame, text="費用マスター")
        self.create_master_tab()
        
        # ステータスバー
        self.status_label = ttk.Label(main_frame, text="Tkinter版デモ - ネイティブ外観テスト")
        self.status_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # グリッドの重みを設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def create_payment_tab(self):
        # 検索・フィルターフレーム
        filter_frame = ttk.LabelFrame(self.payment_frame, text="検索・フィルター", padding="10")
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(filter_frame, text="状態:").grid(row=0, column=0, padx=(0, 5))
        status_combo = ttk.Combobox(filter_frame, values=["全て", "照合済み", "処理済み", "処理中", "未処理"])
        status_combo.set("全て")
        status_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(filter_frame, text="検索:").grid(row=0, column=2, padx=(0, 5))
        search_entry = ttk.Entry(filter_frame, width=30)
        search_entry.grid(row=0, column=3, padx=(0, 10))
        
        search_btn = ttk.Button(filter_frame, text="検索")
        search_btn.grid(row=0, column=4)
        
        # データ表示用Treeview
        tree_frame = ttk.Frame(self.payment_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        columns = ("件名", "案件名", "支払い先", "コード", "金額", "支払日", "状態")
        self.payment_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # 列の設定
        for col in columns:
            self.payment_tree.heading(col, text=col)
            if col == "金額":
                self.payment_tree.column(col, width=100, anchor="e")
            elif col == "コード":
                self.payment_tree.column(col, width=80)
            else:
                self.payment_tree.column(col, width=150)
        
        # スクロールバー
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.payment_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.payment_tree.xview)
        self.payment_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.payment_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # グリッドの重みを設定
        self.payment_frame.columnconfigure(0, weight=1)
        self.payment_frame.rowconfigure(1, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
    
    def create_expense_tab(self):
        # ツールバー
        toolbar = ttk.Frame(self.expense_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Button(toolbar, text="新規追加").grid(row=0, column=0, padx=(0, 5))
        ttk.Button(toolbar, text="編集").grid(row=0, column=1, padx=(0, 5))
        ttk.Button(toolbar, text="削除").grid(row=0, column=2, padx=(0, 5))
        ttk.Button(toolbar, text="CSVエクスポート").grid(row=0, column=3, padx=(0, 20))
        
        ttk.Label(toolbar, text="月:").grid(row=0, column=4, padx=(0, 5))
        month_combo = ttk.Combobox(toolbar, values=["2025年06月", "2025年05月", "2025年04月"])
        month_combo.set("2025年06月")
        month_combo.grid(row=0, column=5)
        
        # データ表示
        columns = ("支払日", "支払い先", "案件名", "金額", "状態", "備考")
        self.expense_tree = ttk.Treeview(self.expense_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.expense_tree.heading(col, text=col)
            if col == "金額":
                self.expense_tree.column(col, width=100, anchor="e")
            else:
                self.expense_tree.column(col, width=150)
        
        self.expense_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.expense_frame.columnconfigure(0, weight=1)
        self.expense_frame.rowconfigure(1, weight=1)
    
    def create_master_tab(self):
        # 左右分割
        paned_window = ttk.PanedWindow(self.master_frame, orient="horizontal")
        paned_window.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 左側: マスターリスト
        left_frame = ttk.LabelFrame(paned_window, text="費用マスターリスト", padding="10")
        
        columns = ("支払い先", "案件名", "金額", "支払タイプ")
        self.master_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.master_tree.heading(col, text=col)
            self.master_tree.column(col, width=120)
        
        self.master_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 右側: 編集フォーム
        right_frame = ttk.LabelFrame(paned_window, text="編集", padding="10")
        
        ttk.Label(right_frame, text="支払い先:").grid(row=0, column=0, sticky="w", pady=2)
        payee_entry = ttk.Entry(right_frame, width=30)
        payee_entry.grid(row=0, column=1, pady=2)
        
        ttk.Label(right_frame, text="案件名:").grid(row=1, column=0, sticky="w", pady=2)
        project_entry = ttk.Entry(right_frame, width=30)
        project_entry.grid(row=1, column=1, pady=2)
        
        ttk.Label(right_frame, text="金額:").grid(row=2, column=0, sticky="w", pady=2)
        amount_entry = ttk.Entry(right_frame, width=30)
        amount_entry.grid(row=2, column=1, pady=2)
        
        ttk.Label(right_frame, text="支払タイプ:").grid(row=3, column=0, sticky="w", pady=2)
        type_combo = ttk.Combobox(right_frame, values=["月額固定", "回数ベース"], width=27)
        type_combo.grid(row=3, column=1, pady=2)
        
        # ボタン
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="保存").grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="削除").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="クリア").grid(row=0, column=2, padx=5)
        
        paned_window.add(left_frame, weight=2)
        paned_window.add(right_frame, weight=1)
        
        self.master_frame.columnconfigure(0, weight=1)
        self.master_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
    
    def load_sample_data(self):
        # サンプルデータの挿入
        payment_data = [
            ("番組制作費", "ラジオ番組A", "制作会社A", "001", "¥500,000", "2025-06-15", "照合済み"),
            ("スポンサー料", "CM枠B", "広告代理店B", "002", "¥300,000", "2025-06-20", "処理中"),
            ("機材費", "録音機器", "機材会社C", "003", "¥150,000", "2025-06-25", "未処理"),
        ]
        
        for data in payment_data:
            self.payment_tree.insert("", "end", values=data)
            
        expense_data = [
            ("2025-06-01", "制作会社A", "ラジオ番組A", "¥500,000", "支払済み", "月額固定"),
            ("2025-06-05", "広告代理店B", "CM制作", "¥200,000", "処理中", ""),
        ]
        
        for data in expense_data:
            self.expense_tree.insert("", "end", values=data)
            
        master_data = [
            ("制作会社A", "ラジオ番組A", "¥500,000", "月額固定"),
            ("機材会社C", "録音機器メンテナンス", "¥50,000", "回数ベース"),
        ]
        
        for data in master_data:
            self.master_tree.insert("", "end", values=data)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = BillingManagerTkDemo()
    app.run()