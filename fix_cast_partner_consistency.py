"""出演者の所属事務所と契約取引先の不一致を修正するツール

不一致が見つかった契約について、以下の修正方法を選択できます：
1. 契約の取引先を出演者の所属事務所に変更
2. 出演者の所属事務所を契約取引先に変更
3. 手動で選択

使い方:
    python3 fix_cast_partner_consistency.py
"""
import sqlite3
from datetime import datetime


def get_inconsistencies():
    """不一致のある契約を取得"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                c.id as contract_id,
                c.production_id,
                c.partner_id as contract_partner_id,
                p.name as production_name,
                partner.name as contract_partner_name,
                c.item_name,
                c.contract_start_date,
                c.contract_end_date
            FROM contracts c
            LEFT JOIN productions p ON c.production_id = p.id
            LEFT JOIN partners partner ON c.partner_id = partner.id
            WHERE c.work_type = '出演'
            ORDER BY c.production_id, c.id
        """)

        contracts = cursor.fetchall()
        inconsistencies = []

        for contract in contracts:
            (contract_id, production_id, contract_partner_id, production_name,
             contract_partner_name, item_name, start_date, end_date) = contract

            # この契約に紐付いている出演者を取得
            cursor.execute("""
                SELECT
                    cc.cast_id,
                    c.name as cast_name,
                    c.partner_id as cast_partner_id,
                    cp.name as cast_partner_name,
                    cc.role
                FROM contract_cast cc
                JOIN cast c ON cc.cast_id = c.id
                LEFT JOIN partners cp ON c.partner_id = cp.id
                WHERE cc.contract_id = ?
            """, (contract_id,))

            cast_members = cursor.fetchall()

            # 各出演者の所属と契約先を比較
            mismatched_casts = []
            for cast_member in cast_members:
                (cast_id, cast_name, cast_partner_id, cast_partner_name, role) = cast_member

                # 所属事務所と契約先が一致しない場合
                if cast_partner_id != contract_partner_id:
                    mismatched_casts.append({
                        'cast_id': cast_id,
                        'cast_name': cast_name,
                        'cast_partner_id': cast_partner_id,
                        'cast_partner_name': cast_partner_name or "(所属なし)",
                        'role': role or ""
                    })

            if mismatched_casts:
                inconsistencies.append({
                    'contract_id': contract_id,
                    'production_name': production_name or "(番組なし)",
                    'contract_partner_id': contract_partner_id,
                    'contract_partner_name': contract_partner_name or "(取引先なし)",
                    'item_name': item_name or "",
                    'period': f"{start_date} 〜 {end_date}",
                    'mismatched_casts': mismatched_casts
                })

        return inconsistencies

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()


def update_contract_partner(contract_id, new_partner_id):
    """契約の取引先を更新"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE contracts
            SET partner_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_partner_id, contract_id))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        return False
    finally:
        conn.close()


def update_cast_partner(cast_id, new_partner_id):
    """出演者の所属事務所を更新"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE cast
            SET partner_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_partner_id, cast_id))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        return False
    finally:
        conn.close()


