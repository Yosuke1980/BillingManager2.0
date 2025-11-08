-- マイグレーション: productionsテーブルの拡張
-- バージョン: 007
-- 作成日: 2025-11-09
-- 説明: 番組詳細情報（放送時間、放送曜日、制作物種別など）のカラムを追加

-- 制作物種別（レギュラー、イベント、コーナーなど）
ALTER TABLE productions ADD COLUMN production_type TEXT DEFAULT 'レギュラー';

-- 実施開始時間
ALTER TABLE productions ADD COLUMN start_time TEXT;

-- 実施終了時間
ALTER TABLE productions ADD COLUMN end_time TEXT;

-- 放送時間（表示用）
ALTER TABLE productions ADD COLUMN broadcast_time TEXT;

-- 放送曜日（カンマ区切り）
ALTER TABLE productions ADD COLUMN broadcast_days TEXT;

-- 親制作物ID（コーナーの場合など）
ALTER TABLE productions ADD COLUMN parent_production_id INTEGER REFERENCES productions(id);

-- 親制作物名（参照用）
ALTER TABLE productions ADD COLUMN parent_production_name TEXT;

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_productions_type ON productions(production_type);
CREATE INDEX IF NOT EXISTS idx_productions_status ON productions(status);
CREATE INDEX IF NOT EXISTS idx_productions_parent ON productions(parent_production_id);
