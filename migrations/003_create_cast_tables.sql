-- マイグレーション: 出演者関連テーブル作成
-- バージョン: 003
-- 作成日: 2025-11-09
-- 説明: cast, contract_cast, production_castテーブルの作成

-- 出演者マスター
CREATE TABLE IF NOT EXISTS cast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    partner_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partner_id) REFERENCES partners(id)
);

-- 契約と出演者の紐付け
CREATE TABLE IF NOT EXISTS contract_cast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    cast_id INTEGER NOT NULL,
    role TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (cast_id) REFERENCES cast(id) ON DELETE CASCADE,
    UNIQUE(contract_id, cast_id)
);

-- 番組と出演者の紐付け
CREATE TABLE IF NOT EXISTS production_cast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_id INTEGER NOT NULL,
    cast_id INTEGER NOT NULL,
    role TEXT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
    FOREIGN KEY (cast_id) REFERENCES cast(id) ON DELETE CASCADE,
    UNIQUE(production_id, cast_id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_cast_partner ON cast(partner_id);
CREATE INDEX IF NOT EXISTS idx_contract_cast_contract ON contract_cast(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_cast_cast ON contract_cast(cast_id);
CREATE INDEX IF NOT EXISTS idx_production_cast_production ON production_cast(production_id);
CREATE INDEX IF NOT EXISTS idx_production_cast_cast ON production_cast(cast_id);
