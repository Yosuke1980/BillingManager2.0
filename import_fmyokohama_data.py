"""FM横浜番組表データのインポートスクリプト

FM横浜の番組表データを解析して、番組・出演者データベースに投入します。
"""
import sqlite3
from datetime import datetime

# FM横浜の番組データ
PROGRAMS = [
    # 月曜日
    {"name": "Sound Ocean", "time": "05:00-05:15", "days": "月,土,日", "cast": []},
    {"name": "メラタデマンデー", "time": "05:15-05:45", "days": "月", "cast": ["ケント・フリック"]},
    {"name": "○○玉手箱", "time": "05:45-06:00", "days": "月", "cast": ["小倉淳", "IMALU"]},
    {"name": "ちょうどいいラジオ", "time": "06:00-09:00", "days": "月,火,水,木", "cast": ["光邦"]},
    {"name": "Lovely Day♡", "time": "09:00-12:00", "days": "月,火,水,木", "cast": ["近藤さや香", "藤田優一"]},
    {"name": "Kiss & Ride", "time": "12:00-15:00", "days": "月,水", "cast": ["小林大河", "長友愛莉", "令和応援団 龍口健太郎"]},
    {"name": "Kiss & Ride", "time": "12:00-15:00", "days": "火", "cast": ["小林大河", "関取花", "令和応援団 龍口健太郎"]},
    {"name": "Kiss & Ride", "time": "12:00-14:50", "days": "木", "cast": ["小林大河", "有華", "長友愛莉"]},
    {"name": "Tresen", "time": "15:00-19:00", "days": "月", "cast": ["植松哲平", "あんにゅ（コアラモード.）"]},
    {"name": "Tresen", "time": "15:00-19:00", "days": "火", "cast": ["植松哲平", "泉ノ波あみ"]},
    {"name": "Tresen", "time": "15:00-19:00", "days": "水", "cast": ["植松哲平", "平沢あくび"]},
    {"name": "Tresen", "time": "15:00-19:00", "days": "木", "cast": ["植松哲平", "halca"]},
    {"name": "PRIME TIME", "time": "19:00-21:50", "days": "月", "cast": ["栗原治久", "manatie"]},
    {"name": "PRIME TIME", "time": "19:00-21:50", "days": "火", "cast": ["栗原治久", "REMO-CON"]},
    {"name": "PRIME TIME", "time": "19:00-21:50", "days": "水", "cast": ["栗原治久", "川内美月"]},
    {"name": "PRIME TIME", "time": "19:00-21:50", "days": "木", "cast": ["栗原治久", "DJ帝"]},
    {"name": "Keep Green & Blue", "time": "21:50-22:00", "days": "月,火,水,木,金", "cast": ["MITSUMI"]},
    {"name": "YOKOHAMA RADIO APARTMENT 「ドア開けてます！」", "time": "22:00-23:30", "days": "月", "cast": ["橋口洋平(wacci)"]},
    {"name": "YOKOHAMA RADIO APARTMENT 「ちょいと歌います」", "time": "22:00-23:30", "days": "火", "cast": ["松本千夏"]},
    {"name": "YOKOHAMA RADIO APARTMENT 「ふらっと、道草」", "time": "22:00-23:30", "days": "水", "cast": ["NakamuraEmi"]},
    {"name": "YOKOHAMA RADIO APARTMENT 「無礼ハイツ202」", "time": "22:00-23:30", "days": "木", "cast": ["BREIMEN"]},
    {"name": "E★K radio「Tiny Little Small」", "time": "23:30-24:00", "days": "月", "cast": ["大橋ちっぽけ"]},
    {"name": "E★K radio「火曜日のシンピナイト」", "time": "23:30-24:00", "days": "火", "cast": ["SHIN WONHO"]},
    {"name": "E★K radio「超 Radio Waves!!」", "time": "23:30-24:00", "days": "水", "cast": ["ケン（THE AGUL）"]},
    {"name": "K-style", "time": "23:30-24:00", "days": "木", "cast": ["K"]},
    {"name": "otonanoラジオ", "time": "24:00-24:30", "days": "月", "cast": ["萩原健太"]},
    {"name": "言ったもん勝ち！だもん", "time": "24:00-24:30", "days": "火", "cast": ["並木良和", "松本伊代"]},
    {"name": "今夜もおきばりさん！", "time": "24:00-24:30", "days": "水", "cast": ["なかの綾"]},
    {"name": "Music Rumble", "time": "24:00-25:00", "days": "木", "cast": ["湯川れい子"]},
    {"name": "BEAT JAM", "time": "24:30-25:30", "days": "月", "cast": ["鈴木しょう治"]},
    {"name": "深夜の音楽食堂", "time": "24:30-25:00", "days": "火", "cast": ["松重豊"]},
    {"name": "恋する♡クリームパン", "time": "24:30-25:00", "days": "水", "cast": ["手がクリームパン"]},
    {"name": "木曜日の男子会", "time": "25:00-25:30", "days": "木", "cast": ["Lead"]},
    {"name": "Hits 200", "time": "27:30-29:00", "days": "月,火,水,木,金", "cast": []},

    # 金曜日
    {"name": "Brand New! Friday", "time": "06:00-09:00", "days": "金", "cast": ["ZiNEZ-ジンジ-"]},
    {"name": "Lovely Day♡～hana金～", "time": "09:00-12:00", "days": "金", "cast": ["はな", "藤田優一"]},
    {"name": "FLAG", "time": "12:00-14:45", "days": "金", "cast": ["石川舜一郎", "トビー"]},
    {"name": "Tresen Friday", "time": "15:00-19:00", "days": "金", "cast": ["じゅんご", "舘谷春香"]},
    {"name": "U-MORE！", "time": "19:00-22:00", "days": "金", "cast": ["鈴木裕介"]},
    {"name": "ZERO-8", "time": "22:00-23:30", "days": "金", "cast": ["REIJI", "八村倫太郎(WATWING)"]},
    {"name": "JACK STYLE", "time": "23:30-24:00", "days": "金", "cast": ["ジャッキー・ウー"]},
    {"name": "+Smile", "time": "24:00-24:30", "days": "金", "cast": ["elliott"]},
    {"name": "Life Goes On ～スワサントン BLUES～", "time": "24:30-25:00", "days": "金", "cast": ["夏木マリ"]},
    {"name": "懐メロ時間旅行", "time": "25:00-25:30", "days": "金", "cast": ["AIBY"]},
    {"name": "Lovefunky Raydio", "time": "25:30-26:00", "days": "金", "cast": ["Lovefunky", "DJ Dragon"]},
    {"name": "Loco Spirits!", "time": "26:00-26:30", "days": "金", "cast": ["有明（レイラ）"]},
    {"name": "濱ジャズ", "time": "26:30-27:00", "days": "金", "cast": ["ゴンザレス鈴木"]},
    {"name": "あつあつ音楽人", "time": "27:00-28:00", "days": "金", "cast": ["ハセガワ アツシ"]},

    # 土曜日
    {"name": "The Burn", "time": "05:00-08:00", "days": "土", "cast": ["井手大介"]},
    {"name": "日産神奈川 presents Pick up my town", "time": "08:00-08:30", "days": "土", "cast": ["大枝桃果"]},
    {"name": "KANAGAWA Muffin", "time": "08:30-08:55", "days": "土", "cast": ["金子 桃"]},
    {"name": "鎌倉まめヴィアージュ", "time": "08:55-09:00", "days": "土", "cast": ["影山のぞみ"]},
    {"name": "FUTURESCAPE", "time": "09:00-11:00", "days": "土", "cast": ["小山薫堂", "柳井麻希"]},
    {"name": "Travelin' Light", "time": "11:00-12:50", "days": "土", "cast": ["畠山美由紀"]},
    {"name": "God Bless Saturday", "time": "13:00-15:55", "days": "土", "cast": ["じゅんご", "田﨑さくら"]},
    {"name": "Route 847", "time": "16:00-18:30", "days": "土", "cast": ["柴田聡"]},
    {"name": "Piano Winery ～響きのクラシック～", "time": "18:45-19:00", "days": "土", "cast": ["樋口あゆ子"]},
    {"name": "ハートフルラジオ 虫の知らせ", "time": "19:00-19:30", "days": "土", "cast": ["並木良和", "榊原郁恵"]},
    {"name": "CROWN CHAT", "time": "19:30-20:00", "days": "土", "cast": ["CROWN HEAD"]},
    {"name": "THE MOTOR WEEKLY", "time": "20:00-20:30", "days": "土", "cast": ["高橋アキラ", "山下麗奈"]},
    {"name": "Startline", "time": "20:30-21:00", "days": "土", "cast": ["坂詰美紗子", "中村豪（やるせなす）"]},
    {"name": "イケてるタランチュラ", "time": "21:00-21:30", "days": "土", "cast": ["瑛人"]},
    {"name": "ありったけ交差点", "time": "21:30-22:00", "days": "土", "cast": ["Omoinotake"]},
    {"name": "LIVE DAM WAO! presents FEEL THE MUSIC", "time": "22:00-22:30", "days": "土", "cast": ["Laco（EOW）", "柄須賀皇司(the paddles)"]},
    {"name": "Flow of Hope", "time": "22:30-23:00", "days": "土", "cast": ["なおこ"]},
    {"name": "HONMOKU RED HOT STREET", "time": "23:00-24:00", "days": "土", "cast": ["横山 剣（クレイジーケンバンド）"]},
    {"name": "Adult Nostalgic Radioshow ～ANR大人の秘密基地～", "time": "24:00-24:30", "days": "土", "cast": ["IKURA"]},
    {"name": "BAY DREAM", "time": "24:30-25:00", "days": "土", "cast": ["サイプレス上野"]},
    {"name": "BANG BANG BANG！", "time": "25:00-25:30", "days": "土", "cast": ["加藤雅也"]},
    {"name": "JOY TO THE WORLD", "time": "25:30-26:00", "days": "土", "cast": ["木村至信"]},
    {"name": "Radio HITS Radio", "time": "26:00-28:30", "days": "土", "cast": ["今泉圭姫子"]},

    # 日曜日
    {"name": "ほねごり相模原 presents スマッシュラジオ", "time": "05:45-06:00", "days": "日", "cast": ["光邦", "陣内貴美子"]},
    {"name": "SHONAN by the Sea", "time": "06:00-09:13", "days": "日", "cast": ["秀島史香"]},
    {"name": "SEASIDE CLASSIC", "time": "09:13-09:27", "days": "日", "cast": ["礒 絵里子"]},
    {"name": "YOKOHAMA My Choice!", "time": "09:30-10:00", "days": "日", "cast": ["今井友理恵"]},
    {"name": "まんてんサンデーズ", "time": "10:00-11:33", "days": "日", "cast": ["NOLOV"]},
    {"name": "ウエインズトヨタ神奈川 presents サンデービーコル", "time": "11:48-12:00", "days": "日", "cast": ["杉枝真結"]},
    {"name": "ヤマハ発動機 presents Sunday Ride with Ken", "time": "12:00-12:30", "days": "日", "cast": ["三宅健"]},
    {"name": "ALFALINK presents RADIO LINK", "time": "12:30-13:00", "days": "日", "cast": ["小林千鶴"]},
    {"name": "Take your time.", "time": "13:00-15:20", "days": "日", "cast": ["武居詩織"]},
    {"name": "横浜DiscoTrain", "time": "15:20-15:30", "days": "日", "cast": ["DJ OSSHY"]},
    {"name": "日立システムズエンジニアリングサービス LANDMARK SPORTS HEROES", "time": "15:30-16:00", "days": "日", "cast": ["モリタニブンペイ", "西園寺加栞"]},
    {"name": "Sunset Breeze", "time": "16:00-17:48", "days": "日", "cast": ["北島美穂"]},
    {"name": "おうち売却マスター", "time": "17:48-17:57", "days": "日", "cast": ["じゅんご", "齋藤剛", "杉山善昭"]},
    {"name": "COLORFUL KAWASAKI", "time": "18:15-18:30", "days": "日", "cast": ["松原江里佳"]},
    {"name": "RADIO MASHUP", "time": "18:30-19:00", "days": "日", "cast": ["橘ケンチ", "EXILE TETSUYA"]},
    {"name": "アレキとか！ドロスとか！", "time": "19:00-19:30", "days": "日", "cast": ["白井眞輝[Alexandros]"]},
    {"name": "YOKOHAMA SYA⇔REE", "time": "19:30-20:00", "days": "日", "cast": ["ReeSya", "杉崎智介"]},
    {"name": "YAMABICO", "time": "20:00-21:00", "days": "日", "cast": ["MITSUMI"]},
    {"name": "サンデーradio 調子 do～yo！！", "time": "21:00-21:30", "days": "日", "cast": ["KIMI（DA PUMP）", "U-YEAH（DA PUMP）"]},
    {"name": "Baile Yokohama", "time": "21:30-22:00", "days": "日", "cast": ["目﨑雅昭", "細木美知代"]},
    {"name": "かりゆし☆らんど", "time": "22:00-22:30", "days": "日", "cast": ["柴田聡"]},
    {"name": "BREAK IT DOWN", "time": "22:30-23:00", "days": "日", "cast": ["CHiCO", "KEN THE 390", "小玉ひかり", "Dickey"]},
    {"name": "SORASHIGE BOOK", "time": "23:00-23:30", "days": "日", "cast": ["加藤シゲアキ（NEWS）"]},
    {"name": "Rebellmusik", "time": "23:30-24:00", "days": "日", "cast": ["SUGIZO"]},
    {"name": "Coastline84.7", "time": "24:00-24:30", "days": "日", "cast": ["河口恭吾"]},
    {"name": "Sunday Pocket", "time": "24:30-25:00", "days": "日", "cast": ["石渡健文"]},
]


