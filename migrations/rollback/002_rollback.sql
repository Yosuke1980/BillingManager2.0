-- ロールバック: expense_items テーブル削除
-- バージョン: 002
-- 注意: このロールバックを実行すると全ての費用項目データが削除されます

DROP INDEX IF EXISTS idx_expense_items_work_type;
DROP INDEX IF EXISTS idx_expense_items_status;
DROP INDEX IF EXISTS idx_expense_items_payment_date;
DROP INDEX IF EXISTS idx_expense_items_partner;
DROP INDEX IF EXISTS idx_expense_items_production;
DROP INDEX IF EXISTS idx_expense_items_contract;

DROP TABLE IF EXISTS expense_items;
