"""FM横浜番組データベース再構築スクリプト

既存のFM横浜番組データを全て削除し、
最新の番組表データから再構築します。
"""
import sqlite3
from datetime import datetime


def delete_existing_programs(cursor):
    """既存のFM横浜関連データを削除"""
    print("既存のFM横浜番組データを削除中...")

    # FM横浜の番組IDを取得
    cursor.execute("""
        SELECT id FROM productions
        WHERE description LIKE '%FM横浜%' OR description LIKE '%FM Yokohama%'
    """)
    program_ids = [row[0] for row in cursor.fetchall()]

    if not program_ids:
        print("  削除対象の番組が見つかりませんでした")
        return 0

    # 関連データを削除
    for program_id in program_ids:
        # 出演者の関連を削除
        cursor.execute("DELETE FROM production_cast WHERE production_id = ?", (program_id,))
        # プロデューサーの関連を削除
        cursor.execute("DELETE FROM production_producers WHERE production_id = ?", (program_id,))

    # 番組本体を削除
    cursor.execute("""
        DELETE FROM productions
        WHERE description LIKE '%FM横浜%' OR description LIKE '%FM Yokohama%'
    """)

    deleted_count = len(program_ids)
    print(f"  削除完了: {deleted_count}番組")
    return deleted_count


