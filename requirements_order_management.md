# 発注管理機能 要件定義書

## バージョン情報
- 作成日: 2025-10-31
- 最終更新日: 2025-11-01
- 対象システム: BillingManager2.0
- 目的: 既存のラジオ局支払い・費用管理システムに発注管理機能を追加

## 実装状況
- ✅ **Phase 1完了**: データベース拡張、発注先マスタ、基本UI構築
- ✅ **Phase 2完了**: Gmail連携、メール自動生成、下書き作成、送信確認機能
- ✅ **Phase 3完了**: 案件管理、費用項目管理、ツリービュー、アラート機能
- ✅ **Phase 4完了**: 予算管理、予算集計、表示機能
- ✅ **Phase 6完了**: 取引先マスタ統合（partners テーブル）
- ✅ **番組マスター機能完了**: 番組情報の管理（放送時間、曜日、ステータス、制作会社、出演者）
- ✅ **出演者マスター機能完了**: 出演者情報の管理（所属事務所連携）

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
- 番組マスター管理
- 出演者マスター管理
- 取引先マスター統合管理

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
    └─ コーナーB出演料

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

### 2.2 統合取引先マスター管理 ✅ **実装完了**

#### 2.2.1 背景と統合の経緯
**旧システムの問題:**
- **支払先マスタ** (`payee_master.db`): 既存の支払い管理機能で使用
- **発注先マスタ** (`suppliers`): 発注管理機能で使用
- データ重複、メンテナンス性低下、整合性リスクが存在

**統合によるメリット:**
1. **データ一元管理**: 取引先情報を1箇所で管理
2. **情報の整合性**: 更新時の不一致を防止
3. **業務効率化**: マスタメンテナンスの工数削減
4. **拡張性**: 将来的な取引先情報の拡張が容易

#### 2.2.2 管理項目
- 取引先ID (自動採番)
- 取引先名 (会社名/個人名)
- 取引先コード (既存の支払先コードを継承)
- 担当者名
- メールアドレス
- 電話番号
- 住所
- 取引先区分 (発注先/支払先/両方)
- 備考
- 作成日時・更新日時

**取引先区分の説明:**
- `発注先`: 発注管理でのみ使用
- `支払先`: 支払い管理でのみ使用
- `両方`: 両方の機能で使用（デフォルト）

#### 2.2.3 機能
- 取引先の登録・編集・削除
- 一覧表示・検索
- 取引先区分によるフィルタリング
- 費用項目作成時に選択可能
- 番組マスターの制作会社選択に使用
- 出演者マスターの所属事務所選択に使用

---

### 2.3 番組マスター管理 ✅ **実装完了**

#### 2.3.1 概要
番組の基本情報を管理し、出演者や制作会社との紐付けを行う機能です。

#### 2.3.2 管理項目
- 番組ID (自動採番)
- 番組名 (必須、ユニーク)
- 備考
- 開始日
- 終了日
- 放送時間（例: 23:00-24:00）
- 放送曜日（月・火・水・木・金・土・日）
- ステータス（放送中/終了）
- 出演者リスト（出演者マスターから選択、役割設定可能）
- 制作会社リスト（取引先マスターから選択）
- 作成日時・更新日時

#### 2.3.3 出演者管理機能
- **出演者追加**: 出演者マスターから複数選択可能
- **役割設定**: 各出演者に役割（MC、アシスタント等）を設定可能
- **出演者表示**: 「出演者名（所属事務所）- 役割」形式で表示
- **出演者削除**: 番組からの出演者削除
- **新規出演者登録**: 番組編集中に新規出演者を登録可能

#### 2.3.4 制作会社管理機能
- **制作会社追加**: 取引先マスターから複数選択可能
- **制作会社表示**: 取引先コード付きで表示
- **制作会社削除**: 番組からの制作会社削除

#### 2.3.5 UI機能
- 番組一覧表示（テーブル形式）
- 検索機能（番組名）
- ステータスフィルター（全て/放送中/終了）
- 番組編集ダイアログ
  - 基本情報入力
  - 出演者リスト管理
  - 制作会社リスト管理
