#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from utils import get_latest_csv_file, format_amount
from database import DatabaseManager

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
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .status-matched { background-color: #90EE90; padding: 2px 8px; border-radius: 4px; }
    .status-processing { background-color: #FFFF99; padding: 2px 8px; border-radius: 4px; }
    .status-processed { background-color: #ADD8E6; padding: 2px 8px; border-radius: 4px; }
    .status-unprocessed { background-color: #F8F8F8; padding: 2px 8px; border-radius: 4px; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 3px solid #1f77b4;
    }
    /* データテーブルの見やすさ改善 */
    div[data-testid="stDataFrame"] {
        font-size: 12px;
    }
    div[data-testid="stDataFrame"] table {
        font-size: 12px !important;
    }
    /* Streamlitコンポーネントのサイズ最適化 */
    .stSelectbox > div > div {
        font-size: 12px !important;
        padding: 0.25rem 0.5rem !important;
    }
    .stTextInput > div > div > input {
        font-size: 12px !important;
        padding: 0.25rem 0.5rem !important;
        height: 2rem !important;
    }
    .stButton > button {
        font-size: 12px !important;
        padding: 0.25rem 0.75rem !important;
        height: 2.2rem !important;
        line-height: 1.2 !important;
    }
    .stRadio > div {
        font-size: 12px !important;
    }
    .stRadio > div > label > div {
        font-size: 12px !important;
    }
    /* メトリクス表示の最適化 */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    div[data-testid="metric-container"] > div {
        font-size: 12px !important;
    }
    /* サイドバーの最適化 */
    .css-1d391kg {
        font-size: 12px !important;
    }
    .stSidebar .stSelectbox label {
        font-size: 12px !important;
    }
    /* ヘッダーサイズ調整 */
    h1, .stTitle {
        font-size: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2, .stHeader {
        font-size: 1.25rem !important;
        margin-bottom: 0.5rem !important;
    }
    h3, .stSubheader {
        font-size: 1.1rem !important;
        margin-bottom: 0.3rem !important;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitBillingApp:
    def __init__(self):
        self.csv_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.db_manager = DatabaseManager()
        self.header_mapping = {
            "おもて情報.件名": "subject",
            "明細情報.明細項目": "project_name", 
            "おもて情報.請求元": "payee",
            "おもて情報.支払先コード": "payee_code",
            "明細情報.金額": "amount",
            "おもて情報.自社支払期限": "payment_date",
            "状態": "status",
        }
        
        # データベース初期化
        self.init_database()
    
    def init_database(self):
        """データベースの初期化"""
        try:
            self.db_manager.init_db()
            return True
        except Exception as e:
            st.error(f"データベース初期化エラー: {e}")
            return False
    
    def import_latest_csv(self):
        """最新のCSVファイルからデータをインポート"""
        csv_file = get_latest_csv_file(self.csv_folder)
        
        if not csv_file:
            return False, "CSVファイルが見つかりません"
        
        try:
            row_count = self.db_manager.import_csv_data(csv_file, self.header_mapping)
            file_name = os.path.basename(csv_file)
            return True, f"{row_count}件のデータをCSVからインポートしました: {file_name}"
        except Exception as e:
            return False, f"CSVファイルの読み込みに失敗しました: {str(e)}"
        
    def load_payment_data(self):
        """支払いデータを読み込み"""
        try:
            payment_rows, _ = self.db_manager.get_payment_data()
            if not payment_rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(payment_rows, columns=[
                'id', 'subject', 'project_name', 'payee', 'payee_code', 
                'amount', 'payment_date', 'status'
            ])
            return df
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def load_expense_data(self):
        """費用データを読み込み"""
        try:
            expense_rows, _ = self.db_manager.get_expense_data()
            if not expense_rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(expense_rows, columns=[
                'id', 'project_name', 'payee', 'payee_code', 
                'amount', 'payment_date', 'status'
            ])
            return df
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            return pd.DataFrame()
    
    def load_master_data(self):
        """マスターデータを読み込み"""
        try:
            master_rows = self.db_manager.get_master_data()
            if not master_rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(master_rows, columns=[
                'id', 'project_name', 'payee', 'payee_code', 'amount', 
                'payment_type', 'broadcast_days', 'start_date', 'end_date'
            ])
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
        
        # フィルター状態をセッション状態で管理
        if 'payment_status_filter' not in st.session_state:
            st.session_state.payment_status_filter = "すべて"
        if 'payment_search_term' not in st.session_state:
            st.session_state.payment_search_term = ""
        
        # フィルター
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            status_options = ["すべて"] + df['status'].unique().tolist()
            selected_status = st.selectbox(
                "状態フィルター", 
                status_options,
                index=status_options.index(st.session_state.payment_status_filter) if st.session_state.payment_status_filter in status_options else 0,
                key="payment_status_selectbox"
            )
            st.session_state.payment_status_filter = selected_status
        
        with col2:
            search_term = st.text_input(
                "検索（件名・支払い先）", 
                value=st.session_state.payment_search_term,
                key="payment_search_input"
            )
            st.session_state.payment_search_term = search_term
        
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
                st.metric("照合済", matched_count, delta=f"{matched_count/len(filtered_df)*100:.1f}%")
            
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
            display_df['支払日'] = pd.to_datetime(display_df['payment_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
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
                height=600,
                column_config={
                    "件名": st.column_config.TextColumn("件名", width="large"),
                    "案件名": st.column_config.TextColumn("案件名", width="medium"), 
                    "支払い先": st.column_config.TextColumn("支払い先", width="medium"),
                    "コード": st.column_config.TextColumn("コード", width="small"),
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
        
        # 月別フィルター状態をセッション状態で管理
        if 'expense_month_filter' not in st.session_state:
            st.session_state.expense_month_filter = "すべて"
        
        # 月別フィルター
        df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce')
        df['year_month'] = df['payment_date'].dt.strftime('%Y年%m月')
        
        col1, col2 = st.columns([1, 3])
        with col1:
            # NaN値を除外してからソート
            unique_months = df['year_month'].dropna().unique().tolist()
            month_options = ["すべて"] + sorted(unique_months, reverse=True)
            selected_month = st.selectbox(
                "月フィルター", 
                month_options,
                index=month_options.index(st.session_state.expense_month_filter) if st.session_state.expense_month_filter in month_options else 0,
                key="expense_month_selectbox"
            )
            st.session_state.expense_month_filter = selected_month
        
        # フィルタリング
        if selected_month != "すべて":
            df = df[df['year_month'] == selected_month]
        
        # 統計
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_amount = df['amount'].sum()
            st.metric("総金額", f"¥{total_amount:,.0f}")
        with col2:
            avg_amount = df['amount'].mean()
            st.metric("平均金額", f"¥{avg_amount:,.0f}")
        with col3:
            matched_count = len(df[df['status'] == '照合済'])
            st.metric("照合済", matched_count, delta=f"{matched_count/len(df)*100:.1f}%" if len(df) > 0 else "0%")
        with col4:
            st.metric("総件数", len(df))
        
        # データ表示
        if not df.empty:
            display_df = df.copy()
            display_df['金額'] = display_df['amount'].apply(lambda x: f"¥{x:,.0f}")
            display_df['支払日'] = pd.to_datetime(display_df['payment_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            display_df = display_df.rename(columns={
                'payee': '支払い先',
                'project_name': '案件名',
                'payee_code': 'コード',
                'status': '状態'
            })
            
            columns_to_show = ['支払日', '支払い先', 'コード', '案件名', '金額', '状態']
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "支払日": st.column_config.DateColumn("支払日", width="small"),
                    "支払い先": st.column_config.TextColumn("支払い先", width="medium"),
                    "コード": st.column_config.TextColumn("コード", width="small"),
                    "案件名": st.column_config.TextColumn("案件名", width="medium"),
                    "金額": st.column_config.TextColumn("金額", width="small"),
                    "状態": st.column_config.TextColumn("状態", width="small")
                }
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
            display_df['開始日'] = pd.to_datetime(display_df['start_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            display_df['終了日'] = pd.to_datetime(display_df['end_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            display_df = display_df.rename(columns={
                'payee': '支払い先',
                'project_name': '案件名',
                'payee_code': 'コード',
                'payment_type': '支払タイプ',
                'broadcast_days': '放送曜日'
            })
            
            columns_to_show = ['支払い先', 'コード', '案件名', '金額', '支払タイプ', '放送曜日', '開始日', '終了日']
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "支払い先": st.column_config.TextColumn("支払い先", width="medium"),
                    "コード": st.column_config.TextColumn("コード", width="small"),
                    "案件名": st.column_config.TextColumn("案件名", width="medium"),
                    "金額": st.column_config.TextColumn("金額", width="small"),
                    "支払タイプ": st.column_config.TextColumn("支払タイプ", width="small"),
                    "放送曜日": st.column_config.TextColumn("放送曜日", width="small"),
                    "開始日": st.column_config.DateColumn("開始日", width="small"),
                    "終了日": st.column_config.DateColumn("終了日", width="small")
                }
            )

def main():
    # タイトル
    st.markdown('<h1 class="main-header">📻 ラジオ局支払い・費用管理システム</h1>', unsafe_allow_html=True)
    
    # 照合完了メッセージを表示（一回のみ）
    if st.session_state.get('matching_completed', False):
        st.success(st.session_state.matching_result)
        # フラグをリセット
        st.session_state.matching_completed = False
        del st.session_state.matching_result
    
    app = StreamlitBillingApp()
    
    # 初回起動時にCSVデータを自動読み込み
    if 'csv_loaded' not in st.session_state:
        with st.spinner("初期データを読み込み中..."):
            success, message = app.import_latest_csv()
            if success:
                st.success(message)
            else:
                st.warning(message)
            st.session_state['csv_loaded'] = True
    
    # サイドバーでタブ選択
    st.sidebar.title("📋 メニュー")
    tab = st.sidebar.radio(
        "タブを選択:",
        ["💳 支払い情報", "💰 費用管理", "⚙️ 費用マスター"]
    )
    
    # CSVファイル情報とインポート機能
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 CSVデータ管理")
    
    csv_file = get_latest_csv_file(app.csv_folder)
    if csv_file:
        file_name = os.path.basename(csv_file)
        file_size = os.path.getsize(csv_file) // 1024
        file_time = datetime.fromtimestamp(os.path.getmtime(csv_file)).strftime("%m/%d %H:%M")
        st.sidebar.info(f"📄 最新CSV: {file_name}\n({file_size}KB, {file_time})")
        
        # CSVインポートボタン
        if st.sidebar.button("🔄 CSVデータを再読み込み", help="最新のCSVファイルからデータを再インポートします"):
            with st.spinner("CSVデータを読み込み中..."):
                success, message = app.import_latest_csv()
                if success:
                    st.sidebar.success(message)
                    st.rerun()  # ページを再読み込み
                else:
                    st.sidebar.error(message)
    else:
        st.sidebar.warning("CSVファイルが見つかりません")
    
    # 照合機能
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 データ照合")
    
    if st.sidebar.button("💰 費用と支払いを照合", help="費用データと支払いデータを自動照合します"):
        with st.spinner("データを照合中..."):
            try:
                matched_count, not_matched_count = app.db_manager.match_expenses_with_payments()
                if matched_count > 0:
                    # 照合完了フラグをセット
                    st.session_state.matching_completed = True
                    st.session_state.matching_result = f"照合完了: {matched_count}件一致、{not_matched_count}件未一致"
                    st.rerun()  # ページを再読み込み
                else:
                    st.sidebar.info(f"照合結果: 新しい一致なし、{not_matched_count}件未一致")
            except Exception as e:
                st.sidebar.error(f"照合エラー: {str(e)}")
    
    # 照合統計の表示
    try:
        # 支払いデータの照合状況
        payment_rows, _ = app.db_manager.get_payment_data()
        if payment_rows:
            payment_df = pd.DataFrame(payment_rows, columns=[
                'id', 'subject', 'project_name', 'payee', 'payee_code', 
                'amount', 'payment_date', 'status'
            ])
            payment_matched = len(payment_df[payment_df['status'] == '照合済'])
            payment_total = len(payment_df)
            
            # 費用データの照合状況
            expense_rows, _ = app.db_manager.get_expense_data()
            if expense_rows:
                expense_df = pd.DataFrame(expense_rows, columns=[
                    'id', 'project_name', 'payee', 'payee_code', 
                    'amount', 'payment_date', 'status'
                ])
                expense_matched = len(expense_df[expense_df['status'] == '照合済'])
                expense_total = len(expense_df)
                
                # 照合率を表示
                st.sidebar.markdown("**📊 照合状況**")
                st.sidebar.text(f"支払い: {payment_matched}/{payment_total} ({payment_matched/payment_total*100:.1f}%)" if payment_total > 0 else "支払い: 0件")
                st.sidebar.text(f"費用: {expense_matched}/{expense_total} ({expense_matched/expense_total*100:.1f}%)" if expense_total > 0 else "費用: 0件")
    except:
        pass  # エラーは無視
    
    # タブ表示
    if tab == "💳 支払い情報":
        app.show_payment_tab()
    elif tab == "💰 費用管理":
        app.show_expense_tab()
    elif tab == "⚙️ 費用マスター":
        app.show_master_tab()

if __name__ == "__main__":
    main()