def get_or_create_partner(cursor, name, partner_type="出演者"):
    """パートナーを取得または作成"""
    cursor.execute("""
        SELECT id FROM partners
        WHERE name = ? AND partner_type = ?
    """, (name, partner_type))

    result = cursor.fetchone()
    if result:
        return result[0]

    # partnersテーブルにnotesカラムがあるか確認
    cursor.execute("PRAGMA table_info(partners)")
    columns = [col[1] for col in cursor.fetchall()]

    if "notes" in columns:
        cursor.execute("""
            INSERT INTO partners (name, partner_type, notes, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (name, partner_type, "FM横浜番組表から自動追加"))
    else:
        cursor.execute("""
            INSERT INTO partners (name, partner_type, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (name, partner_type))

    return cursor.lastrowid


def rebuild_programs():
    """番組データベースを再構築"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # 既存データを削除
        deleted_count = delete_existing_programs(cursor)
        conn.commit()

        print("\n新しい番組データをインポート中...")
        added_count = 0
        cast_added = 0

        # 番組データ（簡素化版 - 主要番組のみ）
        # 実際のインポートは次のステップで詳細データを使用

        programs = [
            # 月曜日
            {"name": "Sound Ocean", "time_slot": "05:00-05:15", "days": "月,土,日", "cast": []},
            {"name": "メラタデマンデー", "time_slot": "05:15-05:45", "days": "月", "cast": ["ケント・フリック"]},
            {"name": "ちょうどいいラジオ", "time_slot": "06:00-09:00", "days": "月,火,水,木", "cast": ["宮澤　光邦"]},
            {"name": "Lovely Day♡", "time_slot": "09:00-12:00", "days": "月,火,水,木", "cast": ["近藤さや香", "藤田優一"]},
            {"name": "Lovely Day♡～hana金～", "time_slot": "09:00-12:00", "days": "金", "cast": ["はな", "藤田優一"]},
            {"name": "Kiss & Ride", "time_slot": "12:00-15:00", "days": "月,火,水", "cast": ["小林大河", "長友愛莉", "令和応援団 龍口健太郎"]},
            {"name": "Kiss & Ride", "time_slot": "12:00-14:50", "days": "木", "cast": ["小林大河", "有華", "長友愛莉"]},
            {"name": "Tresen", "time_slot": "15:00-19:00", "days": "月", "cast": ["植松哲平", "あんにゅ（コアラモード.）"]},
            {"name": "Tresen", "time_slot": "15:00-19:00", "days": "火", "cast": ["植松哲平", "泉ノ波あみ"]},
            {"name": "Tresen", "time_slot": "15:00-19:00", "days": "水", "cast": ["植松哲平", "平沢あくび"]},
            {"name": "Tresen", "time_slot": "15:00-19:00", "days": "木", "cast": ["植松哲平", "halca"]},
            {"name": "Tresen Friday", "time_slot": "15:00-19:00", "days": "金", "cast": ["じゅんご", "舘谷春香"]},
            {"name": "PRIME TIME", "time_slot": "19:00-21:50", "days": "月", "cast": ["栗原治久", "manatie"]},
            {"name": "PRIME TIME", "time_slot": "19:00-21:50", "days": "火", "cast": ["栗原治久", "REMO-CON"]},
            {"name": "PRIME TIME", "time_slot": "19:00-21:50", "days": "水", "cast": ["栗原治久", "川内美月"]},
            {"name": "PRIME TIME", "time_slot": "19:00-21:50", "days": "木", "cast": ["栗原治久", "DJ帝"]},
            {"name": "Keep Green & Blue", "time_slot": "21:50-22:00", "days": "月,火,水,木", "cast": ["MITSUMI"]},
            {"name": "otonanoラジオ", "time_slot": "24:00-24:30", "days": "月", "cast": ["萩原健太"]},
            {"name": "BEAT JAM", "time_slot": "24:30-25:30", "days": "月", "cast": ["鈴木しょう治"]},

            # 火曜日
            {"name": "Mach Discovery", "time_slot": "05:15-05:45", "days": "火", "cast": ["赤塚剛文", "あこ"]},
            {"name": "深夜の音楽食堂", "time_slot": "24:30-25:00", "days": "火", "cast": ["松重豊"]},

            # 水曜日
            {"name": "YOKOHAMA LAGOON", "time_slot": "05:30-06:00", "days": "水", "cast": ["長松清潤"]},

            # 木曜日
            {"name": "グローバル・シチズン", "time_slot": "05:30-06:00", "days": "木", "cast": ["なかよし先生（中谷よしふみ）", "椎名陽介", "安 慶陽", "橘奈穂", "川島優貴"]},
            {"name": "LIGHT UP KANAGAWA", "time_slot": "14:50-14:58", "days": "木", "cast": ["柳井麻希", "黒岩祐治（神奈川県知事）"]},
            {"name": "Music Rumble", "time_slot": "24:00-25:00", "days": "木", "cast": ["湯川れい子"]},

            # 金曜日
            {"name": "Brand New! Friday", "time_slot": "06:00-09:00", "days": "金", "cast": ["ZiNEZ-ジンジ-"]},
            {"name": "FLAG", "time_slot": "12:00-14:45", "days": "金", "cast": ["石川舜一郎", "トビー"]},
            {"name": "U-MORE！", "time_slot": "19:00-22:00", "days": "金", "cast": ["鈴木裕介"]},
            {"name": "ZERO-8", "time_slot": "22:00-23:30", "days": "金", "cast": ["REIJI", "八村倫太郎(WATWING)"]},
            {"name": "Life Goes On ～スワサントン BLUES～", "time_slot": "24:30-25:00", "days": "金", "cast": ["夏木マリ"]},
            {"name": "懐メロ時間旅行", "time_slot": "25:00-25:30", "days": "金", "cast": ["AIBY"]},

            # 土曜日
            {"name": "The Burn", "time_slot": "05:00-08:00", "days": "土", "cast": ["井手大介"]},
            {"name": "FUTURESCAPE", "time_slot": "09:00-11:00", "days": "土", "cast": ["小山薫堂", "柳井麻希"]},
            {"name": "Travelin' Light", "time_slot": "11:00-12:50", "days": "土", "cast": ["畠山美由紀"]},
            {"name": "God Bless Saturday", "time_slot": "13:00-15:55", "days": "土", "cast": ["じゅんご", "田﨑さくら"]},
            {"name": "Route 847", "time_slot": "16:00-18:30", "days": "土", "cast": ["柴田聡"]},
            {"name": "HONMOKU RED HOT STREET", "time_slot": "23:00-24:00", "days": "土", "cast": ["横山 剣（クレイジーケンバンド）"]},

            # 日曜日
            {"name": "SHONAN by the Sea", "time_slot": "06:00-09:13", "days": "日", "cast": ["秀島史香"]},
            {"name": "YOKOHAMA My Choice!", "time_slot": "09:30-10:00", "days": "日", "cast": ["今井友理恵"]},
            {"name": "まんてんサンデーズ", "time_slot": "10:00-11:33", "days": "日", "cast": ["NOLOV"]},
            {"name": "Sunday Ride with Ken", "time_slot": "12:00-12:30", "days": "日", "cast": ["三宅健"]},
            {"name": "Take your time.", "time_slot": "13:00-15:20", "days": "日", "cast": ["武居詩織"]},
            {"name": "Sunset Breeze", "time_slot": "16:00-17:48", "days": "日", "cast": ["北島美穂"]},
            {"name": "RADIO MASHUP", "time_slot": "18:30-19:00", "days": "日", "cast": ["橘ケンチ", "EXILE TETSUYA"]},
            {"name": "YAMABICO", "time_slot": "20:00-21:00", "days": "日", "cast": ["MITSUMI"]},
            {"name": "SORASHIGE BOOK", "time_slot": "23:00-23:30", "days": "日", "cast": ["加藤シゲアキ（NEWS）"]},
        ]

        for program_data in programs:
            # 番組を追加
            cursor.execute("""
                INSERT INTO productions (
                    name, production_type, start_time, end_time, broadcast_days,
                    description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                program_data["name"],
                "レギュラー",
                program_data["time_slot"].split("-")[0] if "-" in program_data["time_slot"] else None,
                program_data["time_slot"].split("-")[1] if "-" in program_data["time_slot"] else None,
                program_data["days"],
                "FM横浜番組表（2025年版）からインポート"
            ))

            production_id = cursor.lastrowid
            added_count += 1

            # 出演者を追加
            for cast_name in program_data["cast"]:
                cast_id = get_or_create_partner(cursor, cast_name, "出演者")
                cursor.execute("""
                    INSERT INTO production_cast (production_id, cast_id, role)
                    VALUES (?, ?, ?)
                """, (production_id, cast_id, "パーソナリティ"))
                cast_added += 1

        conn.commit()

        print(f"\n✓ 番組データベースの再構築が完了しました")
        print(f"  削除した番組: {deleted_count}件")
        print(f"  追加した番組: {added_count}件")
        print(f"  登録した出演者関連: {cast_added}件")

        # 現在の番組数を確認
        cursor.execute("SELECT COUNT(*) FROM productions")
        total_count = cursor.fetchone()[0]
        print(f"\n現在の番組総数: {total_count}件")

    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    rebuild_programs()