- 新規追加・編集・削除機能

---

### 2.4 出演者マスター管理 ✅ **実装完了**

#### 2.4.1 概要
出演者の基本情報を管理し、所属事務所（取引先マスター）との紐付けを行う機能です。

#### 2.4.2 管理項目
- 出演者ID (自動採番)
- 出演者名 (必須、ユニーク)
- 所属事務所/個人 (取引先マスターから選択、必須)
- 備考
- 作成日時・更新日時

#### 2.4.3 所属事務所連携
- 取引先マスター（partners）との連携
- 所属事務所選択時に取引先選択ダイアログを使用
- 個人事務所や個人も取引先として登録可能

#### 2.4.4 UI機能
- 出演者一覧表示（テーブル形式）
  - 出演者名、所属事務所名、取引先コード、備考を表示
- 検索機能（出演者名、所属事務所名）
- 出演者編集ダイアログ
  - 出演者名入力
  - 所属事務所選択（取引先選択ダイアログ）
  - 備考入力
- 新規追加・編集・削除機能

#### 2.4.5 番組マスターとの連携
- 番組編集時に出演者マスターから選択
- 複数出演者の一括選択が可能
- 出演者ごとに役割を設定可能
- 「出演者名（所属事務所）」形式で表示

---

### 2.5 案件管理

#### 2.5.1 案件情報
- 案件ID (自動採番)
- 案件名
- 実施日 (単発案件の場合)
- 開始日・終了日 (レギュラー案件の場合)
- 案件タイプ (レギュラー/単発)
- 予算額
- 親案件ID (階層構造用)
- 作成日時・更新日時

#### 2.5.2 予算管理 ✅ **実装済み**
- 案件ごとに予算を設定
- 費用項目の合計が実績
- 予算 vs 実績の比較表示
- 残予算の自動計算
- 予算超過時の警告表示

#### 2.5.3 レギュラー案件の日付管理 ✅ **実装済み**
**目的:** レギュラー案件は継続的な番組のため、期間（開始日〜終了日）で管理する必要がある。

**仕様:**
- レギュラー案件には `start_date`（開始日）と `end_date`（終了日）を設定
- 単発案件には `date`（実施日）のみを設定
- 案件編集ダイアログでは、タイプに応じて表示フィールドを動的に切り替え
  - レギュラー選択時: 「開始日」「終了日」フィールドを表示
  - 単発選択時: 「実施日」フィールドのみ表示
- 案件一覧での日付表示形式
  - レギュラー案件: `2025-04-01 ～ 2025-09-30`
  - 単発案件: `2025-08-09`

#### 2.5.4 案件複製機能 ✅ **実装済み**
**目的:** 類似案件を効率的に作成するため、既存案件を複製可能にする。

**仕様:**
- 案件一覧に「複製」ボタンを配置
- 複製時の確認ダイアログを表示
- 複製される内容:
  - 案件名（末尾に「（コピー）」を自動追加）
  - 案件タイプ（レギュラー/単発）
  - 予算額
  - 日付（実施日/開始日/終了日）
  - 関連するすべての費用項目
- 複製されない内容:
  - 案件ID（新規採番）
  - 作成日時・更新日時（新規作成時刻）
  - 費用項目のステータス（すべて「発注予定」にリセット）
  - 発注番号（クリア）

---

### 2.6 費用項目管理

#### 2.6.1 費用項目情報
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

#### 2.6.2 ステータス管理
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

### 2.7 発注メール自動生成機能

#### 2.7.1 発注番号の自動採番
- 形式: `RB-YYYYMMDD-XXX`
- 例: `RB-20250809-001`
- 日付ごとに連番
- 重複チェック機能

#### 2.7.2 メールテンプレート
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

#### 2.7.3 変数の自動置換
- 発注先マスタから担当者名を取得
- 案件情報から案件名・実施日を取得
- 費用項目から金額・項目名を取得
- 設定ファイルから署名を取得

