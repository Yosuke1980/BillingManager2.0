-- マイグレーション: 既存expense_itemsテーブルに不足カラムを追加
-- バージョン: 005
-- 作成日: 2025-11-09
-- 説明: actual_payment_date等の不足しているカラムをexpense_itemsテーブルに追加

-- actual_payment_dateカラムを追加（存在しない場合のみ）
-- SQLiteはIF NOT EXISTSをサポートしていないため、エラーを無視する必要がある
-- migration_manager.pyのexecutescript()では個別にエラーハンドリングされる

-- 実際の支払日
ALTER TABLE expense_items ADD COLUMN actual_payment_date DATE;

-- 請求書番号
ALTER TABLE expense_items ADD COLUMN invoice_number TEXT;

-- 源泉徴収額
ALTER TABLE expense_items ADD COLUMN withholding_tax REAL;

-- 消費税額
ALTER TABLE expense_items ADD COLUMN consumption_tax REAL;

-- 支払金額
ALTER TABLE expense_items ADD COLUMN payment_amount REAL;

-- 請求書ファイルパス
ALTER TABLE expense_items ADD COLUMN invoice_file_path TEXT;

-- 支払方法
ALTER TABLE expense_items ADD COLUMN payment_method TEXT;

-- 承認者
ALTER TABLE expense_items ADD COLUMN approver TEXT;

-- 承認日
ALTER TABLE expense_items ADD COLUMN approval_date DATE;

-- partner_id（取引先ID）
ALTER TABLE expense_items ADD COLUMN partner_id INTEGER REFERENCES partners(id);

-- contract_id（契約ID）
ALTER TABLE expense_items ADD COLUMN contract_id INTEGER REFERENCES contracts(id) ON DELETE SET NULL;

-- work_type（業務種別）がまだなければ追加
ALTER TABLE expense_items ADD COLUMN work_type TEXT DEFAULT '制作';

-- expected_payment_date（支払予定日）
ALTER TABLE expense_items ADD COLUMN expected_payment_date DATE;

-- payment_status（支払状態）
ALTER TABLE expense_items ADD COLUMN payment_status TEXT DEFAULT '未払い';

-- payment_verified_date（支払確認日）
ALTER TABLE expense_items ADD COLUMN payment_verified_date DATE;

-- payment_matched_id（支払照合ID）
ALTER TABLE expense_items ADD COLUMN payment_matched_id INTEGER;

-- payment_difference（支払差額）
ALTER TABLE expense_items ADD COLUMN payment_difference REAL DEFAULT 0;

-- expected_payment_amount（予定支払額）
ALTER TABLE expense_items ADD COLUMN expected_payment_amount REAL;
