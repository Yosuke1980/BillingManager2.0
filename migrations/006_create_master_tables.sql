-- マイグレーション: マスターテーブルの作成
-- バージョン: 006
-- 作成日: 2025-11-09
-- 説明: productions（番組マスター）とpartners（取引先マスター）テーブルを作成

-- 番組マスターテーブル
CREATE TABLE IF NOT EXISTS productions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 取引先マスターテーブル
CREATE TABLE IF NOT EXISTS partners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_kana TEXT,
    company_type TEXT,
    postal_code TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    contact_person TEXT,
    payment_terms TEXT,
    bank_name TEXT,
    bank_branch TEXT,
    account_type TEXT,
    account_number TEXT,
    account_holder TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_productions_name ON productions(name);
CREATE INDEX IF NOT EXISTS idx_productions_status ON productions(status);
CREATE INDEX IF NOT EXISTS idx_partners_name ON partners(name);