---

### 2.8 Gmail連携機能

#### 2.8.1 使用プロトコル
- **IMAP**: Gmail接続
- **対象**: Google Workspace アカウント
- **認証**: メールアドレス + アプリパスワード

#### 2.8.2 下書き作成機能
1. ユーザーが「発注メール作成」ボタンをクリック
2. メールテンプレートに情報を埋め込み
3. IMAPでGmail [Gmail]/Drafts に下書き保存
4. 下書きIDをDBに記録
5. ステータスを「下書き作成済」に更新
6. (オプション) ブラウザでGmail下書きを開く

#### 2.8.3 送信確認機能
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

#### 2.8.4 Gmail設定
- 初回起動時または設定画面で入力
- メールアドレス
- アプリパスワード
- 署名
- 設定ファイル (config.py) に保存

---

### 2.9 アラート機能

#### 2.9.1 請求書未着アラート
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

#### 2.9.2 下書き未送信アラート
**条件:**
- ステータスが「下書き作成済」
- 下書き作成から24時間以上経過

**表示:**
```
📧 下書き未送信: 2件
- 8/15 番組B - 加藤出演料 (加藤プロ/山田)
```

#### 2.9.3 アラート表示位置
- 発注管理タブの上部に常時表示
- 該当項目がある場合のみ表示
- クリックで該当項目にジャンプ

---

### 2.10 履歴管理

#### 2.10.1 発注履歴 (order_history)
- 発注番号ごとの履歴
- メール件名・本文の記録
- 送信日時・送信先の記録
- Gmail下書きID・メッセージIDの記録

#### 2.10.2 ステータス履歴 (status_history)
- ステータス変更の履歴
- 変更日時の記録
- 備考の記録

---

## 3. データベース設計

### 3.1 テーブル一覧

#### 3.1.1 partners (統合取引先マスタ) ✅ **実装済み**
```sql
CREATE TABLE partners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                             -- 取引先名
    code TEXT UNIQUE,                               -- 取引先コード
    contact_person TEXT,                            -- 担当者名
    email TEXT,                                     -- メールアドレス
    phone TEXT,                                     -- 電話番号
    address TEXT,                                   -- 住所
    partner_type TEXT DEFAULT '両方',               -- 取引先区分（発注先/支払先/両方）
    notes TEXT,                                     -- 備考
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 programs (番組マスター) ✅ **実装済み**
```sql
CREATE TABLE programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                      -- 番組名
    description TEXT,                               -- 備考
    start_date DATE,                                -- 開始日
    end_date DATE,                                  -- 終了日
    broadcast_time TEXT,                            -- 放送時間
    broadcast_days TEXT,                            -- 放送曜日（CSV形式）
    status TEXT DEFAULT '放送中',                   -- ステータス（放送中/終了）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.3 cast (出演者マスター) ✅ **実装済み**
```sql
CREATE TABLE cast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                      -- 出演者名
    partner_id INTEGER NOT NULL,                    -- 所属事務所ID（partners参照）
    notes TEXT,                                     -- 備考
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partner_id) REFERENCES partners(id)
);
```

#### 3.1.4 program_cast (番組-出演者紐付け) ✅ **実装済み**
```sql
CREATE TABLE program_cast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,                    -- 番組ID
    cast_id INTEGER NOT NULL,                       -- 出演者ID
    role TEXT,                                      -- 役割（MC、アシスタント等）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
    FOREIGN KEY (cast_id) REFERENCES cast(id) ON DELETE CASCADE
);
```

#### 3.1.5 program_producers (番組-制作会社紐付け) ✅ **実装済み**
```sql
CREATE TABLE program_producers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,                    -- 番組ID
    partner_id INTEGER NOT NULL,                    -- 制作会社ID（partners参照）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE
);
```

