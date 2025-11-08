-- マイグレーション: contracts テーブル作成
-- バージョン: 001
-- 作成日: 2025-11-09
-- 説明: 契約管理の中核テーブル（発注書・契約書の統合管理）

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 基本情報
    production_id INTEGER,
    project_id INTEGER,
    partner_id INTEGER NOT NULL,
    work_type TEXT DEFAULT '制作',

    -- 契約内容
    item_name TEXT NOT NULL,
    contract_type TEXT DEFAULT 'regular_fixed',

    -- 契約期間
    contract_start_date DATE NOT NULL,
    contract_end_date DATE NOT NULL,
    contract_period_type TEXT DEFAULT '半年',

    -- 金額・支払条件
    payment_type TEXT DEFAULT '月額固定',
    unit_price REAL,
    spot_amount REAL,
    payment_timing TEXT DEFAULT '翌月末払い',

    -- 書類管理
    document_type TEXT DEFAULT '発注書',
    document_status TEXT DEFAULT '未',
    pdf_file_path TEXT,

    -- メール送信
    email_to TEXT,
    email_subject TEXT,
    email_body TEXT,
    email_sent_date DATE,

    -- 自動延長設定
    auto_renewal_enabled INTEGER DEFAULT 1,
    renewal_period_months INTEGER DEFAULT 3,
    termination_notice_date DATE,
    last_renewal_date DATE,
    renewal_count INTEGER DEFAULT 0,

    -- その他
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
    FOREIGN KEY (partner_id) REFERENCES partners(id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_contracts_production ON contracts(production_id);
CREATE INDEX IF NOT EXISTS idx_contracts_partner ON contracts(partner_id);
CREATE INDEX IF NOT EXISTS idx_contracts_dates ON contracts(contract_start_date, contract_end_date);
CREATE INDEX IF NOT EXISTS idx_contracts_work_type ON contracts(work_type);
