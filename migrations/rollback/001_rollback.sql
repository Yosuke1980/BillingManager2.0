-- ロールバック: contracts テーブル削除
-- バージョン: 001

DROP INDEX IF EXISTS idx_contracts_work_type;
DROP INDEX IF EXISTS idx_contracts_dates;
DROP INDEX IF EXISTS idx_contracts_partner;
DROP INDEX IF EXISTS idx_contracts_production;

DROP TABLE IF EXISTS contracts;