#### 3.1.6 suppliers (発注先マスタ) ⚠️ **廃止予定**
```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**注記:** partners テーブルに統合済み。後方互換性のため残存。

#### 3.1.7 projects (案件マスタ) ✅ **実装済み**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                             -- 案件名
    date DATE NOT NULL,                             -- 実施日（単発案件用）
    type TEXT NOT NULL,                             -- レギュラー/単発
    budget REAL DEFAULT 0,                          -- 予算額
    parent_id INTEGER,                              -- 親案件ID (階層用)
    start_date DATE,                                -- 開始日（レギュラー案件用）
    end_date DATE,                                  -- 終了日（レギュラー案件用）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES projects(id)
);
```

#### 3.1.8 expenses_order (費用項目) ✅ **実装済み**
```sql
CREATE TABLE expenses_order (
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

#### 3.1.9 order_history (発注履歴) ✅ **実装済み**
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
    FOREIGN KEY (expense_id) REFERENCES expenses_order(id)
);
```

#### 3.1.10 status_history (ステータス履歴) ✅ **実装済み**
```sql
CREATE TABLE status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,                    -- 費用項目ID
    old_status TEXT,                                -- 旧ステータス
    new_status TEXT,                                -- 新ステータス
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                                     -- 備考
    FOREIGN KEY (expense_id) REFERENCES expenses_order(id)
);
```

### 3.2 データベースファイル
- **order_management.db**: 発注管理機能専用データベース
- 既存の支払い管理データベースとは独立

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
- **発注管理** ← 実装済み

### 4.2 発注管理タブの構成 ✅ **実装済み**

#### 4.2.1 サブタブ
```
[案件一覧] [取引先マスター] [出演者マスター] [番組マスター] [設定]
```

#### 4.2.2 案件一覧画面
- 案件リスト表示
- フィルター機能（タイプ別）
- 新規案件作成・編集・複製・削除
- 予算・実績・残予算の表示
- 日付のタイプ別表示

#### 4.2.3 取引先マスター画面
- 取引先一覧表示
- 検索機能
- 取引先区分フィルター
- 新規追加・編集・削除

#### 4.2.4 出演者マスター画面
- 出演者一覧表示
- 所属事務所情報表示
- 検索機能
- 新規追加・編集・削除

#### 4.2.5 番組マスター画面
- 番組一覧表示
- 番組情報（放送時間、曜日、ステータス）
- 出演者リスト管理
- 制作会社リスト管理
- ステータスフィルター
- 検索機能
- 新規追加・編集・削除

#### 4.2.6 設定画面
- Gmail設定
- メール署名設定

---

## 5. 既存システムとの統合

### 5.1 app.py への追加 ✅ **実装済み**

#### 5.1.1 インポート追加
```python
from order_management_tab import OrderManagementTab
```

#### 5.1.2 タブ追加
```python
# 発注管理タブ
self.order_management_tab = OrderManagementTab(tab_control, self)
tab_control.addTab(self.order_management_tab, '発注管理')
```

### 5.2 database.py への追加 ✅ **実装済み**

```python
# データベース初期化メソッドに追加
self._create_order_management_tables()
```

### 5.3 config.py への追加 ✅ **実装済み**

```python
# Gmail IMAP設定
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# タブ名追加
TAB_NAMES = {
    'payment': '支払い',
    'expense': '費用管理',
    'master': '費用マスター',
    'project_filter': '案件絞込み',
    'monitoring': '監視機能',
    'order_management': '発注管理',
}
```

---

## 6. 実装計画と実装状況

### Phase 1: 基礎構築 ✅ **完了**
- ✅ データベース拡張
- ✅ 発注先マスタ機能
- ✅ 基本UI構築

### Phase 2: Gmail連携 ✅ **完了**
- ✅ Gmail設定機能
- ✅ メール自動生成
- ✅ Gmail下書き作成
- ✅ 送信確認機能

### Phase 3: コア機能 ✅ **完了**
- ✅ 案件管理
- ✅ 費用項目管理
- ✅ ツリービュー
- ✅ アラート機能

### Phase 4: 予算管理 ✅ **完了**
- ✅ 予算設定
- ✅ 予算集計
- ✅ 表示機能

