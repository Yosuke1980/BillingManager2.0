# 発注管理機能 要件定義書

## バージョン情報
- 作成日: 2025-10-31
- 対象システム: BillingManager2.0
- 目的: 既存のラジオ局支払い・費用管理システムに発注管理機能を追加

---

## 1. 概要

### 1.1 背景と目的
- **課題**: 単発案件で請求書の受領漏れが発生している
- **原因**: 発注管理が散在し、追跡が困難
- **目的**: 発注から請求書受領までを一元管理し、漏れをなくす

### 1.2 対象範囲
- レギュラー番組の細分化管理
- 単発案件（イベント、ゲスト、取材、公開収録など）の管理
- 発注メール作成の自動化
- Gmail連携による発注状況の自動追跡
- 案件ごとの予算管理

### 1.3 既存システムとの関係
- **既存機能を維持**: 支払いタブ、費用管理タブ、費用マスタータブ、案件絞込みタブ、監視機能タブ
- **新規追加**: 「発注管理」タブを追加
- **データベース拡張**: 既存DBに新規テーブルを追加（既存テーブルは変更しない）
- **独立性**: 新機能は既存機能と独立して動作し、段階的に統合可能

---

## 2. 機能要件

### 2.1 発注管理の基本構造

#### 2.1.1 階層構造
```
番組/イベント (レベル1: Project)
└─ コーナー (レベル2: Sub-Project) ※任意
   └─ 費用項目 (レベル3: Expense)
```

**例:**
```
番組A
├─ A出演料
├─ 制作費
└─ コーナーB
    ├─ コーナーB制作費
    └─ コーナーB、p出演料

夏休みイベント (単発)
├─ 伊藤出演料: 10,000円
├─ 加藤出演料: 20,000円
└─ 制作費: 100,000円
```

#### 2.1.2 案件タイプ
- **レギュラー**: 継続的な番組
- **単発**: イベント、ゲスト出演、取材費、公開収録など

#### 2.1.3 役務の管理
- 同じ発注先が複数の案件に登場する場合、案件ごとに別管理
- 発注先マスタから選択して費用項目を作成

---

### 2.2 発注先マスタ管理

#### 2.2.1 管理項目
- 発注先ID (自動採番)
- 発注先名 (会社名/個人名)
- 担当者名
- メールアドレス
- 電話番号
- 住所
- 備考

#### 2.2.2 機能
- 発注先の登録・編集・削除
- 一覧表示・検索
- 費用項目作成時に選択可能

---

### 2.3 案件管理

#### 2.3.1 案件情報
- 案件ID (自動採番)
- 案件名
- 実施日
- 案件タイプ (レギュラー/単発)
- 予算額
- 親案件ID (階層構造用)
- 作成日時・更新日時

#### 2.3.2 予算管理
- 案件ごとに予算を設定
- 費用項目の合計が実績
- 予算 vs 実績の比較表示
- 残予算の自動計算
- 予算超過時の警告表示

---

### 2.4 費用項目管理

#### 2.4.1 費用項目情報
- 費用項目ID (自動採番)
- 案件ID (親案件への紐付け)
- 項目名 (例: 伊藤出演料)
- 金額
- 発注先ID (マスタから選択)
- 担当者 (発注先の担当者)
- ステータス
- 発注番号
- 各種日付 (発注日、実施日、請求書受領日、支払予定日、支払日)
- Gmail関連情報
- 備考

#### 2.4.2 ステータス管理
```
1. 発注予定
   ↓
2. 下書き作成済
   ↓ (Gmail送信ボックスで自動検知)
3. 発注済
   ↓
4. 実施済
   ↓ (実施日翌日に自動チェック)
5. 請求書待ち ⚠️
   ↓
6. 請求書受領
   ↓
7. 支払済
```

---

### 2.5 発注メール自動生成機能

#### 2.5.1 発注番号の自動採番
- 形式: `RB-YYYYMMDD-XXX`
- 例: `RB-20250809-001`
- 日付ごとに連番
- 重複チェック機能

