# BillingManager2.0 データベース構造ドキュメント

## 目次
1. [データベース概要](#データベース概要)
2. [全テーブルスキーマ詳細](#全テーブルスキーマ詳細)
3. [タブとデータベースの対応関係](#タブとデータベースの対応関係)
4. [ER図とリレーション](#er図とリレーション)
5. [データフロー](#データフロー)
6. [インデックス情報](#インデックス情報)

---

## データベース概要

このアプリケーションでは **5つの主要データベース** を使用しています：

| データベース | ファイルパス | 役割 | 主要テーブル数 |
|------------|------------|------|--------------|
| **order_management.db** | `database/order_management.db` | 発注・契約・番組管理のメインDB | 10 |
| **billing.db** | `billing.db` | CSV支払いデータの管理 | 1 |
| **expense_master.db** | `expense_master.db` | 定期費用マスタデータ | 1 |
| **payee_master.db** | `payee_master.db` | 支払先マスタデータ | 1 |
| **expenses.db** | `database/expenses.db` | （未使用） | 0 |

### データベースの役割分担

- **order_management.db**: アプリケーションのコア。番組、契約、費用項目、取引先、出演者など全ての発注管理データを管理
- **billing.db**: CSVからインポートした支払い実績データを保存。`order_management.db`と照合される
- **expense_master.db**: 定期的に発生する費用のテンプレートを保存
- **payee_master.db**: 支払先名と支払先コードのマッピング（自動補完用）
- **expenses.db**: 現在未使用（将来の拡張用）

---

## 全テーブルスキーマ詳細

### 1. billing.db

#### paymentsテーブル（支払い情報）

CSVからインポートされた支払い実績データを格納。

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 支払いID（主キー） |
| subject | TEXT | - | - | 件名 |
| project_name | TEXT | - | - | プロジェクト名 |
| payee | TEXT | - | - | 支払先名 |
| payee_code | TEXT | - | - | 支払先コード |
| amount | REAL | - | - | 金額 |
| payment_date | TEXT | - | - | 支払日（ISO形式文字列） |
| status | TEXT | - | '未処理' | ステータス（未処理/処理中/処理済/照合済） |
| type | TEXT | - | '' | タイプ |
| client_name | TEXT | - | '' | クライアント名 |
| department | TEXT | - | '' | 部署 |
| project_status | TEXT | - | '進行中' | プロジェクトステータス |
| project_start_date | TEXT | - | '' | プロジェクト開始日 |
| project_end_date | TEXT | - | '' | プロジェクト終了日 |
| budget | REAL | - | 0 | 予算 |
| approver | TEXT | - | '' | 承認者 |
| urgency_level | TEXT | - | '通常' | 緊急度レベル |

**用途**: 支払い実績の記録、費用項目との照合

---

### 2. order_management.db

発注・契約・番組管理のメインデータベース。10個のテーブルで構成。

#### 2.1 productionsテーブル（番組・イベント情報）

番組やイベントの基本情報を管理。

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 番組ID |
| name | TEXT | NOT NULL UNIQUE | - | 番組名（一意） |
| description | TEXT | - | - | 説明 |
| start_date | DATE | - | - | 開始日 |
| end_date | DATE | - | - | 終了日 |
| status | TEXT | - | 'active' | ステータス（active/終了） |
| production_type | TEXT | - | 'レギュラー' | 番組タイプ（レギュラー/イベント/特番/コーナー） |
| start_time | TEXT | - | - | 開始時刻 |
| end_time | TEXT | - | - | 終了時刻 |
| broadcast_time | TEXT | - | - | 放送時間 |
| broadcast_days | TEXT | - | - | 放送曜日 |
| parent_production_id | INTEGER | FK to productions(id) | - | 親番組ID（コーナーの場合） |
| parent_production_name | TEXT | - | - | 親番組名 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新日時 |

**インデックス**:
- `idx_productions_name` (name)
- `idx_productions_status` (status)
- `idx_productions_type` (production_type)
- `idx_productions_parent` (parent_production_id)

**用途**: 番組マスタ、番組別集計の基準

---

#### 2.2 partnersテーブル（取引先情報）

取引先・業者の詳細情報を管理。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 取引先ID |
| name | TEXT | NOT NULL UNIQUE | 取引先名（一意） |
| name_kana | TEXT | - | フリガナ |
| company_type | TEXT | - | 会社種別 |
| postal_code | TEXT | - | 郵便番号 |
| address | TEXT | - | 住所 |
| phone | TEXT | - | 電話番号 |
| email | TEXT | - | メールアドレス |
| contact_person | TEXT | - | 担当者名 |
| payment_terms | TEXT | - | 支払条件 |
| bank_name | TEXT | - | 銀行名 |
| bank_branch | TEXT | - | 支店名 |
| account_type | TEXT | - | 口座種別 |
| account_number | TEXT | - | 口座番号 |
| account_holder | TEXT | - | 口座名義 |
| notes | TEXT | - | 備考 |
| created_at | TIMESTAMP | - | 作成日時 |
| updated_at | TIMESTAMP | - | 更新日時 |

**インデックス**:
- `idx_partners_name` (name)

**用途**: 取引先マスタ、契約・費用項目との紐付け

---

#### 2.3 contractsテーブル（契約情報）

番組と取引先間の契約を管理。自動延長機能あり。

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 契約ID |
| production_id | INTEGER | FK to productions(id) ON DELETE CASCADE | - | 番組ID |
| project_id | INTEGER | - | - | プロジェクトID（将来用） |
| partner_id | INTEGER | FK to partners(id), NOT NULL | - | 取引先ID |
| work_type | TEXT | - | '制作' | 作業種別 |
| item_name | TEXT | NOT NULL | - | 契約項目名 |
| contract_type | TEXT | - | 'regular_fixed' | 契約タイプ |
| contract_start_date | DATE | NOT NULL | - | 契約開始日 |
| contract_end_date | DATE | NOT NULL | - | 契約終了日 |
| contract_period_type | TEXT | - | '半年' | 契約期間タイプ |
| payment_type | TEXT | - | '月額固定' | 支払タイプ |
| unit_price | REAL | - | - | 単価 |
| spot_amount | REAL | - | - | スポット金額 |
| payment_timing | TEXT | - | '翌月末払い' | 支払タイミング |
| document_type | TEXT | - | '発注書' | 書類種別 |
| document_status | TEXT | - | '未' | 書類ステータス（未/作成中/完了） |
| pdf_file_path | TEXT | - | - | PDFファイルパス |
| email_to | TEXT | - | - | 送信先メールアドレス |
| email_subject | TEXT | - | - | メール件名 |
| email_body | TEXT | - | - | メール本文 |
| email_sent_date | DATE | - | - | メール送信日 |
| auto_renewal_enabled | INTEGER | - | 1 | 自動延長有効フラグ（1=有効） |
| renewal_period_months | INTEGER | - | 3 | 延長期間（月数） |
| termination_notice_date | DATE | - | - | 解約通知日 |
| last_renewal_date | DATE | - | - | 最終延長日 |
| renewal_count | INTEGER | - | 0 | 延長回数 |
| notes | TEXT | - | - | 備考 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新日時 |

**インデックス**:
- `idx_contracts_production` (production_id)
- `idx_contracts_partner` (partner_id)
- `idx_contracts_dates` (contract_start_date, contract_end_date)
- `idx_contracts_work_type` (work_type)

**外部キー**:
- `production_id` → `productions(id)` ON DELETE CASCADE
- `partner_id` → `partners(id)`

**用途**: 契約管理、自動延長、発注書生成、費用項目の自動生成元

---

#### 2.4 expense_itemsテーブル（費用項目）

個別の費用項目と支払状況を管理。契約から自動生成される場合もある。

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 費用項目ID |
| contract_id | INTEGER | FK to contracts(id) ON DELETE SET NULL | - | 契約ID（契約から生成された場合） |
| production_id | INTEGER | FK to productions(id) ON DELETE CASCADE, NOT NULL | - | 番組ID |
| partner_id | INTEGER | FK to partners(id) | - | 取引先ID |
| item_name | TEXT | NOT NULL | - | 項目名 |
| work_type | TEXT | - | '制作' | 作業種別 |
| amount | REAL | NOT NULL | - | 金額 |
| implementation_date | DATE | - | - | 実施日 |
| order_number | TEXT | UNIQUE | - | 発注番号 |
| order_date | DATE | - | - | 発注日 |
| status | TEXT | - | '発注予定' | ステータス（発注予定/発注済/請求書受領/支払完了） |
| invoice_received_date | DATE | - | - | 請求書受領日 |
| expected_payment_date | DATE | - | - | 支払予定日 |
| expected_payment_amount | REAL | - | - | 支払予定金額 |
| payment_scheduled_date | DATE | - | - | 支払予定日（スケジュール） |
| actual_payment_date | DATE | - | - | 実際の支払日 |
| payment_status | TEXT | - | '未払い' | 支払ステータス（未払い/支払済） |
| payment_verified_date | DATE | - | - | 支払確認日 |
| payment_matched_id | INTEGER | - | - | 照合済み支払ID（billing.dbのpayments.id） |
| payment_difference | REAL | - | 0 | 支払差額 |
| invoice_number | TEXT | - | - | 請求書番号 |
| withholding_tax | REAL | - | - | 源泉徴収税 |
| consumption_tax | REAL | - | - | 消費税 |
| payment_amount | REAL | - | - | 支払金額 |
| invoice_file_path | TEXT | - | - | 請求書ファイルパス |
| payment_method | TEXT | - | - | 支払方法 |
| approver | TEXT | - | - | 承認者 |
| approval_date | DATE | - | - | 承認日 |
| gmail_draft_id | TEXT | - | - | Gmail下書きID |
| gmail_message_id | TEXT | - | - | GmailメッセージID |
| email_sent_at | TIMESTAMP | - | - | メール送信日時 |
| contact_person | TEXT | - | - | 担当者 |
| notes | TEXT | - | - | 備考 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新日時 |

**インデックス**:
- `idx_expense_items_contract` (contract_id)
- `idx_expense_items_production` (production_id)
- `idx_expense_items_partner` (partner_id)
- `idx_expense_items_payment_date` (expected_payment_date)
- `idx_expense_items_status` (status, payment_status)
- `idx_expense_items_work_type` (work_type)

**外部キー**:
- `contract_id` → `contracts(id)` ON DELETE SET NULL
- `production_id` → `productions(id)` ON DELETE CASCADE
- `partner_id` → `partners(id)`

**用途**: 費用項目管理、支払い照合、番組別費用集計

---

#### 2.5 castテーブル（出演者情報）

出演者・パーソナリティの情報を管理。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 出演者ID |
| name | TEXT | NOT NULL | 出演者名 |
| partner_id | INTEGER | FK to partners(id) | 所属事務所（partnersテーブル） |
| notes | TEXT | - | 備考 |
| created_at | TIMESTAMP | - | 作成日時 |
| updated_at | TIMESTAMP | - | 更新日時 |

**インデックス**:
- `idx_cast_partner` (partner_id)

**外部キー**:
- `partner_id` → `partners(id)`

**用途**: 出演者マスタ、番組・契約との紐付け

---

#### 2.6 contract_castテーブル（契約-出演者関連）

契約と出演者の多対多関係を管理。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | ID |
| contract_id | INTEGER | FK to contracts(id) ON DELETE CASCADE, NOT NULL | 契約ID |
| cast_id | INTEGER | FK to cast(id) ON DELETE CASCADE, NOT NULL | 出演者ID |
| role | TEXT | - | 役割・担当 |
| created_at | TIMESTAMP | - | 作成日時 |

**制約**:
- UNIQUE(contract_id, cast_id) - 同じ契約に同じ出演者は重複登録不可

**インデックス**:
- `idx_contract_cast_contract` (contract_id)
- `idx_contract_cast_cast` (cast_id)

**外部キー**:
- `contract_id` → `contracts(id)` ON DELETE CASCADE
- `cast_id` → `cast(id)` ON DELETE CASCADE

**用途**: 契約詳細での出演者情報表示

---

#### 2.7 production_castテーブル（番組-出演者関連）

番組と出演者の多対多関係を管理。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | ID |
| production_id | INTEGER | FK to productions(id) ON DELETE CASCADE, NOT NULL | 番組ID |
| cast_id | INTEGER | FK to cast(id) ON DELETE CASCADE, NOT NULL | 出演者ID |
| role | TEXT | - | 役割・担当 |
| start_date | DATE | - | 出演開始日 |
| end_date | DATE | - | 出演終了日 |
| created_at | TIMESTAMP | - | 作成日時 |

**制約**:
- UNIQUE(production_id, cast_id) - 同じ番組に同じ出演者は重複登録不可

**インデックス**:
- `idx_production_cast_production` (production_id)
- `idx_production_cast_cast` (cast_id)

**外部キー**:
- `production_id` → `productions(id)` ON DELETE CASCADE
- `cast_id` → `cast(id)` ON DELETE CASCADE

**用途**: 番組詳細での出演者情報表示

---

#### 2.8 contract_renewal_historyテーブル（契約更新履歴）

契約の自動延長履歴を記録。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 履歴ID |
| contract_id | INTEGER | FK to contracts(id) ON DELETE CASCADE, NOT NULL | 契約ID |
| renewal_date | DATE | NOT NULL | 更新実行日 |
| old_end_date | DATE | - | 旧終了日 |
| new_end_date | DATE | - | 新終了日 |
| notes | TEXT | - | 備考 |
| created_at | TIMESTAMP | - | 作成日時 |

**インデックス**:
- `idx_contract_renewal_contract` (contract_id)

**外部キー**:
- `contract_id` → `contracts(id)` ON DELETE CASCADE

**用途**: 契約延長の監査証跡

---

#### 2.9 order_historyテーブル（発注履歴）

費用項目の変更履歴を記録。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 履歴ID |
| expense_id | INTEGER | FK to expense_items(id), NOT NULL | 費用項目ID |
| action | TEXT | NOT NULL | アクション（作成/更新/削除など） |
| old_value | TEXT | - | 変更前の値 |
| new_value | TEXT | - | 変更後の値 |
| changed_at | TIMESTAMP | - | 変更日時 |
| notes | TEXT | - | 備考 |

**インデックス**:
- `idx_order_history_expense` (expense_id)

**外部キー**:
- `expense_id` → `expense_items(id)`

**用途**: 変更履歴の追跡、監査証跡

---

#### 2.10 status_historyテーブル（ステータス履歴）

費用項目のステータス変更履歴を記録。

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 履歴ID |
| expense_id | INTEGER | FK to expense_items(id), NOT NULL | 費用項目ID |
| old_status | TEXT | - | 変更前ステータス |
| new_status | TEXT | - | 変更後ステータス |
| changed_at | TIMESTAMP | - | 変更日時 |
| notes | TEXT | - | 備考 |

**インデックス**:
- `idx_status_history_expense` (expense_id)

**外部キー**:
- `expense_id` → `expense_items(id)`

**用途**: ステータス変更の追跡

---

#### 2.11 schema_versionsテーブル（スキーマバージョン管理）

データベースマイグレーション履歴を管理。

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | ID |
| version | INTEGER | UNIQUE NOT NULL | - | バージョン番号 |
| migration_name | TEXT | NOT NULL | - | マイグレーション名 |
| applied_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 適用日時 |
| checksum | TEXT | - | - | チェックサム |
| success | BOOLEAN | - | 1 | 成功フラグ |
| error_message | TEXT | - | - | エラーメッセージ |

**用途**: データベーススキーマのバージョン管理

---

### 3. expense_master.db

#### expense_masterテーブル（費用マスタ）

定期的に発生する費用のテンプレートを保存。

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|---------|-----------|------|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | - | ID |
| project_name | TEXT | - | プロジェクト名 |
| payee | TEXT | - | 支払先名 |
| payee_code | TEXT | - | 支払先コード |
| amount | REAL | - | 金額 |
| payment_date | TEXT | - | 支払日 |
| status | TEXT | '未処理' | ステータス |
| payment_type | TEXT | '月額固定' | 支払タイプ（月額固定/回数ベース） |
| start_date | TEXT | - | 開始日 |
| end_date | TEXT | - | 終了日 |
| broadcast_days | TEXT | - | 放送曜日 |
| client_name | TEXT | '' | クライアント名 |
| department | TEXT | '' | 部署 |
| project_status | TEXT | '進行中' | プロジェクトステータス |
| project_start_date | TEXT | '' | プロジェクト開始日 |
| project_end_date | TEXT | '' | プロジェクト終了日 |
| budget | REAL | 0 | 予算 |
| approver | TEXT | '' | 承認者 |
| urgency_level | TEXT | '通常' | 緊急度 |
| payment_timing | TEXT | '翌月末払い' | 支払タイミング |

**用途**: 定期費用のテンプレート、発注マスタへの変換元

---

### 4. payee_master.db

#### payee_masterテーブル（支払先マスタ）

支払先名と支払先コードのマッピング。自動補完機能で使用。

| カラム名 | データ型 | 制約 | デフォルト値 | 説明 |
|---------|---------|------|------------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | ID |
| payee_name | TEXT | UNIQUE | - | 支払先名（一意） |
| payee_code | TEXT | - | - | 支払先コード |
| created_date | TEXT | - | CURRENT_TIMESTAMP | 作成日 |
| updated_date | TEXT | - | CURRENT_TIMESTAMP | 更新日 |

**用途**: 支払先入力時の自動補完、コードの自動入力

---

## タブとデータベースの対応関係

アプリケーションは **8つのメインタブ** で構成されており、それぞれが異なるデータベーステーブルと連携しています。

### タブ1: 📺 費用項目管理

**ファイル**: `order_management/ui/expense_items_widget.py`

**使用テーブル**:
- `expense_items` (order_management.db) - **メイン**
- `productions` (order_management.db) - 番組情報参照
- `partners` (order_management.db) - 取引先情報参照
- `contracts` (order_management.db) - 契約情報参照
- `payments` (billing.db) - 支払照合用

**主要機能**:
- ✅ 費用項目の一覧表示・編集・削除
- 🔍 支払状態フィルタリング（未払い/支払済）
- ⚠️ 期限超過アラート表示
- 📝 契約なし項目の検出
- 📋 未登録支払いの検出
- 📊 ダッシュボード統計（総件数、総額、未払い件数など）

**データフロー**:
```
契約 (contracts) → 費用項目自動生成 → expense_items
                                          ↓
                                    支払照合 ← payments (billing.db)
```

---

### タブ2: 💰 支払い情報

**ファイル**: `payment_tab.py`

**使用テーブル**:
- `payments` (billing.db) - **メイン**

**主要機能**:
- 📥 CSVからの支払いデータインポート
- 🎨 ステータス別色分け表示
  - 🟢 照合済（ライトグリーン）
  - 🔵 処理済（ライトブルー）
  - 🟡 処理中（黄色）
  - ⚪ 未処理（オフホワイト）
- 🔍 ステータスフィルタ（未処理/処理中/処理済/照合済/未照合）
- 📊 支払先、金額、日付の管理

**データフロー**:
```
CSV ファイル → インポート → payments → 自動照合 → expense_items
```

---

### タブ3: 📊 番組別費用詳細

**ファイル**: `order_management/ui/production_expense_detail_widget.py`

**使用テーブル**:
- `productions` (order_management.db) - 番組リスト
- `expense_items` (order_management.db) - 費用集計

**主要機能**:
- 📺 番組ごとの費用集計表示
- 📅 月別費用サマリー
- 💰 総費用額・未払い・支払済の集計
- 🎭 番組種別フィルタ（レギュラー/イベント/特番/コーナー）
- 📈 並び替え（総費用額順/月額平均順/未払い件数順）

**データフロー**:
```
productions (番組) ← 集計 ← expense_items (費用項目)
                              ↓
                        月別サマリー表示
```

---

### タブ4: 🎭 番組・イベント管理

**ファイル**: `order_management/ui/production_master_widget.py`

**使用テーブル**:
- `productions` (order_management.db) - **メイン**
- `production_cast` (order_management.db) - 番組-出演者関連
- `cast` (order_management.db) - 出演者情報

**主要機能**:
- ➕ 番組・イベントの新規追加
- ✏️ 番組情報の編集
- 🗑️ 番組の削除
- 🎪 番組種別管理（レギュラー/イベント/特番/コーナー）
- 📻 放送時間・曜日の設定
- 🔗 親子関係設定（コーナーと親番組）
- 📊 統計情報表示

**データフロー**:
```
productions ← 親子関係 → productions (parent_production_id)
     ↓
production_cast ← 関連付け → cast (出演者)
```

---

### タブ5: 📋 番組詳細

**ファイル**: `order_management/ui/production_detail_widget.py`

**使用テーブル**:
- `productions` (order_management.db)
- `expense_items` (order_management.db)
- `contracts` (order_management.db)
- `cast` (order_management.db)
- `production_cast` (order_management.db)

**主要機能**:
- 📅 月別番組一覧表示
- 🎬 単発番組 vs レギュラー番組の切り替え
- 📖 選択した番組の詳細情報表示
- 👥 出演者情報表示
- 💰 費用項目一覧表示
- 📊 契約情報表示

**データフロー**:
```
月選択 → productions フィルタ → 番組詳細表示
                                  ↓
                          cast, expense_items, contracts 参照
```

---

### タブ6: 👥 マスター管理

**ファイル**: `master_management_tab.py`

**サブタブ構成**:

#### サブタブ 6-1: 取引先マスター
**使用テーブル**:
- `partners` (order_management.db) - **メイン**

**主要機能**:
- 🏢 取引先情報の新規追加・編集・削除
- 💳 銀行口座情報の管理
- 📝 支払条件の設定
- 📇 連絡先情報の管理

#### サブタブ 6-2: 出演者マスター
**使用テーブル**:
- `cast` (order_management.db) - **メイン**
- `partners` (order_management.db) - 所属事務所

**主要機能**:
- 👤 出演者情報の新規追加・編集・削除
- 🏢 所属事務所との紐付け
- 📝 備考情報の管理

**リレーション**:
```
partners (所属事務所) ← 1:N → cast (出演者)
```

---

### タブ7: 📝 発注管理 - 契約一覧

**ファイル**: `order_management/ui/order_contract_widget.py`

**使用テーブル**:
- `contracts` (order_management.db) - **メイン**
- `productions` (order_management.db) - 番組情報
- `partners` (order_management.db) - 取引先情報
- `contract_cast` (order_management.db) - 契約-出演者関連
- `cast` (order_management.db) - 出演者情報
- `contract_renewal_history` (order_management.db) - 更新履歴
- `expense_items` (order_management.db) - 自動生成される費用項目

**主要機能**:
- 📄 契約情報の新規追加・編集・削除
- ⏰ 契約期限アラート（7日以内 = 🔴赤色表示）
- 🔄 契約自動延長機能
- 📋 PDF発注書の管理・生成
- 📧 メール送信機能
- 📊 発注状況サマリー（緊急対応/注意/未完了/正常）
- 🎨 色分け表示（赤=緊急、黄=注意、緑=完了、グレー=通常）

**データフロー**:
```
契約作成 → contracts
              ↓
        自動延長チェック → contract_renewal_history
              ↓
        費用項目自動生成 → expense_items
```

**リレーション**:
```
productions ← 1:N → contracts ← N:1 → partners
                       ↓
                    contract_cast ← M:N → cast
                       ↓
                    expense_items (自動生成)
                       ↓
                    contract_renewal_history
```

---

### タブ8: 🗂️ データ管理

**ファイル**: `data_management_tab.py`

**サブタブ構成**:

#### サブタブ 8-1: 費用管理
**ファイル**: `expense_tab.py`

**使用テーブル**:
- `expense_master` (expense_master.db) - **メイン**

**主要機能**:
- 📊 月次費用データの管理
- 🏢 プロジェクトごとの費用集計
- ✏️ 直接編集機能

#### サブタブ 8-2: 費用マスター
**ファイル**: `master_tab.py`

**使用テーブル**:
- `expense_master` (expense_master.db) - **メイン**

**主要機能**:
- 📝 定期的に発生する費用のテンプレート管理
- 🎨 支払タイプ別色分け
  - 🔵 月額固定（ライトブルー）
  - 🔴 回数ベース（ライトピンク）
- 📅 開始日・終了日の管理
- 💰 金額・支払タイミングの設定

#### サブタブ 8-3: 発注チェック
**ファイル**: `order_check_tab.py`

**使用テーブル**:
- `expense_master` (expense_master.db) - 読み取り
- `contracts` (order_management.db) - 照合先
- `expense_items` (order_management.db) - 追加先

**主要機能**:
- 🔍 費用マスターと発注マスタの照合
- ⚠️ 未登録項目の検出と表示
- ➕ 未登録項目の簡単追加（ワンクリック）
- 🎨 色分け表示（緑=登録済、黄=未登録）

**データフロー**:
```
expense_master → チェック → contracts との照合
                              ↓
                        未登録の場合 → 追加ダイアログ
                              ↓
                        contracts + expense_items 作成
```

#### サブタブ 8-4: 発注・支払照合
**ファイル**: `order_payment_reconciliation_tab.py`

**使用テーブル**:
- `expense_items` (order_management.db) - 発注データ
- `payments` (billing.db) - 支払データ

**主要機能**:
- 📅 月次支払予定リストの生成
- 🔗 実際の支払いデータとの照合
- 📊 月次サマリー表示（発注件数、総額、支払済件数など）
- 📄 差異レポート出力
- 🎨 照合状態の色分け表示

**データフロー**:
```
expense_items (発注予定) ← 照合 → payments (実績)
         ↓
   照合結果レポート
         ↓
   差異がある場合はアラート
```

---

## ER図とリレーション

### メインデータベース (order_management.db) のER図

```
┌─────────────────────────────────────────────────────────────┐
│                    order_management.db                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   productions    │ 番組・イベントマスタ
│                  │
│ ├ id (PK)        │
│ ├ name (UNIQUE)  │
│ ├ production_type│ (レギュラー/イベント/特番/コーナー)
│ ├ start_date     │
│ ├ end_date       │
│ └ parent_id (FK) ├─┐ 自己参照（親子関係）
└────────┬─────────┘ │
         │ 1         │
         │           └─────────────────┐
         │ N                           │
┌────────▼─────────────────────────────▼───┐        ┌─────────────────┐
│            contracts                     │   N    │    partners     │
│      契約情報（番組と取引先の契約）          ├────────┤   取引先マスタ   │
│                                          │   1    │                 │
│ ├ id (PK)                               │        │ ├ id (PK)       │
│ ├ production_id (FK) → productions      │        │ ├ name (UNIQUE) │
│ ├ partner_id (FK) → partners            │        │ ├ bank_name     │
│ ├ contract_start_date                   │        │ ├ account_number│
│ ├ contract_end_date                     │        │ └ ...           │
│ ├ payment_type (月額固定/回数ベース)      │        └────────┬────────┘
│ ├ auto_renewal_enabled                  │                 │ 1
│ └ ...                                    │                 │
└────────┬─────────────┬───────────────────┘                 │
         │ 1           │ 1                                   │ N
         │             │                              ┌──────▼──────┐
         │ N           │ N                            │    cast     │
┌────────▼──────┐ ┌───▼──────────────┐               │  出演者マスタ │
│expense_items  │ │contract_renewal  │               │             │
│  費用項目      │ │   _history       │               │ ├ id (PK)   │
│               │ │  契約更新履歴      │               │ ├ name      │
│ ├ id (PK)     │ │                  │               │ └ partner_id│
│ ├ contract_id │ │ ├ id (PK)        │               │    (FK)     │
│ ├ production  │ │ ├ contract_id    │               └──────┬──────┘
│ │  _id (FK)   │ │ ├ renewal_date   │                      │ N
│ ├ partner_id  │ │ ├ old_end_date   │                      │
│ ├ amount      │ │ └ new_end_date   │                      │ M
│ ├ payment     │ └──────────────────┘               ┌──────▼──────────┐
│ │  _status    │                                    │ contract_cast   │
│ ├ payment     │                                    │  契約-出演者関連  │
│ │  _matched_id│ ← 照合                              │                 │
│ └ ...         │                                    │ ├ id (PK)       │
└───────────────┘                                    │ ├ contract_id   │
         │ 1                                         │ │   (FK)        │
         │                                           │ └ cast_id (FK)  │
         │ N                                         └─────────────────┘
┌────────▼──────────┐                                         │ M
│ order_history     │                                         │
│  発注履歴          │                                         │ N
│                   │                                  ┌──────▼─────────┐
│ ├ id (PK)         │                                  │production_cast │
│ ├ expense_id (FK) │                                  │ 番組-出演者関連  │
│ ├ action          │                                  │                │
│ ├ old_value       │                                  │ ├ id (PK)      │
│ └ new_value       │                                  │ ├ production_id│
└───────────────────┘                                  │ │   (FK)       │
                                                       │ └ cast_id (FK) │
┌───────────────────┐                                  └────────────────┘
│ status_history    │
│ ステータス履歴      │
│                   │
│ ├ id (PK)         │
│ ├ expense_id (FK) │
│ ├ old_status      │
│ └ new_status      │
└───────────────────┘
```

### データベース間の連携図

```
┌─────────────────────────────────────────────────────────────┐
│                   データベース間連携                           │
└─────────────────────────────────────────────────────────────┘

billing.db                    order_management.db
┌─────────────┐              ┌──────────────────────────┐
│             │              │                          │
│  payments   │  自動照合     │    expense_items         │
│             ├─────────────→│                          │
│ ・CSV入力   │  起動時実行   │ ・発注管理               │
│ ・支払実績  │              │ ・payment_matched_id に  │
│             │              │   照合結果を記録         │
└─────────────┘              └──────────────────────────┘
                                         ▲
                                         │ チェック・変換
expense_master.db                        │
┌──────────────────┐                     │
│                  │  発注チェックタブ    │
│ expense_master   ├─────────────────────┘
│                  │
│ ・定期費用       │  未登録項目を検出
│ ・テンプレート   │  → contracts + expense_items 作成
└──────────────────┘

payee_master.db
┌──────────────────┐
│                  │  自動補完機能
│  payee_master    ├───────────→ 各タブの支払先入力フィールド
│                  │
│ ・支払先名       │  名前 → コード自動入力
│ ・支払先コード   │
└──────────────────┘
```

### 主要なリレーションシップ詳細

#### 1. 番組 ↔ 契約 ↔ 取引先

```
productions (1) ←──→ (N) contracts (N) ←──→ (1) partners

外部キー:
  contracts.production_id → productions.id (ON DELETE CASCADE)
  contracts.partner_id → partners.id

意味:
  1つの番組に複数の契約が存在
  1つの契約は1つの番組と1つの取引先を結ぶ
```

#### 2. 契約 ↔ 費用項目

```
contracts (1) ←──→ (N) expense_items

外部キー:
  expense_items.contract_id → contracts.id (ON DELETE SET NULL)

意味:
  1つの契約から複数の費用項目が自動生成される
  月額固定: 毎月自動生成
  回数ベース: 実施ごとに生成
```

#### 3. 契約 ↔ 出演者（多対多）

```
contracts (N) ←──→ (M) contract_cast (M) ←──→ (N) cast

外部キー:
  contract_cast.contract_id → contracts.id (ON DELETE CASCADE)
  contract_cast.cast_id → cast.id (ON DELETE CASCADE)

意味:
  1つの契約に複数の出演者が関連付けられる
  1人の出演者が複数の契約に関連付けられる
```

#### 4. 番組 ↔ 出演者（多対多）

```
productions (N) ←──→ (M) production_cast (M) ←──→ (N) cast

外部キー:
  production_cast.production_id → productions.id (ON DELETE CASCADE)
  production_cast.cast_id → cast.id (ON DELETE CASCADE)

意味:
  1つの番組に複数の出演者が出演
  1人の出演者が複数の番組に出演
```

#### 5. 取引先 ↔ 出演者

```
partners (1) ←──→ (N) cast

外部キー:
  cast.partner_id → partners.id

意味:
  1つの取引先（事務所）に複数の出演者が所属
```

#### 6. 番組の親子関係（自己参照）

```
productions (親) (1) ←──→ (N) productions (子)

外部キー:
  productions.parent_production_id → productions.id

意味:
  コーナーは親番組を持つ
  親番組は複数のコーナーを持つことができる
```

#### 7. 支払照合（データベース間）

```
expense_items (order_management.db)
        ↕ 照合
payments (billing.db)

照合条件:
  - 番組名（production_name）
  - 取引先名（payee/partner_name）
  - 金額（amount）
  - 支払日（payment_date/expected_payment_date）

照合結果:
  expense_items.payment_matched_id に payments.id を記録
  expense_items.payment_status を「支払済」に更新
```

---

## データフロー

### 1. 起動時の自動照合フロー

**ファイル**: `app.py:201-223`

```
アプリ起動
    ↓
1. CSVから最新データを billing.db にインポート（追記モード）
    ↓
2. 自動照合実行: _auto_reconcile_payments()
    ↓
3. order_db.reconcile_payments_with_expenses('billing.db')
    ↓
4. 照合条件チェック:
   - 番組名が一致
   - 取引先名が一致
   - 金額が一致
   - 支払日が範囲内
    ↓
5. 一致した場合:
   expense_items.payment_status = '支払済'
   expense_items.payment_matched_id = payments.id
   expense_items.actual_payment_date = payments.payment_date
    ↓
6. ログ出力:
   「照合成功=N件, 未照合費用=M件, 未照合支払=K件」
```

### 2. 契約から費用項目の自動生成フロー

```
契約作成・編集 (contracts)
    ↓
payment_type をチェック
    ↓
┌────────────────┴─────────────────┐
│                                  │
▼ 月額固定                         ▼ 回数ベース
│                                  │
契約期間中の各月について              実施ごとに手動で
expense_items を自動生成              expense_items を作成
│                                  │
↓                                  ↓
・production_id                    ・production_id
・partner_id                       ・partner_id
・contract_id                      ・contract_id
・amount (契約の unit_price)       ・amount (その都度入力)
・expected_payment_date            ・expected_payment_date
 (payment_timing に基づく)          (手動設定)
・payment_status = '未払い'         ・payment_status = '未払い'
```

### 3. 契約自動延長フロー

**ファイル**: `app.py:225-256`

```
アプリ起動
    ↓
契約自動延長チェック: _check_auto_renewal_on_startup()
    ↓
get_contracts_for_auto_renewal() を実行
    ↓
対象契約の条件:
  ・auto_renewal_enabled = 1
  ・contract_end_date が近い（例: 7日以内）
  ・termination_notice_date が設定されていない
    ↓
対象契約が存在する場合
    ↓
通知ダイアログを表示:
  「以下のN件の契約が自動延長の対象です」
  - 番組名 - 取引先名 - 終了日
    ↓
ユーザーが発注管理タブで「自動延長チェック」ボタンをクリック
    ↓
各契約について:
  1. contract_end_date を延長（renewal_period_months 分）
  2. renewal_count をインクリメント
  3. last_renewal_date を更新
  4. contract_renewal_history に履歴レコード追加
     - old_end_date
     - new_end_date
     - renewal_date
    ↓
月額固定の場合:
  延長期間分の expense_items を自動生成
```

### 4. CSVインポート → 支払照合フロー

```
1. CSVファイル準備（会計システムから出力）
    ↓
2. アプリ起動 または メニューから「データ再読込」
    ↓
3. import_latest_csv() 実行
    ↓
4. CSVデータを billing.db の payments テーブルにインポート
   - 上書きモード: 既存データ削除 → 新規挿入
   - 追記モード: 既存データ保持 → 追加のみ
    ↓
5. _auto_reconcile_payments() 自動実行
    ↓
6. order_management.db の expense_items と照合
    ↓
7. 照合成功:
   - expense_items.payment_status = '支払済'
   - expense_items.payment_matched_id = payments.id
   - payments.status = '照合済'
    ↓
8. 費用項目管理タブに反映
   - 支払済の行が色分け表示される
   - 未払い件数が減少
```

### 5. 費用マスター → 発注マスタ変換フロー

```
データ管理タブ > 発注チェック サブタブ
    ↓
expense_master テーブルから全レコード取得
    ↓
各レコードについて contracts テーブルを検索:
  ・project_name (番組名) で照合
  ・payee (取引先名) で照合
    ↓
┌────────────────┴─────────────────┐
│                                  │
▼ 照合成功（登録済）                ▼ 照合失敗（未登録）
│                                  │
緑色で表示                          黄色で表示
「登録済」                          「未登録」
│                                  │
↓                                  ↓
                                  「発注追加」ボタンが有効
                                  │
                                  ▼
                                  クリック
                                  │
                                  ▼
                              UnifiedOrderDialog 表示
                              （統合発注ダイアログ）
                                  │
                                  ▼
                              番組・取引先を選択
                              契約情報を入力
                                  │
                                  ▼
                              保存
                                  │
                                  ▼
                              contracts レコード作成
                              expense_items レコード作成（初回分）
                                  │
                                  ▼
                              order_added シグナル発火
                                  │
                                  ▼
                              発注管理タブのリスト更新
                              タブバッジ更新
```

### 6. 番組詳細表示フロー

```
番組詳細タブを開く
    ↓
1. 月選択コンボボックスで月を選択（例: 2025年01月）
    ↓
2. 番組タイプを選択（単発 or レギュラー）
    ↓
3. get_productions_for_month(month_str) または
   get_regular_productions() を実行
    ↓
4. 該当する番組のリストを左側に表示
    ↓
5. 番組を選択
    ↓
6. 以下の情報を並行して取得:
   ┌─────────────────────────────────┐
   │ production 詳細情報              │
   │ - 番組名、種別、放送時間など      │
   └─────────────────────────────────┘
   ┌─────────────────────────────────┐
   │ production_cast から出演者取得    │
   │ → cast 情報を表示                │
   └─────────────────────────────────┘
   ┌─────────────────────────────────┐
   │ expense_items 一覧取得           │
   │ - 費用項目リスト                 │
   │ - 支払状況                       │
   └─────────────────────────────────┘
   ┌─────────────────────────────────┐
   │ contracts 一覧取得               │
   │ - 契約情報                       │
   │ - 契約期間                       │
   └─────────────────────────────────┘
    ↓
7. 右側パネルに全情報を統合表示
```

---

## インデックス情報

パフォーマンス最適化のため、頻繁に検索・結合されるカラムにインデックスが設定されています。

### order_management.db のインデックス

#### productionsテーブル
- `idx_productions_name` ON `name` - 番組名での検索
- `idx_productions_status` ON `status` - ステータスフィルタ
- `idx_productions_type` ON `production_type` - 種別フィルタ
- `idx_productions_parent` ON `parent_production_id` - 親子関係の検索

#### partnersテーブル
- `idx_partners_name` ON `name` - 取引先名での検索

#### contractsテーブル
- `idx_contracts_production` ON `production_id` - 番組別契約一覧
- `idx_contracts_partner` ON `partner_id` - 取引先別契約一覧
- `idx_contracts_dates` ON `(contract_start_date, contract_end_date)` - 期間での検索
- `idx_contracts_work_type` ON `work_type` - 作業種別フィルタ

#### expense_itemsテーブル
- `idx_expense_items_contract` ON `contract_id` - 契約別費用項目
- `idx_expense_items_production` ON `production_id` - 番組別費用集計
- `idx_expense_items_partner` ON `partner_id` - 取引先別費用集計
- `idx_expense_items_payment_date` ON `expected_payment_date` - 支払日での検索
- `idx_expense_items_status` ON `(status, payment_status)` - ステータスフィルタ（複合）
- `idx_expense_items_work_type` ON `work_type` - 作業種別フィルタ

#### castテーブル
- `idx_cast_partner` ON `partner_id` - 所属事務所別出演者一覧

#### contract_castテーブル
- `idx_contract_cast_contract` ON `contract_id` - 契約別出演者一覧
- `idx_contract_cast_cast` ON `cast_id` - 出演者別契約一覧

#### production_castテーブル
- `idx_production_cast_production` ON `production_id` - 番組別出演者一覧
- `idx_production_cast_cast` ON `cast_id` - 出演者別番組一覧

#### contract_renewal_historyテーブル
- `idx_contract_renewal_contract` ON `contract_id` - 契約別更新履歴

#### order_historyテーブル
- `idx_order_history_expense` ON `expense_id` - 費用項目別履歴

#### status_historyテーブル
- `idx_status_history_expense` ON `expense_id` - 費用項目別ステータス履歴

### インデックスの効果

これらのインデックスにより、以下の操作が高速化されています：

1. **番組別集計**: `production_id` でのフィルタ・集計
2. **取引先別集計**: `partner_id` でのフィルタ・集計
3. **期限切れ契約の検出**: `contract_end_date` での範囲検索
4. **支払状況フィルタ**: `(status, payment_status)` の複合インデックス
5. **出演者情報の取得**: `production_cast`, `contract_cast` の結合
6. **履歴の追跡**: `expense_id` での履歴検索

---

## まとめ

このドキュメントは、BillingManager2.0アプリケーションのデータベース構造を包括的に説明しています。

### 主要なポイント

1. **5つのデータベース**: 役割分担により、発注管理・支払実績・マスタデータを効率的に管理
2. **10個のメインテーブル**: `order_management.db` がアプリのコアで、番組・契約・費用・取引先・出演者を統合管理
3. **自動連携**: 起動時の自動照合、契約からの費用項目自動生成、契約自動延長など
4. **明確なリレーション**: 外部キー制約とインデックスにより、データ整合性とパフォーマンスを確保
5. **8つのタブ**: 各タブが特定のテーブルと連携し、業務フローに沿った機能を提供

### 開発時の参照ガイド

- **新機能追加時**: 該当するタブとテーブルのマッピングを確認
- **データベース変更時**: リレーションシップと外部キー制約を考慮
- **パフォーマンス問題**: インデックスの追加・最適化を検討
- **データフロー確認**: 自動処理の流れを理解し、副作用を防止

---

**最終更新**: 2025年11月15日
**バージョン**: 1.0.0