### Phase 5: 拡張機能 ✅ **完了**
- ✅ レギュラー案件の日付管理（開始日・終了日）
- ✅ 案件複製機能

### Phase 6: 取引先マスタ統合 ✅ **完了**
- ✅ 新テーブル `partners` の作成
- ✅ 統合取引先マスタUI
- ✅ 取引先区分による表示切り替え
- ✅ 番組マスター・出演者マスターとの連携

### Phase 7: 番組マスター機能 ✅ **完了**
- ✅ 番組マスターDB設計
- ✅ 番組マスターUI
- ✅ 出演者管理機能
- ✅ 制作会社管理機能
- ✅ 番組編集ダイアログ

### Phase 8: 出演者マスター機能 ✅ **完了**
- ✅ 出演者マスターDB設計
- ✅ 出演者マスターUI
- ✅ 所属事務所連携
- ✅ 番組マスターとの連携
- ✅ 出演者編集ダイアログ

---

## 7. 実装済み機能の詳細

### 7.1 データベース層 ✅ **実装済み**
**実装ファイル:**
- `database.py`: テーブル定義と自動マイグレーション
- `order_management/database_manager.py`: CRUD操作

**主要メソッド:**
- `get_partners()`: 統合取引先一覧取得
- `save_partner()`: 統合取引先保存
- `get_suppliers()`: 発注先一覧取得（互換性）
- `save_supplier()`: 発注先保存（互換性）
- `get_projects()`: 案件一覧取得
- `save_project()`: 案件保存
- `duplicate_project()`: 案件複製
- `get_expenses_by_project()`: 案件別費用項目取得
- `save_expense_order()`: 費用項目保存
- `get_project_summary()`: 予算・実績集計
- `get_programs()`: 番組一覧取得
- `save_program()`: 番組保存
- `get_program_cast_v2()`: 番組の出演者リスト取得
- `save_program_cast_v2()`: 番組の出演者保存
- `get_program_producers()`: 番組の制作会社リスト取得
- `save_program_producers()`: 番組の制作会社保存
- `get_casts()`: 出演者一覧取得
- `save_cast()`: 出演者保存
- `delete_cast()`: 出演者削除

### 7.2 Gmail連携層 ✅ **実装済み**
**実装ファイル:**
- `order_management/gmail_manager.py`: IMAP接続・下書き作成・送信確認
- `order_management/email_template.py`: メールテンプレート生成
- `order_management/order_number_generator.py`: 発注番号自動採番

**主要機能:**
- Gmail IMAP接続（アプリパスワード認証）
- 下書きメール作成
- 送信済みメール検索
- 発注番号自動生成（RB-YYYYMMDD-XXX形式）

### 7.3 UI層 ✅ **実装済み**
**実装ファイル:**
- `order_management_tab.py`: メインタブ
- `order_management/ui/projects_main_widget.py`: 案件メイン画面
- `order_management/ui/project_list_widget.py`: 案件一覧
- `order_management/ui/project_edit_dialog.py`: 案件編集
- `order_management/ui/expense_edit_dialog.py`: 費用項目編集
- `order_management/ui/project_tree_widget.py`: ツリービュー
- `order_management/ui/partner_master_widget.py`: 統合取引先マスタ
- `order_management/ui/program_master_widget.py`: 番組マスター
- `order_management/ui/program_edit_dialog.py`: 番組編集
- `order_management/ui/cast_master_widget.py`: 出演者マスター
- `order_management/ui/cast_edit_dialog.py`: 出演者編集
- `order_management/ui/producer_select_dialog.py`: 制作会社選択（共通）
- `order_management/ui/alert_widget.py`: アラート表示
- `order_management/ui/settings_widget.py`: Gmail設定
- `order_management/ui/ui_helpers.py`: UI共通ヘルパー関数

**主要UI機能:**
- タブ構成（案件一覧・取引先マスター・出演者マスター・番組マスター・設定）
- 案件フィルタリング（タイプ別）
- 予算・実績・残予算の表示
- 条件付き日付フィールド表示
- 案件複製ボタン
- 発注メール下書き作成
- アラート表示（請求書未着・下書き未送信）
- 番組管理（出演者・制作会社）
- 出演者管理（所属事務所連携）

