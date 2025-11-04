"""プロジェクトデータベース簡素化マイグレーション

プロジェクトを単発イベント・特番専用にシンプル化
- type, start_date, end_date, date, budget カラムを削除
- implementation_date カラムを追加
- start_date → implementation_date にデータ変換
"""
import sqlite3
import sys
from datetime import datetime


def migrate():
    """マイグレーション実行"""
    print("=" * 60)
    print("プロジェクトデータベース簡素化マイグレーション")
    print("=" * 60)

    db_path = "order_management.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 既存データの確認
        print("\n📊 現在のデータ状況:")
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        print(f"   既存プロジェクト数: {project_count}件")

        cursor.execute("SELECT COUNT(*) FROM projects WHERE budget > 0")
        budget_count = cursor.fetchone()[0]
        print(f"   予算設定あり: {budget_count}件")

        cursor.execute("SELECT SUM(budget) FROM projects")
        total_budget = cursor.fetchone()[0] or 0
        print(f"   予算総額: {total_budget:,.0f}円")

        cursor.execute("SELECT COUNT(*) FROM expenses_order WHERE project_id IS NOT NULL")
        expense_count = cursor.fetchone()[0]
        print(f"   プロジェクト紐付き経費: {expense_count}件")

        # 警告表示
        if budget_count > 0 or expense_count > 0:
            print("\n⚠️  警告:")
            print(f"   - {budget_count}件の予算データが削除されます")
            print(f"   - {expense_count}件の経費の予算管理機能が失われます")

        # 確認
        print("\n続行しますか？ (yes/no): ", end="")
        response = input().strip().lower()
        if response not in ['yes', 'y']:
            print("❌ マイグレーションをキャンセルしました")
            return False

        print("\n🔄 マイグレーション開始...")

        # ステップ1: 新しいテーブルを作成
        print("\n1. 新しいテーブル構造を作成中...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                implementation_date DATE,
                parent_id INTEGER,
                project_type TEXT DEFAULT 'イベント',
                program_id INTEGER REFERENCES programs(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES projects_new(id)
            )
        """)
        print("   ✓ projects_new テーブル作成完了")

        # ステップ2: データ移行
        print("\n2. データを移行中...")
        cursor.execute("""
            INSERT INTO projects_new
                (id, name, implementation_date, parent_id, project_type,
                 program_id, created_at, updated_at)
            SELECT
                id,
                name,
                COALESCE(start_date, date) as implementation_date,
                parent_id,
                COALESCE(project_type, 'イベント') as project_type,
                program_id,
                created_at,
                updated_at
            FROM projects
        """)
        migrated_count = cursor.rowcount
        print(f"   ✓ {migrated_count}件のプロジェクトを移行しました")

        # ステップ3: 旧テーブルを削除し、新テーブルをリネーム
        print("\n3. テーブルを入れ替え中...")
        cursor.execute("DROP TABLE projects")
        cursor.execute("ALTER TABLE projects_new RENAME TO projects")
        print("   ✓ テーブル入れ替え完了")

        # ステップ4: インデックス再作成
        print("\n4. インデックスを作成中...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_projects_program_id
            ON projects(program_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_projects_implementation_date
            ON projects(implementation_date)
        """)
        print("   ✓ インデックス作成完了")

        # コミット
        conn.commit()

        # 結果確認
        print("\n📊 マイグレーション結果:")
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        print("   新しいカラム構成:")
        for col in columns:
            print(f"     - {col[1]} ({col[2]})")

        cursor.execute("SELECT COUNT(*) FROM projects")
        final_count = cursor.fetchone()[0]
        print(f"\n   最終プロジェクト数: {final_count}件")

        print("\n" + "=" * 60)
        print("✅ マイグレーション完了!")
        print("=" * 60)
        print("\n削除されたカラム:")
        print("  - type (レギュラー/単発の区別)")
        print("  - start_date (開始日)")
        print("  - end_date (終了日)")
        print("  - date (旧フィールド)")
        print("  - budget (予算)")
        print("\n追加されたカラム:")
        print("  - implementation_date (実施日)")
        print("\n次のステップ:")
        print("  1. python3 -c 'from order_management.database_manager import OrderManagementDB; db = OrderManagementDB(); print(\"OK\")' でインポート確認")
        print("  2. アプリケーションを起動して動作確認")

        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
