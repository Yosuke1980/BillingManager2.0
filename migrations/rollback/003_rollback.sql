-- ロールバック: 出演者関連テーブル削除
-- バージョン: 003

DROP INDEX IF EXISTS idx_production_cast_cast;
DROP INDEX IF EXISTS idx_production_cast_production;
DROP INDEX IF EXISTS idx_contract_cast_cast;
DROP INDEX IF EXISTS idx_contract_cast_contract;
DROP INDEX IF EXISTS idx_cast_partner;

DROP TABLE IF EXISTS production_cast;
DROP TABLE IF EXISTS contract_cast;
DROP TABLE IF EXISTS cast;