#### 2.5.2 メールテンプレート
**件名:**
```
【発注 {発注番号}】{実施日} {案件名} - {項目名}
```

**本文:**
```
{担当者名}様

お世話になっております。

下記の通り、ご依頼申し上げます。

━━━━━━━━━━━━━━━━━━━━━━
■発注番号: {発注番号}
■案件名: {案件名}
■実施日: {実施日}
■ご担当: {出演者/作業者名}
■金額: {金額:,}円
━━━━━━━━━━━━━━━━━━━━━━

■お支払予定日: {支払予定日}

実施後、下記内容を含む請求書をお送りいただけますと幸いです。
・発注番号: {発注番号}
・案件名: {案件名}
・金額: {金額:,}円

何卒よろしくお願いいたします。

────────────────────────
{署名}
────────────────────────
```

#### 2.5.3 変数の自動置換
- 発注先マスタから担当者名を取得
- 案件情報から案件名・実施日を取得
- 費用項目から金額・項目名を取得
- 設定ファイルから署名を取得

---

### 2.6 Gmail連携機能

#### 2.6.1 使用プロトコル
- **IMAP**: Gmail接続
- **対象**: Google Workspace アカウント
- **認証**: メールアドレス + アプリパスワード

#### 2.6.2 下書き作成機能
1. ユーザーが「発注メール作成」ボタンをクリック
2. メールテンプレートに情報を埋め込み
3. IMAPでGmail [Gmail]/Drafts に下書き保存
4. 下書きIDをDBに記録
5. ステータスを「下書き作成済」に更新
6. (オプション) ブラウザでGmail下書きを開く

#### 2.6.3 送信確認機能
**トリガー:**
- アプリ起動時
- 発注管理タブを開いたとき
- 手動チェックボタンクリック時

**処理フロー:**
1. IMAPでGmail [Gmail]/Sent Mail フォルダに接続
2. 「下書き作成済」または「発注済」でない項目の発注番号でメール検索
3. 件名に発注番号を含むメールが見つかった場合:
   - ステータスを「発注済」に更新
   - 送信日時を記録
   - 送信先メールアドレスを記録
   - order_historyに履歴を保存

#### 2.6.4 Gmail設定
- 初回起動時または設定画面で入力
- メールアドレス
- アプリパスワード
- 署名
- 設定ファイル (config.py) に保存

---

### 2.7 アラート機能

#### 2.7.1 請求書未着アラート
**条件:**
- ステータスが「実施済」または「請求書待ち」
- 実施日の翌日を過ぎている
- 請求書受領日が未設定

**表示:**
```
⚠️ 請求書未着: 3件
- 8/9 夏休みイベント - 伊藤出演料 (伊藤事務所/田中)
- 8/10 番組A - ゲスト佐藤出演料 (佐藤プロ/山田)
```

#### 2.7.2 下書き未送信アラート
**条件:**
- ステータスが「下書き作成済」
- 下書き作成から24時間以上経過

**表示:**
```
📧 下書き未送信: 2件
- 8/15 番組B - 加藤出演料 (加藤プロ/山田)
```

#### 2.7.3 アラート表示位置
- 発注管理タブの上部に常時表示
- 該当項目がある場合のみ表示
- クリックで該当項目にジャンプ

---

### 2.8 履歴管理

#### 2.8.1 発注履歴 (order_history)
- 発注番号ごとの履歴
- メール件名・本文の記録
- 送信日時・送信先の記録
- Gmail下書きID・メッセージIDの記録

#### 2.8.2 ステータス履歴 (status_history)
- ステータス変更の履歴
- 変更日時の記録
- 備考の記録

---

## 3. データベース設計

### 3.1 新規テーブル

#### 3.1.1 suppliers (発注先マスタ)
```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                             -- 発注先名
    contact_person TEXT,                            -- 担当者名
    email TEXT,                                     -- メールアドレス
    phone TEXT,                                     -- 電話番号
    address TEXT,                                   -- 住所
    notes TEXT,                                     -- 備考
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 projects (案件マスタ)
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                             -- 案件名
    date DATE NOT NULL,                             -- 実施日
    type TEXT NOT NULL,                             -- レギュラー/単発
    budget REAL DEFAULT 0,                          -- 予算額
    parent_id INTEGER,                              -- 親案件ID (階層用)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES projects(id)
);
```

