#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
費用マスターから発注書管理への一括移行スクリプト

expense_master.db の expense_master テーブルのデータを
order_management.db の order_contracts テーブルに移行します。
"""

import sqlite3
import re
from datetime import datetime

def extract_program_name(project_name):
    """
    案件名から番組名を抽出する

    例:
    - "Baile Yokohama出演料" → "Baile Yokohama"
    - "KIRIN構成料" → "KIRIN"
    - "F.L.A.G." → "FLAG"
    """
    # 削除するサフィックスのパターン
    suffixes = [
        r'出演料',
        r'出演費',
        r'制作費',
        r'使用料',
        r'構成料',
        r'宿泊費',
        r'勤務分',
        r'配信料',
        r'情報',
        r'サービス',
        r'料',
        r'費',
        r'分',
    ]

    program_name = project_name.strip()

    # 各サフィックスを削除
    for suffix in suffixes:
        # 末尾のサフィックスを削除（最長マッチを優先）
        pattern = suffix + r'$'
        program_name = re.sub(pattern, '', program_name)

    # 「F.L.A.G.」→「FLAG」のように、ドットを削除
    program_name = program_name.replace('.', '')

    # 前後の空白を削除
    program_name = program_name.strip()

    return program_name if program_name else project_name

def extract_item_name(project_name):
    """
    案件名から費用項目名を抽出する

    例:
    - "Baile Yokohama出演料" → "出演料"
    - "Baile Yokohama制作費" → "制作費"
    - "KIRIN構成料" → "構成料"
    """
    # 抽出するサフィックスのパターン（優先順位順）
    patterns = [
        (r'出演料', '出演料'),
        (r'出演費', '出演費'),
        (r'制作費', '制作費'),
        (r'使用料', '使用料'),
        (r'構成料', '構成料'),
        (r'宿泊費', '宿泊費'),
        (r'勤務分', '勤務分'),
        (r'配信料', '配信料'),
        (r'協力費', '協力費'),
        (r'負担金', '負担金'),
        (r'回線料', '回線料'),
        (r'利用料', '利用料'),
        (r'保守サービス費用', '保守サービス費用'),
    ]

    for pattern, item in patterns:
        if re.search(pattern, project_name):
            return item

    # マッチしない場合は「その他」
    return "その他"

def determine_order_category(item_name):
    """
    費用項目名から発注書カテゴリを決定する

    例:
    - "出演料" → "レギュラー出演発注書"
    - "制作費" → "レギュラー制作発注書"
    """
    if '出演' in item_name:
        return 'レギュラー出演発注書'
    else:
        return 'レギュラー制作発注書'

def migrate_data():
    """メインの移行処理"""

    print("=" * 60)
    print("費用マスター → 発注書管理 一括移行スクリプト")
    print("=" * 60)
    print()

    # データベース接続
    expense_conn = sqlite3.connect('expense_master.db')
    order_conn = sqlite3.connect('order_management.db')

    expense_cursor = expense_conn.cursor()
    order_cursor = order_conn.cursor()

    try:
        # ステップ1: 既存データを削除
        print("[ステップ1] 既存の order_contracts データを削除中...")
        order_cursor.execute("SELECT COUNT(*) FROM order_contracts")
        existing_count = order_cursor.fetchone()[0]
        print(f"  削除対象: {existing_count}件")

        order_cursor.execute("DELETE FROM order_contracts")
        order_conn.commit()
        print(f"  ✓ {existing_count}件を削除しました")
        print()

        # ステップ2: 費用マスターデータを取得
        print("[ステップ2] 費用マスターデータを取得中...")
        expense_cursor.execute("""
            SELECT id, project_name, payee, payee_code, amount, payment_type
            FROM expense_master
            ORDER BY id
        """)
        expenses = expense_cursor.fetchall()
        print(f"  ✓ {len(expenses)}件のデータを取得しました")
        print()

        # ステップ3: 番組名を抽出して番組マスターに登録
        print("[ステップ3] 番組マスターにデータを登録中...")
        program_map = {}  # program_name -> program_id
        new_programs = 0

        for expense in expenses:
            expense_id, project_name, payee, payee_code, amount, payment_type = expense
            program_name = extract_program_name(project_name)

            if program_name and program_name not in program_map:
                # 既存の番組を確認
                order_cursor.execute("SELECT id FROM programs WHERE name = ?", (program_name,))
                existing = order_cursor.fetchone()

                if existing:
                    program_map[program_name] = existing[0]
                    print(f"  既存: {program_name} (ID: {existing[0]})")
                else:
                    # 新規番組を登録
                    order_cursor.execute("""
                        INSERT INTO programs (name, description, start_date, status)
                        VALUES (?, '', '2025/1/1', '放送中')
                    """, (program_name,))
                    program_id = order_cursor.lastrowid
                    program_map[program_name] = program_id
                    new_programs += 1
                    print(f"  新規: {program_name} (ID: {program_id})")

        order_conn.commit()
        print(f"  ✓ {new_programs}件の番組を新規登録しました")
        print()

        # ステップ4: 取引先マッピングを作成
        print("[ステップ4] 取引先マッピングを作成中...")
        order_cursor.execute("SELECT id, code FROM partners")
        partners = order_cursor.fetchall()
        partner_map = {code: partner_id for partner_id, code in partners if code}
        print(f"  ✓ {len(partner_map)}件の取引先をマッピングしました")
        print()

        # ステップ5: 発注書データを作成
        print("[ステップ5] 発注書データを作成中...")
        success_count = 0
        skip_count = 0

        for expense in expenses:
            expense_id, project_name, payee, payee_code, amount, payment_type = expense

            # 番組名と項目名を抽出
            program_name = extract_program_name(project_name)
            item_name = extract_item_name(project_name)

            # 番組IDを取得
            program_id = program_map.get(program_name)
            if not program_id:
                print(f"  ⚠ スキップ: {project_name} (番組IDが見つかりません)")
                skip_count += 1
                continue

            # 取引先IDを取得
            partner_id = partner_map.get(payee_code)
            if not partner_id:
                print(f"  ⚠ スキップ: {project_name} (取引先 {payee_code} が見つかりません)")
                skip_count += 1
                continue

            # 発注書カテゴリを決定
            order_category = determine_order_category(item_name)

            # 発注書データを挿入
            order_cursor.execute("""
                INSERT INTO order_contracts (
                    program_id,
                    partner_id,
                    contract_start_date,
                    contract_end_date,
                    contract_period_type,
                    pdf_status,
                    order_type,
                    order_status,
                    payment_type,
                    unit_price,
                    payment_timing,
                    item_name,
                    contract_type,
                    project_name_type,
                    order_category,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                program_id,
                partner_id,
                '2025-10-01',  # 契約開始日
                '2026-04-01',  # 契約終了日（半年後）
                '半年',
                '未配布',
                '発注書',
                '未完了',
                payment_type,
                amount,
                '翌月末払い',
                item_name,
                'regular_fixed',
                'program',
                order_category,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            ))

            success_count += 1
            print(f"  ✓ {project_name} → {program_name} ({item_name})")

        order_conn.commit()
        print()
        print(f"  ✓ {success_count}件の発注書を作成しました")
        if skip_count > 0:
            print(f"  ⚠ {skip_count}件をスキップしました")
        print()

        # 結果サマリー
        print("=" * 60)
        print("移行完了")
        print("=" * 60)
        print(f"削除: {existing_count}件")
        print(f"番組登録: {new_programs}件")
        print(f"発注書作成: {success_count}件")
        print(f"スキップ: {skip_count}件")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        order_conn.rollback()

    finally:
        expense_conn.close()
        order_conn.close()

if __name__ == '__main__':
    migrate_data()
