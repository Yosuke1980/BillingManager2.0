-- マイグレーション: 履歴管理テーブル作成
-- バージョン: 004
-- 作成日: 2025-11-09
-- 説明: 契約更新履歴、発注履歴、ステータス履歴テーブルの作成

-- 契約更新履歴
CREATE TABLE IF NOT EXISTS contract_renewal_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    renewal_date DATE NOT NULL,
    old_end_date DATE,
    new_end_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);

-- 発注履歴
CREATE TABLE IF NOT EXISTS order_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (expense_id) REFERENCES expense_items(id)
);

-- ステータス履歴
CREATE TABLE IF NOT EXISTS status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (expense_id) REFERENCES expense_items(id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_contract_renewal_contract ON contract_renewal_history(contract_id);
CREATE INDEX IF NOT EXISTS idx_order_history_expense ON order_history(expense_id);
CREATE INDEX IF NOT EXISTS idx_status_history_expense ON status_history(expense_id);