#### 3.1.3 expenses (費用項目)
```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                    -- 案件ID
    item_name TEXT NOT NULL,                        -- 項目名
    amount REAL NOT NULL,                           -- 金額
    supplier_id INTEGER,                            -- 発注先ID
    contact_person TEXT,                            -- 担当者
    status TEXT DEFAULT '発注予定',                 -- ステータス
    order_number TEXT UNIQUE,                       -- 発注番号
    order_date DATE,                                -- 発注日
    implementation_date DATE,                       -- 実施日
    invoice_received_date DATE,                     -- 請求書受領日
    payment_scheduled_date DATE,                    -- 支払予定日
    payment_date DATE,                              -- 支払日
    gmail_draft_id TEXT,                            -- Gmail下書きID
    gmail_message_id TEXT,                          -- 送信後のメッセージID
    email_sent_at TIMESTAMP,                        -- 実際の送信日時
    notes TEXT,                                     -- 備考
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);
```

#### 3.1.4 order_history (発注履歴)
```sql
CREATE TABLE order_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,                    -- 費用項目ID
    order_number TEXT NOT NULL,                     -- 発注番号
    email_subject TEXT,                             -- メール件名
    email_body TEXT,                                -- メール本文
    sent_to TEXT,                                   -- 送信先
    gmail_draft_id TEXT,                            -- Gmail下書きID
    gmail_message_id TEXT,                          -- 送信後のメッセージID
    sent_at TIMESTAMP,                              -- 送信日時
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses(id)
);
```

#### 3.1.5 status_history (ステータス履歴)
```sql
CREATE TABLE status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,                    -- 費用項目ID
    old_status TEXT,                                -- 旧ステータス
    new_status TEXT,                                -- 新ステータス
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                                     -- 備考
    FOREIGN KEY (expense_id) REFERENCES expenses(id)
);
```

### 3.2 既存データベースとの関係
- **既存テーブルは変更しない**
- **新規テーブルのみ追加**
- 将来的に既存の費用管理と統合する場合は、データ移行スクリプトを別途作成

---

## 4. UI設計

### 4.1 タブ構成

#### 4.1.1 既存タブ (変更なし)
- 支払い
- 費用管理
- 費用マスター
- 案件絞込み
- 監視機能

#### 4.1.2 新規タブ
- **発注管理** ← NEW!

### 4.2 発注管理タブの構成

#### 4.2.1 サブタブ
```
[案件一覧] [発注先マスタ] [設定]
```

#### 4.2.2 案件一覧画面レイアウト
```
┌─────────────────────────────────────────────────────┐
│ 🚨 アラート: 請求書未着 3件 / 📧 下書き未送信 2件   │
│ • 8/9 夏休みイベント - 伊藤出演料 [詳細へ]          │
└─────────────────────────────────────────────────────┘

┌─ フィルター ────────────────────────────────────────┐
│ 期間: [2025/08 ▼] タイプ: [全て ▼]                 │
│ [Gmail送信確認] [新規案件作成]                      │
└─────────────────────────────────────────────────────┘

┌─ 案件リスト ────────────────────────────────────────┐
│ 日付    │案件名          │タイプ  │予算    │実績    │残  │状態 │
│ 8/9     │夏休みイベント  │単発    │150,000 │130,000 │20K │⚠️   │
│ 8/15    │番組A 8月分     │レギュラー│500,000 │480,000 │20K │✓   │
│ 8/20    │取材費          │単発    │50,000  │0       │50K │📝  │
└─────────────────────────────────────────────────────┘
```