def get_all_partners():
    """すべての取引先を取得"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, code FROM partners ORDER BY name")
        return cursor.fetchall()
    finally:
        conn.close()


def interactive_fix():
    """対話的に不一致を修正"""
    print("=" * 100)
    print("出演者の所属事務所と契約取引先の不一致修正ツール")
    print("=" * 100)
    print()

    inconsistencies = get_inconsistencies()

    if not inconsistencies:
        print("✅ 不一致は見つかりませんでした！")
        return

    print(f"⚠️  {len(inconsistencies)}件の不一致が見つかりました\n")
    print("=" * 100)

    fixed_count = 0
    skipped_count = 0

    for idx, issue in enumerate(inconsistencies, 1):
        print(f"\n【{idx}/{len(inconsistencies)}】契約ID: {issue['contract_id']}")
        print(f"番組: {issue['production_name']}")
        print(f"項目名: {issue['item_name']}")
        print(f"期間: {issue['period']}")
        print(f"契約取引先: {issue['contract_partner_name']} (ID: {issue['contract_partner_id']})")
        print()
        print("不一致の出演者:")
        for cast in issue['mismatched_casts']:
            print(f"  • {cast['cast_name']} (所属: {cast['cast_partner_name']}, ID: {cast['cast_partner_id']})")
            if cast['role']:
                print(f"    役割: {cast['role']}")

        print("\n" + "-" * 100)
        print("修正方法を選択してください:")
        print("  1: 契約の取引先を出演者の所属に合わせる（推奨）")
        print("  2: 出演者の所属を契約取引先に合わせる")
        print("  3: 手動で取引先を選択")
        print("  s: スキップ（修正しない）")
        print("  q: 終了")

        choice = input("\n選択 (1/2/3/s/q): ").strip().lower()

        if choice == 'q':
            print("\n修正を中断しました")
            break
        elif choice == 's':
            print("→ スキップしました")
            skipped_count += 1
            continue
        elif choice == '1':
            # 契約の取引先を出演者の所属に変更
            # 複数の出演者がいる場合は最初の出演者の所属を使用
            if len(issue['mismatched_casts']) > 1:
                # すべて同じ所属か確認
                partner_ids = set(c['cast_partner_id'] for c in issue['mismatched_casts'])
                if len(partner_ids) > 1:
                    print("\n⚠️ 複数の異なる所属事務所があります。手動で選択してください。")
                    continue

            new_partner_id = issue['mismatched_casts'][0]['cast_partner_id']
            new_partner_name = issue['mismatched_casts'][0]['cast_partner_name']

            print(f"\n契約の取引先を「{new_partner_name}」に変更します")
            confirm = input("よろしいですか？ (y/n): ").strip().lower()

            if confirm == 'y':
                if update_contract_partner(issue['contract_id'], new_partner_id):
                    print("✓ 修正しました")
                    fixed_count += 1
                else:
                    print("✗ 修正に失敗しました")

        elif choice == '2':
            # 出演者の所属を契約取引先に変更
            print(f"\n以下の出演者の所属を「{issue['contract_partner_name']}」に変更します:")
            for cast in issue['mismatched_casts']:
                print(f"  • {cast['cast_name']}")

            confirm = input("よろしいですか？ (y/n): ").strip().lower()

            if confirm == 'y':
                success = True
                for cast in issue['mismatched_casts']:
                    if not update_cast_partner(cast['cast_id'], issue['contract_partner_id']):
                        success = False
                        print(f"✗ {cast['cast_name']}の修正に失敗しました")

                if success:
                    print("✓ 修正しました")
                    fixed_count += 1

        elif choice == '3':
            # 手動で取引先を選択
            print("\n取引先一覧を取得中...")
            partners = get_all_partners()

            print("\n利用可能な取引先:")
            for i, (p_id, p_name, p_code) in enumerate(partners[:20], 1):  # 最初の20件
                print(f"  {i}: {p_name} ({p_code})")
            if len(partners) > 20:
                print(f"  ... 他{len(partners) - 20}件")

            partner_input = input("\n取引先番号を入力 (1-20) または 's' でスキップ: ").strip()
            if partner_input == 's':
                print("→ スキップしました")
                skipped_count += 1
                continue

            try:
                partner_idx = int(partner_input) - 1
                if 0 <= partner_idx < min(20, len(partners)):
                    selected_partner = partners[partner_idx]
                    print(f"\n「{selected_partner[1]}」を選択しました")

                    target = input("変更対象 (1: 契約, 2: 出演者): ").strip()
                    if target == '1':
                        if update_contract_partner(issue['contract_id'], selected_partner[0]):
                            print("✓ 契約の取引先を修正しました")
                            fixed_count += 1
                    elif target == '2':
                        for cast in issue['mismatched_casts']:
                            update_cast_partner(cast['cast_id'], selected_partner[0])
                        print("✓ 出演者の所属を修正しました")
                        fixed_count += 1
                else:
                    print("無効な番号です。スキップします。")
                    skipped_count += 1
            except ValueError:
                print("無効な入力です。スキップします。")
                skipped_count += 1

    print("\n" + "=" * 100)
    print("【修正完了】")
    print(f"修正: {fixed_count}件")
    print(f"スキップ: {skipped_count}件")
    print("=" * 100)


def auto_fix_simple_cases():
    """単純なケース（出演者が1人で所属が同じ）を自動修正"""
    print("=" * 100)
    print("自動修正モード（単純なケースのみ）")
    print("=" * 100)
    print()

    inconsistencies = get_inconsistencies()

    if not inconsistencies:
        print("✅ 不一致は見つかりませんでした！")
        return

    # 自動修正可能なケースをフィルタリング
    auto_fixable = []
    for issue in inconsistencies:
        # 出演者の所属がすべて同じ場合のみ自動修正可能
        partner_ids = set(c['cast_partner_id'] for c in issue['mismatched_casts'])
        if len(partner_ids) == 1:
            auto_fixable.append(issue)

    if not auto_fixable:
        print("自動修正可能なケースはありません。")
        print("対話的修正モードを使用してください。")
        return

    print(f"{len(auto_fixable)}件の自動修正可能なケースが見つかりました\n")

    for issue in auto_fixable:
        print(f"契約ID: {issue['contract_id']} - {issue['production_name']}")
        print(f"  契約取引先: {issue['contract_partner_name']}")
        new_partner = issue['mismatched_casts'][0]
        print(f"  → 変更先: {new_partner['cast_partner_name']}")

    confirm = input(f"\n{len(auto_fixable)}件の契約取引先を自動修正しますか？ (y/n): ").strip().lower()

    if confirm != 'y':
        print("キャンセルしました")
        return

    fixed_count = 0
    for issue in auto_fixable:
        new_partner_id = issue['mismatched_casts'][0]['cast_partner_id']
        if update_contract_partner(issue['contract_id'], new_partner_id):
            fixed_count += 1
            print(f"✓ 契約ID {issue['contract_id']} を修正しました")

    print(f"\n{fixed_count}件を修正しました")


if __name__ == "__main__":
    import sys

    if '--auto' in sys.argv:
        auto_fix_simple_cases()
    else:
        interactive_fix()

    print("\n修正ツール終了")
