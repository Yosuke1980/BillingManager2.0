"""重複番組の削除スクリプト

同じ名前の番組が複数登録されている場合、以下のルールで統合します：
1. 最も新しいID（最後に作成されたもの）を残す
2. 古い番組に紐づいている出演者、制作会社、契約、費用項目を新しい番組に移行
3. 古い番組レコードを削除
"""
import sqlite3
from utils import log_message


def remove_duplicate_programs():
    """重複番組を削除"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # 重複している番組名を取得
        cursor.execute("""
            SELECT name, COUNT(*) as count
            FROM productions
            GROUP BY name
            HAVING count > 1
            ORDER BY count DESC
        """)
        duplicates = cursor.fetchall()

        if not duplicates:
            print("✓ 重複している番組はありません")
            return

        print(f"重複している番組: {len(duplicates)}件")
        total_deleted = 0

        for name, count in duplicates:
            print(f"\n処理中: {name} ({count}件)")

            # 同じ名前の番組をすべて取得（IDの降順=新しい順）
            cursor.execute("""
                SELECT id, broadcast_days, broadcast_time
                FROM productions
                WHERE name = ?
                ORDER BY id DESC
            """, (name,))
            programs = cursor.fetchall()

            # 最新のもの（最初の要素）を残す
            keep_id = programs[0][0]
            print(f"  保持: ID={keep_id}")

            # 古いものを削除
            for program in programs[1:]:
                old_id = program[0]
                print(f"  削除: ID={old_id}")

                # 関連データを新しいIDに移行
                # 1. 出演者
                cursor.execute("""
                    UPDATE production_cast
                    SET production_id = ?
                    WHERE production_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM production_cast pc2
                        WHERE pc2.production_id = ? AND pc2.cast_id = production_cast.cast_id
                    )
                """, (keep_id, old_id, keep_id))
                moved_cast = cursor.rowcount
                if moved_cast > 0:
                    print(f"    出演者を移行: {moved_cast}件")

                # 2. 制作会社
                cursor.execute("""
                    UPDATE production_producers
                    SET production_id = ?
                    WHERE production_id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM production_producers pp2
                        WHERE pp2.production_id = ? AND pp2.partner_id = production_producers.partner_id
                    )
                """, (keep_id, old_id, keep_id))
                moved_producers = cursor.rowcount
                if moved_producers > 0:
                    print(f"    制作会社を移行: {moved_producers}件")

                # 3. 契約
                cursor.execute("""
                    UPDATE order_contracts
                    SET production_id = ?
                    WHERE production_id = ?
                """, (keep_id, old_id))
                moved_contracts = cursor.rowcount
                if moved_contracts > 0:
                    print(f"    契約を移行: {moved_contracts}件")

                # 4. 費用項目
                cursor.execute("""
                    UPDATE expenses_order
                    SET production_id = ?
                    WHERE production_id = ?
                """, (keep_id, old_id))
                moved_expenses = cursor.rowcount
                if moved_expenses > 0:
                    print(f"    費用項目を移行: {moved_expenses}件")

                # 重複している関連データを削除
                cursor.execute("""
                    DELETE FROM production_cast
                    WHERE production_id = ?
                """, (old_id,))

                cursor.execute("""
                    DELETE FROM production_producers
                    WHERE production_id = ?
                """, (old_id,))

                # 古い番組レコードを削除
                cursor.execute("""
                    DELETE FROM productions
                    WHERE id = ?
                """, (old_id,))

                total_deleted += 1

        conn.commit()
        print(f"\n✓ 重複削除完了: {total_deleted}件の番組を削除しました")

        # 統計情報
        cursor.execute("SELECT COUNT(*) FROM productions")
        program_count = cursor.fetchone()[0]
        print(f"\n現在の番組数: {program_count}件")

    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    remove_duplicate_programs()