#### 4.2.3 案件詳細ツリービュー
```
┌─ 8/9 夏休みイベント (単発) ─────────────────────────┐
│ 予算: 150,000円 / 実績: 130,000円 / 残: 20,000円   │
│                                         [費用追加]   │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ├─ 伊藤出演料: 10,000円                            │
│ │   [請求書待ち⚠️] 実施翌日経過                     │
│ │   発注先: 伊藤事務所 (担当: 田中)                │
│ │   発注番号: RB-20250809-001                       │
│ │   📧 8/5 10:30 送信済                              │
│ │   [詳細編集] [請求書受領] [履歴表示]             │
│ │                                                    │
│ ├─ 加藤出演料: 20,000円                            │
│ │   [下書き作成済📝]                                │
│ │   発注先: 加藤プロ (担当: 山田)                  │
│ │   発注番号: RB-20250809-002                       │
│ │   📧 [Gmail下書きを開く]                          │
│ │   [詳細編集] [下書き削除]                        │
│ │                                                    │
│ └─ 制作費: 100,000円                               │
│     [支払済✓]                                       │
│     発注先: ABC制作 (担当: 鈴木)                   │
│     発注番号: RB-20250809-003                       │
│     [詳細表示] [履歴表示]                          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 5. 既存システムとの統合

### 5.1 app.py への追加

#### 5.1.1 インポート追加
```python
from order_management_tab import OrderManagementTab
```

#### 5.1.2 タブ追加 (_add_tabs メソッド)
```python
# 発注管理タブ
self.order_management_tab = OrderManagementTab(tab_control, self)
tab_control.addTab(self.order_management_tab, '発注管理')
```

#### 5.1.3 データベース初期化 (DatabaseManager)
```python
# database.py の init_db メソッドに追加
self._create_order_management_tables()
```

### 5.2 config.py への追加

```python
# Gmail IMAP設定
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# ユーザー設定（初回起動時に設定）
GMAIL_ADDRESS = ""
GMAIL_APP_PASSWORD = ""
EMAIL_SIGNATURE = ""

# タブ名追加
TAB_NAMES = {
    'payment': '支払い',
    'expense': '費用管理',
    'master': '費用マスター',
    'project_filter': '案件絞込み',
    'monitoring': '監視機能',
    'order_management': '発注管理',  # 追加
}
```

---

## 6. 実装計画

### Phase 1: 基礎構築 (Week 1-2)
- データベース拡張
- 発注先マスタ機能
- 基本UI構築

### Phase 2: Gmail連携 (Week 3-4)
- Gmail設定機能
- メール自動生成
- Gmail下書き作成
- 送信確認機能

### Phase 3: コア機能 (Week 5-6)
- 案件管理
- 費用項目管理
- ツリービュー
- アラート機能

### Phase 4: 予算管理 (Week 7)
- 予算設定
- 予算集計
- 表示機能

### Phase 5: テスト・調整 (Week 8)
- 統合テスト
- パフォーマンス調整
- ドキュメント作成

---

## 7. ファイル構成

```
BillingManager2.0/
├── app.py                          # メインアプリ（タブ追加のみ）
├── database.py                     # DB管理（テーブル追加メソッド追加）
├── config.py                       # 設定（Gmail設定追加）
│
├── order_management_tab.py         # NEW: 発注管理タブのメインクラス
├── order_management/               # NEW: 発注管理モジュール
│   ├── __init__.py
│   ├── models.py                   # データモデル
│   ├── database_manager.py         # 発注管理用DB操作
│   ├── gmail_manager.py            # Gmail IMAP連携
│   ├── email_template.py           # メールテンプレート
│   ├── order_number_generator.py   # 発注番号生成
│   ├── alert_manager.py            # アラート機能
│   │
│   ├── ui/                         # UI関連
│   │   ├── __init__.py
│   │   ├── project_list_widget.py
│   │   ├── project_tree_widget.py
│   │   ├── supplier_master_widget.py
│   │   ├── expense_edit_dialog.py
│   │   ├── project_edit_dialog.py
│   │   ├── supplier_edit_dialog.py
│   │   ├── gmail_settings_dialog.py
│   │   └── alert_widget.py
│   │
│   └── utils/                      # ユーティリティ
│       ├── __init__.py
│       ├── date_utils.py
│       ├── format_utils.py
│       └── validation.py
│
└── requirements_order_management.md # この要件定義書
```

---

**要件定義書 終わり**
