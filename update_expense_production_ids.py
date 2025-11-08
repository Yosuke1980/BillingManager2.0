#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expense_itemsのproduction_idを更新するスクリプト
番組名を使って新しいproduction_idに紐付け直します
"""

import sqlite3

def update_expense_production_ids(db_path):
    """expense_itemsのproduction_idを更新"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("expense_itemsのproduction_idを更新中...")

    # 一時的にカラムを追加（番組名を保持）
    try:
        cursor.execute("ALTER TABLE expense_items ADD COLUMN production_name TEXT")
    except:
        pass  # すでに存在する場合は無視

    # 既存のproduction_idから番組名を取得して一時保存
    # ただし、現在のexpense_itemsには番組名が直接入っているため、
    # production_nameカラムにコピー

    # 実際には、expense_itemsテーブルを確認
    cursor.execute("PRAGMA table_info(expense_items)")
    columns = [col[1] for col in cursor.fetchall()]

    print("expense_itemsテーブルのカラム:")
    for col in columns:
        print(f"  - {col}")

    # production_nameカラムがない場合は処理スキップ
    if 'production_name' not in columns:
        print("\nexpense_itemsテーブルにはproduction_nameカラムが存在しません")
        print("番組名での紐付けはスキップします")
        conn.close()
        return

    # 更新処理
    # production_nameを使ってproductionsテーブルからIDを取得
    cursor.execute("""
        SELECT id, production_name FROM expense_items
        WHERE production_name IS NOT NULL AND production_name != ''
    """)

    expense_items = cursor.fetchall()
    updated_count = 0
    not_found_count = 0
    not_found_names = set()

    for item_id, prod_name in expense_items:
        # 番組名からproduction_idを検索
        cursor.execute("""
            SELECT id FROM productions WHERE name = ?
        """, (prod_name,))

        result = cursor.fetchone()

        if result:
            new_prod_id = result[0]
            cursor.execute("""
                UPDATE expense_items
                SET production_id = ?
                WHERE id = ?
            """, (new_prod_id, item_id))
            updated_count += 1
        else:
            not_found_count += 1
            not_found_names.add(prod_name)

    conn.commit()

    print(f"\n完了:")
    print(f"  更新成功: {updated_count}件")
    print(f"  番組が見つからない: {not_found_count}件")

    if not_found_names:
        print(f"\n見つからなかった番組:")
        for name in sorted(not_found_names):
            print(f"  - {name}")

    conn.close()

if __name__ == "__main__":
    db_file = "/Volumes/MyDrive/GitHub/BillingManager2.0/database/order_management.db"

    print("=" * 60)
    print("expense_items production_id更新ツール")
    print("=" * 60)

    update_expense_production_ids(db_file)

    print("\n処理が完了しました。")