### 7.4 アラート機能 ✅ **実装済み**
**実装ファイル:**
- `order_management/alert_manager.py`: アラート検出ロジック

**アラート種別:**
- 請求書未着アラート（実施日翌日経過）
- 下書き未送信アラート（24時間経過）

### 7.5 モデル層 ✅ **実装済み**
**実装ファイル:**
- `order_management/models.py`: データクラス定義

**データクラス:**
- `Partner`: 統合取引先マスタ
- `Supplier`: 発注先マスタ（互換性）
- `Project`: 案件マスタ
- `ExpenseOrder`: 費用項目
- `OrderHistory`: 発注履歴
- `StatusHistory`: ステータス履歴
- `Program`: 番組マスタ
- `Cast`: 出演者マスタ

---

## 8. ファイル構成

```
BillingManager2.0/
├── app.py                          # メインアプリ
├── database.py                     # DB管理
├── config.py                       # 設定
│
├── order_management_tab.py         # ✅ 発注管理タブのメインクラス
├── order_management/               # ✅ 発注管理モジュール
│   ├── __init__.py
│   ├── models.py                   # ✅ データモデル
│   ├── database_manager.py         # ✅ 発注管理用DB操作
│   ├── gmail_manager.py            # ✅ Gmail IMAP連携
│   ├── email_template.py           # ✅ メールテンプレート
│   ├── order_number_generator.py   # ✅ 発注番号生成
│   ├── alert_manager.py            # ✅ アラート機能
│   ├── config.py                   # ✅ 発注管理設定
│   ├── migrate_expense_master.py   # データマイグレーション
│   │
│   ├── ui/                         # ✅ UI関連
│   │   ├── __init__.py
│   │   ├── projects_main_widget.py # ✅ 案件メイン画面
│   │   ├── project_list_widget.py  # ✅ 案件一覧
│   │   ├── project_tree_widget.py  # ✅ ツリービュー
│   │   ├── project_edit_dialog.py  # ✅ 案件編集
│   │   ├── expense_edit_dialog.py  # ✅ 費用項目編集
│   │   ├── partner_master_widget.py # ✅ 統合取引先マスタ
│   │   ├── program_master_widget.py # ✅ 番組マスター
│   │   ├── program_edit_dialog.py  # ✅ 番組編集
│   │   ├── cast_master_widget.py   # ✅ 出演者マスター
│   │   ├── cast_edit_dialog.py     # ✅ 出演者編集
│   │   ├── producer_select_dialog.py # ✅ 制作会社選択（共通）
│   │   ├── supplier_master_widget.py # ⚠️ 発注先マスタ（旧版・非推奨）
│   │   ├── gmail_settings_dialog.py # ✅ Gmail設定
│   │   ├── alert_widget.py         # ✅ アラート表示
│   │   ├── settings_widget.py      # ✅ 設定ウィジェット
│   │   └── ui_helpers.py           # ✅ UI共通ヘルパー
│   │
│   └── utils/                      # ユーティリティ
│       └── __init__.py
│
├── order_management.db             # ✅ 発注管理データベース
├── requirements_order_management.md # この要件定義書
└── test_project_dates.py           # テストスクリプト
```

**凡例:**
- ✅: 実装済み
- ⚠️: 廃止予定（互換性のため残存）

---

## 9. 今後の拡張予定

### 9.1 高優先度
- 発注メール送信機能の完全自動化
- 請求書PDFの自動取り込み
- 支払い管理機能との統合

### 9.2 中優先度
- モバイル対応
- レポート機能（月次・年次集計）
- データエクスポート機能（Excel、CSV）

### 9.3 低優先度
- 複数ユーザー対応
- 権限管理
- 監査ログ

---

**要件定義書 終わり**

**最終更新: 2025-11-01**
**実装状況: 全Phase完了、運用フェーズ**
