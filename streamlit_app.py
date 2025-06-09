#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from utils import get_latest_csv_file, format_amount

# ページ設定
st.set_page_config(
    page_title="ラジオ局支払い・費用管理システム",
    page_icon="📻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スタイリング
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-matched { background-color: #90EE90; padding: 2px 8px; border-radius: 4px; }
    .status-processing { background-color: #FFFF99; padding: 2px 8px; border-radius: 4px; }
    .status-processed { background-color: #ADD8E6; padding: 2px 8px; border-radius: 4px; }
    .status-unprocessed { background-color: #F8F8F8; padding: 2px 8px; border-radius: 4px; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitBillingApp:
    def __init__(self):
        self.csv_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        
    def load_payment_data(self):
        """支払いデータを読み込み"""
        try:
            conn = sqlite3.connect('billing.db')
            df = pd.read_sql_query("""
                SELECT subject, project_name, payee, payee_code, amount, payment_date, status
                FROM payments
                ORDER BY payment_date DESC
            """, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def load_expense_data(self):
        """費用データを読み込み"""
        try:
            conn = sqlite3.connect('expenses.db')
            df = pd.read_sql_query("""
                SELECT payment_date, payee, project_name, amount, status, notes
                FROM expenses
                ORDER BY payment_date DESC
            """, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def load_master_data(self):
        """マスターデータを読み込み"""
        try:
            conn = sqlite3.connect('expense_master.db')
            df = pd.read_sql_query("""
                SELECT payee, project_name, amount, payment_type, start_date, end_date
                FROM expense_master
                ORDER BY payee, project_name
            """, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def format_status(self, status):
        """状態を色付きで表示"""
        status_map = {
            "照合済": "status-matched",
            "処理中": "status-processing", 
            "処理済": "status-processed",
            "未処理": "status-unprocessed"
        }
        css_class = status_map.get(status, "status-unprocessed")
        return f'<span class="{css_class}">{status}</span>'
    
    def show_payment_tab(self):
        """支払い情報タブ"""
        st.header("📋 支払い情報 (閲覧専用)")
        
        df = self.load_payment_data()
        if df.empty:
            st.warning("支払いデータがありません")
            return
        
        # フィルター
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            status_options = ["すべて"] + df['status'].unique().tolist()
            selected_status = st.selectbox("状態フィルター", status_options)
        
        with col2:
            search_term = st.text_input("検索（件名・支払い先）", "")
        
        with col3:
            st.metric("総件数", len(df))
        
        # フィルタリング
        filtered_df = df.copy()
        if selected_status != "すべて":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
        if search_term:
            filtered_df = filtered_df[
                filtered_df['subject'].str.contains(search_term, na=False) |
                filtered_df['payee'].str.contains(search_term, na=False)
            ]
        
        # 統計情報
        if not filtered_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                matched_count = len(filtered_df[filtered_df['status'] == '照合済'])
                st.metric("照合済", matched_count)
            
            with col2:
                processing_count = len(filtered_df[filtered_df['status'] == '処理中'])
                st.metric("処理中", processing_count)
            
            with col3:
                processed_count = len(filtered_df[filtered_df['status'] == '処理済'])
                st.metric("処理済", processed_count)
            
            with col4:
                unprocessed_count = len(filtered_df[filtered_df['status'] == '未処理'])
                st.metric("未処理", unprocessed_count)
        
        # データ表示
        st.subheader(f"支払いデータ ({len(filtered_df)}件)")
        
        if not filtered_df.empty:
            # データテーブルの表示用に整形
            display_df = filtered_df.copy()
            display_df['金額'] = display_df['amount'].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "")
            display_df['支払日'] = pd.to_datetime(display_df['payment_date']).dt.strftime('%Y-%m-%d')
            
            # 列名を日本語に
            display_df = display_df.rename(columns={
                'subject': '件名',
                'project_name': '案件名', 
                'payee': '支払い先',
                'payee_code': 'コード',
                'status': '状態'
            })
            
            # 表示列を選択
            columns_to_show = ['件名', '案件名', '支払い先', 'コード', '金額', '支払日', '状態']
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "金額": st.column_config.TextColumn("金額", width="small"),
                    "支払日": st.column_config.DateColumn("支払日", width="small"),
                    "状態": st.column_config.TextColumn("状態", width="small")
                }
            )
    
    def show_expense_tab(self):
        """費用管理タブ"""
        st.header("💰 費用管理")
        
        df = self.load_expense_data()
        if df.empty:
            st.warning("費用データがありません")
            return
        
        # 月別フィルター
        df['payment_date'] = pd.to_datetime(df['payment_date'])
        df['year_month'] = df['payment_date'].dt.strftime('%Y年%m月')
        
        col1, col2 = st.columns([1, 3])
        with col1:
            month_options = ["すべて"] + sorted(df['year_month'].unique().tolist(), reverse=True)
            selected_month = st.selectbox("月フィルター", month_options)
        
        # フィルタリング
        if selected_month != "すべて":
            df = df[df['year_month'] == selected_month]
        
        # 統計
        col1, col2, col3 = st.columns(3)
        with col1:
            total_amount = df['amount'].sum()
            st.metric("総金額", f"¥{total_amount:,.0f}")
        with col2:
            avg_amount = df['amount'].mean()
            st.metric("平均金額", f"¥{avg_amount:,.0f}")
        with col3:
            st.metric("件数", len(df))
        
        # データ表示
        if not df.empty:
            display_df = df.copy()
            display_df['金額'] = display_df['amount'].apply(lambda x: f"¥{x:,.0f}")
            display_df['支払日'] = display_df['payment_date'].dt.strftime('%Y-%m-%d')
            
            display_df = display_df.rename(columns={
                'payee': '支払い先',
                'project_name': '案件名',
                'status': '状態',
                'notes': '備考'
            })
            
            columns_to_show = ['支払日', '支払い先', '案件名', '金額', '状態', '備考']
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                hide_index=True
            )
    
    def show_master_tab(self):
        """費用マスタータブ"""
        st.header("⚙️ 費用マスター")
        
        df = self.load_master_data()
        if df.empty:
            st.warning("マスターデータがありません")
            return
        
        # 支払タイプ別統計
        col1, col2, col3 = st.columns(3)
        with col1:
            monthly_count = len(df[df['payment_type'] == '月額固定'])
            st.metric("月額固定", f"{monthly_count}件")
        with col2:
            count_based = len(df[df['payment_type'] == '回数ベース'])
            st.metric("回数ベース", f"{count_based}件")
        with col3:
            total_monthly = df[df['payment_type'] == '月額固定']['amount'].sum()
            st.metric("月額固定合計", f"¥{total_monthly:,.0f}")
        
        # データ表示
        if not df.empty:
            display_df = df.copy()
            display_df['金額'] = display_df['amount'].apply(lambda x: f"¥{x:,.0f}")
            display_df['開始日'] = pd.to_datetime(display_df['start_date']).dt.strftime('%Y-%m-%d')
            display_df['終了日'] = pd.to_datetime(display_df['end_date']).dt.strftime('%Y-%m-%d')
            
            display_df = display_df.rename(columns={
                'payee': '支払い先',
                'project_name': '案件名',
                'payment_type': '支払タイプ'
            })
            
            columns_to_show = ['支払い先', '案件名', '金額', '支払タイプ', '開始日', '終了日']
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                hide_index=True
            )

def main():
    # タイトル
    st.markdown('<h1 class="main-header">📻 ラジオ局支払い・費用管理システム</h1>', unsafe_allow_html=True)
    
    app = StreamlitBillingApp()
    
    # サイドバーでタブ選択
    st.sidebar.title("📋 メニュー")
    tab = st.sidebar.radio(
        "タブを選択:",
        ["💳 支払い情報", "💰 費用管理", "⚙️ 費用マスター"]
    )
    
    # CSVファイル情報
    csv_file = get_latest_csv_file(app.csv_folder)
    if csv_file:
        file_name = os.path.basename(csv_file)
        file_size = os.path.getsize(csv_file) // 1024
        st.sidebar.info(f"📄 最新CSV: {file_name} ({file_size}KB)")
    
    # タブ表示
    if tab == "💳 支払い情報":
        app.show_payment_tab()
    elif tab == "💰 費用管理":
        app.show_expense_tab()
    elif tab == "⚙️ 費用マスター":
        app.show_master_tab()

if __name__ == "__main__":
    main()