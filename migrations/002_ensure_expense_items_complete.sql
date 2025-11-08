-- マイグレーション: expense_items テーブルの完全性確保
-- バージョン: 002
-- 作成日: 2025-11-09
-- 説明: expense_itemsテーブルを作成（既に存在する場合はスキップ）し、必須カラムを確認

CREATE TABLE IF NOT EXISTS expense_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 契約との紐付け
    contract_id INTEGER,

    -- 基本情報
    production_id INTEGER NOT NULL,
    partner_id INTEGER,
    item_name TEXT NOT NULL,
    work_type TEXT DEFAULT '制作',

    -- 金額
    amount REAL NOT NULL,

    -- 実施・発注情報
    implementation_date DATE,
    order_number TEXT UNIQUE,
    order_date DATE,
    status TEXT DEFAULT '発注予定',

    -- 請求・支払情報
    invoice_received_date DATE,
    expected_payment_date DATE,
    expected_payment_amount REAL,
    payment_scheduled_date DATE,
    actual_payment_date DATE,
    payment_status TEXT DEFAULT '未払い',
    payment_verified_date DATE,
    payment_matched_id INTEGER,
    payment_difference REAL DEFAULT 0,

    -- 請求書・支払詳細
    invoice_number TEXT,
    withholding_tax REAL,
    consumption_tax REAL,
    payment_amount REAL,
    invoice_file_path TEXT,
    payment_method TEXT,
    approver TEXT,
    approval_date DATE,

    -- メール・通信
    gmail_draft_id TEXT,
    gmail_message_id TEXT,
    email_sent_at TIMESTAMP,

    -- その他
    contact_person TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
    FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES partners(id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_expense_items_contract ON expense_items(contract_id);
CREATE INDEX IF NOT EXISTS idx_expense_items_production ON expense_items(production_id);
CREATE INDEX IF NOT EXISTS idx_expense_items_partner ON expense_items(partner_id);
CREATE INDEX IF NOT EXISTS idx_expense_items_payment_date ON expense_items(expected_payment_date);
CREATE INDEX IF NOT EXISTS idx_expense_items_status ON expense_items(status, payment_status);
CREATE INDEX IF NOT EXISTS idx_expense_items_work_type ON expense_items(work_type);
