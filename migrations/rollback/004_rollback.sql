-- ロールバック: 履歴管理テーブル削除
-- バージョン: 004

DROP INDEX IF EXISTS idx_status_history_expense;
DROP INDEX IF EXISTS idx_order_history_expense;
DROP INDEX IF EXISTS idx_contract_renewal_contract;

DROP TABLE IF EXISTS status_history;
DROP TABLE IF EXISTS order_history;
DROP TABLE IF EXISTS contract_renewal_history;
