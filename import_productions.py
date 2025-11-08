#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番組・イベントデータのインポートスクリプト
CSVファイルから番組データをproductionsテーブルに上書きします
"""

import sqlite3
import csv
import sys
from datetime import datetime

def parse_date(date_str):
    """日付文字列をYYYY-MM-DD形式に変換"""
    if not date_str or date_str.strip() == '':
        return None

    try:
        # YYYY-MM-DD形式をそのまま返す
        date_str = date_str.strip()
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except:
        pass

    return None

def import_productions(csv_file_path, db_path):
    """CSVファイルから番組データをインポート"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブル存在確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productions'")
    if not cursor.fetchone():
        print("エラー: productionsテーブルが存在しません")
        conn.close()
        return False

    # 既存データを削除
    print("\n既存データを削除中...")
    cursor.execute("DELETE FROM productions")
    deleted_count = cursor.rowcount
    print(f"削除されたレコード数: {deleted_count}")

    # CSVファイルを読み込み
    print(f"\nCSVファイルを読み込み中: {csv_file_path}")

    imported_count = 0
    error_count = 0

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # CSVのIDを使用する場合
                production_id = row.get('ID', '').strip()
                if production_id and production_id.isdigit():
                    production_id = int(production_id)
                else:
                    production_id = None

                # 親制作物IDの処理
                parent_id = row.get('親制作物ID', '').strip()
                if parent_id:
                    try:
                        parent_id = int(float(parent_id))
                    except:
                        parent_id = None
                else:
                    parent_id = None

                # ステータスのマッピング
                status_str = row.get('ステータス', '').strip()
                if status_str == '放送中':
                    status = 'active'
                elif status_str == '完了':
                    status = 'completed'
                else:
                    status = 'active'

                # データを挿入（IDを指定する場合）
                if production_id:
                    cursor.execute("""
                        INSERT INTO productions (
                            id,
                            name,
                            description,
                            production_type,
                            start_date,
                            end_date,
                            start_time,
                            end_time,
                            broadcast_time,
                            broadcast_days,
                            status,
                            parent_production_id,
                            parent_production_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        production_id,
                        row.get('制作物名', '').strip() or '未設定',
                        row.get('説明', '').strip() or None,
                        row.get('制作物種別', '').strip() or 'レギュラー',
                        parse_date(row.get('開始日', '')),
                        parse_date(row.get('終了日', '')),
                        row.get('実施開始時間', '').strip() or None,
                        row.get('実施終了時間', '').strip() or None,
                        row.get('放送時間', '').strip() or None,
                        row.get('放送曜日', '').strip() or None,
                        status,
                        parent_id,
                        row.get('親制作物名', '').strip() or None
                    ))
                else:
                    # IDを指定しない場合（自動採番）
                    cursor.execute("""
                        INSERT INTO productions (
                            name,
                            description,
                            production_type,
                            start_date,
                            end_date,
                            start_time,
                            end_time,
                            broadcast_time,
                            broadcast_days,
                            status,
                            parent_production_id,
                            parent_production_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('制作物名', '').strip() or '未設定',
                        row.get('説明', '').strip() or None,
                        row.get('制作物種別', '').strip() or 'レギュラー',
                        parse_date(row.get('開始日', '')),
                        parse_date(row.get('終了日', '')),
                        row.get('実施開始時間', '').strip() or None,
                        row.get('実施終了時間', '').strip() or None,
                        row.get('放送時間', '').strip() or None,
                        row.get('放送曜日', '').strip() or None,
                        status,
                        parent_id,
                        row.get('親制作物名', '').strip() or None
                    ))

                imported_count += 1

                if imported_count % 5 == 0:
                    print(f"  インポート中... {imported_count}件")

            except Exception as e:
                error_count += 1
                print(f"エラー (行 {imported_count + error_count + 1}): {e}")
                print(f"  データ: {row}")

    # コミット
    conn.commit()

    # 結果を表示
    print(f"\n完了:")
    print(f"  インポート成功: {imported_count}件")
    print(f"  エラー: {error_count}件")

    # インポート後のデータを確認
    cursor.execute("SELECT COUNT(*) FROM productions")
    total = cursor.fetchone()[0]
    print(f"  productionsテーブルの総レコード数: {total}件")

    # 制作物種別ごとの集計
    cursor.execute("""
        SELECT production_type, COUNT(*) as count
        FROM productions
        GROUP BY production_type
        ORDER BY count DESC
    """)
    print(f"\n制作物種別ごとの集計:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}件")

    # ステータスごとの集計
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM productions
        GROUP BY status
        ORDER BY count DESC
    """)
    print(f"\nステータスごとの集計:")
    for row in cursor.fetchall():
        status_label = 'アクティブ' if row[0] == 'active' else '完了' if row[0] == 'completed' else row[0]
        print(f"  {status_label}: {row[1]}件")

    conn.close()
    return True

if __name__ == "__main__":
    # CSVファイルのパスを指定
    csv_file = "/Volumes/MyDrive/GitHub/BillingManager2.0/productions.csv"
    db_file = "/Volumes/MyDrive/GitHub/BillingManager2.0/database/order_management.db"

    print("=" * 60)
    print("番組・イベントデータインポートツール")
    print("=" * 60)

    import_productions(csv_file, db_file)

    print("\n処理が完了しました。")