def import_data():
    """データをインポート"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # すべての出演者を抽出
        all_casts = set()
        for program in PROGRAMS:
            for cast in program["cast"]:
                all_casts.add(cast)

        print(f"出演者数: {len(all_casts)}人")
        print(f"番組数: {len(PROGRAMS)}番組")

        # 出演者マスタに登録（重複チェック）
        partner_ids = {}
        for cast_name in sorted(all_casts):
            # 既存チェック
            cursor.execute("SELECT id FROM partners WHERE name = ?", (cast_name,))
            existing = cursor.fetchone()

            if existing:
                partner_ids[cast_name] = existing[0]
                print(f"既存出演者: {cast_name}")
            else:
                cursor.execute("""
                    INSERT INTO partners (name, partner_type, notes, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (cast_name, "出演者", "FM横浜番組表からインポート"))
                partner_ids[cast_name] = cursor.lastrowid
                print(f"新規出演者: {cast_name}")

        # 番組を登録
        for program in PROGRAMS:
            program_name = program["name"]
            broadcast_days = program["days"]
            time_range = program["time"]

            # 既存チェック
            cursor.execute("""
                SELECT id FROM productions
                WHERE name = ? AND broadcast_days = ?
            """, (program_name, broadcast_days))
            existing_program = cursor.fetchone()

            if existing_program:
                production_id = existing_program[0]
                print(f"既存番組: {program_name} ({broadcast_days})")
            else:
                # 番組を新規登録
                cursor.execute("""
                    INSERT INTO productions (
                        name, production_type, broadcast_time, broadcast_days,
                        status, start_date, description,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    program_name,
                    "レギュラー",
                    time_range,
                    broadcast_days,
                    "放送中",
                    "2025-01-01",  # デフォルト開始日
                    f"FM横浜 ({broadcast_days}) {time_range}"
                ))
                production_id = cursor.lastrowid
                print(f"新規番組: {program_name} ({broadcast_days})")

            # 出演者を番組に紐づけ
            for cast_name in program["cast"]:
                if cast_name not in partner_ids:
                    continue

                partner_id = partner_ids[cast_name]

                # 既に紐づいているかチェック
                cursor.execute("""
                    SELECT id FROM production_cast
                    WHERE production_id = ? AND cast_id = ?
                """, (production_id, partner_id))

                if not cursor.fetchone():
                    # cast_idとしてpartner_idを使用（出演者マスタを統合したため）
                    cursor.execute("""
                        INSERT INTO production_cast (production_id, cast_id, role)
                        VALUES (?, ?, ?)
                    """, (production_id, partner_id, "パーソナリティ"))
                    print(f"  出演者紐づけ: {cast_name}")

        conn.commit()
        print("\n✓ データのインポートが完了しました")

        # 統計情報
        cursor.execute("SELECT COUNT(*) FROM partners WHERE partner_type = '出演者'")
        cast_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM productions WHERE production_type = 'レギュラー'")
        program_count = cursor.fetchone()[0]

        print(f"\n統計:")
        print(f"  出演者マスタ: {cast_count}人")
        print(f"  番組マスタ: {program_count}番組")

    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    import_data()
