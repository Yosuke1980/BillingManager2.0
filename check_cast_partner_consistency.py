"""出演者の所属事務所と契約取引先の整合性チェックツール

出演契約において、出演者の所属事務所と契約取引先が一致しているかをチェックします。

使い方:
    python3 check_cast_partner_consistency.py

出力:
    - 不一致が見つかった契約の一覧
    - 契約ID、番組名、契約取引先、出演者名、出演者の所属事務所
"""
import sqlite3
from datetime import datetime


def check_consistency():
    """データベース内の整合性をチェック"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # 出演契約で出演者が紐付いているものを取得
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

        if not contracts:
            print("✓ 出演契約が見つかりませんでした")
            return

        print(f"出演契約: {len(contracts)}件を検証中...")
        print("=" * 100)

        inconsistencies = []
        total_cast_checked = 0

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
            total_cast_checked += len(cast_members)

            # 各出演者の所属と契約先を比較
            for cast_member in cast_members:
                (cast_id, cast_name, cast_partner_id, cast_partner_name, role) = cast_member

                # 所属事務所と契約先が一致しない場合
                if cast_partner_id != contract_partner_id:
                    inconsistencies.append({
                        'contract_id': contract_id,
                        'production_name': production_name or "(番組なし)",
                        'contract_partner_id': contract_partner_id,
                        'contract_partner_name': contract_partner_name or "(取引先なし)",
                        'cast_name': cast_name,
                        'cast_partner_id': cast_partner_id,
                        'cast_partner_name': cast_partner_name or "(所属なし)",
                        'role': role or "",
                        'item_name': item_name or "",
                        'period': f"{start_date} 〜 {end_date}"
                    })

        print(f"検証完了: {total_cast_checked}人の出演者を確認\n")

        # 結果表示
        if not inconsistencies:
            print("✅ すべての契約で所属事務所と契約取引先が一致しています！")
        else:
            print(f"⚠️  不一致が見つかりました: {len(inconsistencies)}件\n")
            print("=" * 100)

            current_contract = None
            for issue in inconsistencies:
                # 契約ごとにグループ化して表示
                if current_contract != issue['contract_id']:
                    if current_contract is not None:
                        print("-" * 100)
                    print(f"\n【契約ID: {issue['contract_id']}】")
                    print(f"番組: {issue['production_name']}")
                    print(f"項目名: {issue['item_name']}")
                    print(f"期間: {issue['period']}")
                    print(f"契約取引先: {issue['contract_partner_name']} (ID: {issue['contract_partner_id']})")
                    print(f"\n不一致の出演者:")
                    current_contract = issue['contract_id']

                print(f"  • {issue['cast_name']}")
                print(f"    所属: {issue['cast_partner_name']} (ID: {issue['cast_partner_id']})")
                if issue['role']:
                    print(f"    役割: {issue['role']}")

            print("\n" + "=" * 100)
            print(f"\n合計: {len(inconsistencies)}件の不一致")

        # 統計情報
        print("\n" + "=" * 100)
        print("【統計情報】")
        cursor.execute("SELECT COUNT(*) FROM contracts WHERE work_type = '出演'")
        cast_contract_count = cursor.fetchone()[0]
        print(f"出演契約数: {cast_contract_count}件")

        cursor.execute("SELECT COUNT(*) FROM contract_cast")
        total_links = cursor.fetchone()[0]
        print(f"契約-出演者リンク総数: {total_links}件")

        if inconsistencies:
            consistency_rate = ((total_cast_checked - len(inconsistencies)) / total_cast_checked * 100) if total_cast_checked > 0 else 100
            print(f"整合性: {consistency_rate:.1f}% ({total_cast_checked - len(inconsistencies)}/{total_cast_checked})")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def export_to_csv():
    """不一致データをCSVにエクスポート"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                c.id as contract_id,
                p.name as production_name,
                c.item_name,
                c.contract_start_date,
                c.contract_end_date,
                partner.name as contract_partner_name,
                ca.name as cast_name,
                cast_partner.name as cast_partner_name,
                cc.role
            FROM contracts c
            LEFT JOIN productions p ON c.production_id = p.id
            LEFT JOIN partners partner ON c.partner_id = partner.id
            JOIN contract_cast cc ON c.id = cc.contract_id
            JOIN cast ca ON cc.cast_id = ca.id
            LEFT JOIN partners cast_partner ON ca.partner_id = cast_partner.id
            WHERE c.work_type = '出演'
            AND ca.partner_id != c.partner_id
            ORDER BY c.id
        """)

        results = cursor.fetchall()

        if not results:
            print("不一致データはありません")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cast_partner_inconsistency_{timestamp}.csv"

        with open(filename, 'w', encoding='utf-8-sig') as f:
            # ヘッダー
            f.write("契約ID,番組名,項目名,契約開始日,契約終了日,契約取引先,出演者名,出演者所属,役割\n")

            # データ
            for row in results:
                # CSVエスケープ処理
                escaped_row = []
                for value in row:
                    if value is None:
                        escaped_row.append('')
                    else:
                        value_str = str(value)
                        # カンマや改行を含む場合はダブルクォートで囲む
                        if ',' in value_str or '\n' in value_str or '"' in value_str:
                            value_str = '"' + value_str.replace('"', '""') + '"'
                        escaped_row.append(value_str)

                f.write(','.join(escaped_row) + '\n')

        print(f"✓ 不一致データをエクスポートしました: {filename}")
        print(f"  件数: {len(results)}件")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    print("=" * 100)
    print("出演者の所属事務所と契約取引先の整合性チェック")
    print("=" * 100)
    print()

    check_consistency()

    # コマンドライン引数で --export が指定されている場合はCSVエクスポート
    if '--export' in sys.argv:
        print("\n" + "=" * 100)
        export_to_csv()

    print("\nチェック完了")
    print("\nヒント: CSVエクスポートするには --export オプションを付けて実行してください")
    print("  例: python3 check_cast_partner_consistency.py --export")
