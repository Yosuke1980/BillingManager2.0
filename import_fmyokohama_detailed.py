"""FM横浜番組詳細データインポートスクリプト

コーナー、親番組、放送時間、放送曜日などの詳細情報を含めて
番組データを再構築します。
"""
import sqlite3


def delete_existing_programs(cursor):
    """既存のFM横浜関連データを削除"""
    print("既存のFM横浜番組データを削除中...")

    cursor.execute("""
        SELECT id FROM productions
        WHERE description LIKE '%FM横浜%' OR description LIKE '%FM Yokohama%'
    """)
    program_ids = [row[0] for row in cursor.fetchall()]

    if program_ids:
        for program_id in program_ids:
            cursor.execute("DELETE FROM production_cast WHERE production_id = ?", (program_id,))
            cursor.execute("DELETE FROM production_producers WHERE production_id = ?", (program_id,))

        cursor.execute("""
            DELETE FROM productions
            WHERE description LIKE '%FM横浜%' OR description LIKE '%FM Yokohama%'
        """)
        print(f"  削除完了: {len(program_ids)}番組")
    else:
        print("  削除対象の番組が見つかりませんでした")

    return len(program_ids)


def get_or_create_cast(cursor, name):
    """出演者を取得または作成（castテーブル）"""
    # まずcastテーブルで検索
    cursor.execute("""
        SELECT id FROM cast
        WHERE name = ?
    """, (name,))

    result = cursor.fetchone()
    if result:
        return result[0]

    # castテーブルにない場合は、まずpartnersテーブルに出演者として登録
    cursor.execute("""
        SELECT id FROM partners
        WHERE name = ? AND partner_type = '出演者'
    """, (name,))

    partner_result = cursor.fetchone()
    if not partner_result:
        # partnersテーブルに出演者を登録
        cursor.execute("PRAGMA table_info(partners)")
        columns = [col[1] for col in cursor.fetchall()]

        if "notes" in columns:
            cursor.execute("""
                INSERT INTO partners (name, partner_type, notes, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (name, "出演者", "FM横浜番組表から自動追加"))
        else:
            cursor.execute("""
                INSERT INTO partners (name, partner_type, created_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (name, "出演者"))

        partner_id = cursor.lastrowid
    else:
        partner_id = partner_result[0]

    # castテーブルに登録
    cursor.execute("""
        INSERT INTO cast (name, partner_id, notes, created_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (name, partner_id, "FM横浜番組表から自動追加"))

    return cursor.lastrowid


def import_detailed_programs():
    """詳細な番組データをインポート"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # 既存データを削除
        deleted_count = delete_existing_programs(cursor)
        conn.commit()

        print("\n詳細な番組データをインポート中...")

        # 番組IDを保存する辞書（コーナーの親番組参照用）
        program_ids = {}

        added_programs = 0
        added_corners = 0
        cast_relations = 0

        # 月曜日の番組
        programs_data = [
            # 月曜日 05:00-
            {
                "name": "Sound Ocean",
                "type": "レギュラー",
                "time": "05:00-05:15",
                "days": "月,土,日",
                "cast": [],
                "email": "ocean@fmyokohama.jp"
            },
            {
                "name": "メラタデマンデー",
                "type": "レギュラー",
                "time": "05:15-05:45",
                "days": "月",
                "cast": ["ケント・フリック"],
                "email": "kent@fmyokohama.jp"
            },
            # 月-木 06:00-09:00
            {
                "name": "ちょうどいいラジオ",
                "type": "レギュラー",
                "time": "06:00-09:00",
                "days": "月,火,水,木",
                "cast": ["宮澤　光邦"],
                "email": "cer@fmyokohama.jp",
                "corners": [
                    {"time": "06:07", "name": "ヘッドラインニュース", "cast": []},
                    {"time": "06:45", "name": "RADIO SHOPPING", "cast": ["熊谷章洋", "小林アナ", "湯本久美"]},
                    {"time": "07:23", "name": "DRIVER'S MORNING Q", "cast": []},
                    {"time": "07:35", "name": "YOKOHAMA BUSINESS EYE", "cast": ["北田英治", "新瀧健一"]},
                    {"time": "07:43", "name": "東芝プラントシステム 光邦 EYE'S", "cast": []},
                ]
            },
            # 月-木 09:00-12:00
            {
                "name": "Lovely Day♡",
                "type": "レギュラー",
                "time": "09:00-12:00",
                "days": "月,火,水,木",
                "cast": ["近藤さや香", "藤田優一"],
                "email": "lovely@fmyokohama.jp",
                "corners": [
                    {"time": "09:15", "name": "街角リポート", "cast": []},
                    {"time": "09:45", "name": "PLAY OUR LIST", "cast": []},
                    {"time": "10:00", "name": "街角リポート", "cast": []},
                    {"time": "10:23", "name": "RADIO SHOPPING", "cast": ["熊谷章洋", "小林アナ"]},
                    {"time": "11:05", "name": "街角リポート", "cast": []},
                ]
            },
            # 月-水 12:00-15:00
            {
                "name": "Kiss & Ride",
                "type": "レギュラー",
                "time": "12:00-15:00",
                "days": "月,火,水",
                "cast": ["小林大河", "長友愛莉", "令和応援団 龍口健太郎"],
                "email": "kr@fmyokohama.jp",
                "corners": [
                    {"time": "12:15", "name": "CHECK IN", "cast": []},
                    {"time": "12:31", "name": "RADIO SHOPPING", "cast": ["熊谷章洋", "小林アナ"]},
                    {"time": "13:31", "name": "RADIO SHOPPING", "cast": ["熊谷章洋", "小林アナ"]},
                    {"time": "14:15", "name": "CHECK IN", "cast": []},
                ]
            },
            # 月 15:00-19:00
            {
                "name": "Tresen",
                "type": "レギュラー",
                "time": "15:00-19:00",
                "days": "月",
                "cast": ["植松哲平", "あんにゅ（コアラモード.）"],
                "email": "tresen@fmyokohama.jp",
                "corners": [
                    {"time": "15:31", "name": "RADIO SHOPPING", "cast": ["熊谷章洋", "小林アナ"]},
                    {"time": "16:00", "name": "飲食店応援団！Fヨコ SAVE&EAT", "cast": ["川内美月", "manatie", "石井由紀子", "渡部菜都美"]},
                    {"time": "16:50", "name": "ラジオショッピング", "cast": []},
                    {"time": "18:00", "name": "TOYO TIRES presents 転がれ＃オプカン！", "cast": []},
                    {"time": "18:20", "name": "ROOTS & FUTURE", "cast": ["HAN-KUN（湘南乃風）"]},
                ]
            },
            # 月 19:00-21:50
            {
                "name": "PRIME TIME",
                "type": "レギュラー",
                "time": "19:00-21:50",
                "days": "月",
                "cast": ["栗原治久", "manatie"],
                "email": "prime@fmyokohama.jp",
                "corners": [
                    {"time": "19:21", "name": "RADIO SHOPPING", "cast": []},
                    {"time": "20:00", "name": "PRIME TIME MIX", "cast": []},
                    {"time": "21:46", "name": "SPORTS LINE", "cast": []},
                ]
            },
            # 月-木 21:50-22:00
            {
                "name": "Keep Green & Blue",
                "type": "レギュラー",
                "time": "21:50-22:00",
                "days": "月,火,水,木",
                "cast": ["MITSUMI"],
                "email": "keep@fmyokohama.jp"
            },
            # 月 22:00-
            {
                "name": "YOKOHAMA RADIO APARTMENT 「ドア開けてます！」",
                "type": "レギュラー",
                "time": "22:00-23:30",
                "days": "月",
                "cast": ["橋口洋平(wacci)"],
                "email": "wacci@fmyokohama.jp"
            },
            {
                "name": "E★K radio「Tiny Little Small」",
                "type": "レギュラー",
                "time": "23:30-24:00",
                "days": "月",
                "cast": ["大橋ちっぽけ"],
                "email": "chippoke@fmyokohama.jp"
            },
            {
                "name": "otonanoラジオ",
                "type": "レギュラー",
                "time": "24:00-24:30",
                "days": "月",
                "cast": ["萩原健太"],
                "email": "otonano@fmyokohama.jp"
            },
            {
                "name": "BEAT JAM",
                "type": "レギュラー",
                "time": "24:30-25:30",
                "days": "月",
                "cast": ["鈴木しょう治"],
                "email": "beatjam@fmyokohama.jp"
            },
            {
                "name": "ピロートープ",
                "type": "レギュラー",
                "time": "25:30-26:00",
                "days": "月",
                "cast": ["シャイトープ"],
                "email": "shy@fmyokohama.jp"
            },
            {
                "name": "YOKOHAMAパーラー",
                "type": "レギュラー",
                "time": "26:00-26:30",
                "days": "月",
                "cast": ["二ノ宮一馬（甘党男子）", "石塚利彦（甘党男子）"],
                "email": "amadan@fmyokohama.jp"
            },
            {
                "name": "キイテル「裸足」",
                "type": "レギュラー",
                "time": "26:30-27:00",
                "days": "月",
                "cast": ["リンダカラー∞"],
                "email": "hadashi@fmyokohama.jp"
            },
            {
                "name": "Harbor Blue Studio",
                "type": "レギュラー",
                "time": "27:00-27:30",
                "days": "月",
                "cast": ["岸洋佑"],
                "email": "hbs@fmyokohama.jp"
            },
            {
                "name": "Hits 200",
                "type": "レギュラー",
                "time": "27:30-29:00",
                "days": "月,火,水,木,金",
                "email": "h200@fmyokohama.jp"
            },

            # 火曜日
            {
                "name": "Mach Discovery",
                "type": "レギュラー",
                "time": "05:15-05:45",
                "days": "火",
                "cast": ["赤塚剛文", "あこ"],
                "email": "mach@fmyokohama.jp"
            },
            {
                "name": "Tresen",
                "type": "レギュラー",
                "time": "15:00-19:00",
                "days": "火",
                "cast": ["植松哲平", "泉ノ波あみ"],
                "email": "tresen@fmyokohama.jp"
            },
            {
                "name": "PRIME TIME",
                "type": "レギュラー",
                "time": "19:00-21:50",
                "days": "火",
                "cast": ["栗原治久", "REMO-CON"],
                "email": "prime@fmyokohama.jp"
            },
            {
                "name": "YOKOHAMA RADIO APARTMENT 「ちょいと歌います」",
                "type": "レギュラー",
                "time": "22:00-23:30",
                "days": "火",
                "cast": ["松本千夏"],
                "email": "choiuta@fmyokohama.jp"
            },
            {
                "name": "E★K radio「火曜日のシンピナイト」",
                "type": "レギュラー",
                "time": "23:30-24:00",
                "days": "火",
                "cast": ["SHIN WONHO"],
                "email": "shin@fmyokohama.jp"
            },
            {
                "name": "言ったもん勝ち！だもん",
                "type": "レギュラー",
                "time": "24:00-24:30",
                "days": "火",
                "cast": ["並木良和", "松本伊代"],
                "email": "gachi@fmyokohama.jp"
            },
            {
                "name": "深夜の音楽食堂",
                "type": "レギュラー",
                "time": "24:30-25:00",
                "days": "火",
                "cast": ["松重豊"],
                "email": "yashoku@fmyokohama.jp"
            },
            {
                "name": "ヰ世界らじおプラネット",
                "type": "レギュラー",
                "time": "25:00-25:30",
                "days": "火",
                "cast": ["ヰ世界情緒"],
                "email": "isepura@fmyokohama.jp"
            },
            {
                "name": "Voice Media Talk",
                "type": "レギュラー",
                "time": "25:30-26:00",
                "days": "火",
                "cast": ["ふくりゅう"],
                "email": "vmt@fmyokohama.jp"
            },
            {
                "name": "全身全霊ラジオ",
                "type": "レギュラー",
                "time": "26:00-26:30",
                "days": "火",
                "cast": ["PIGGS"],
                "email": "piggs@fmyokohama.jp"
            },
            {
                "name": "キイテル「ロケットマンショー」",
                "type": "レギュラー",
                "time": "26:30-27:00",
                "days": "火",
                "cast": ["ふかわりょう", "平松政俊"],
                "email": "rs@fmyokohama.jp"
            },
            {
                "name": "夜更けのスナックEden",
                "type": "レギュラー",
                "time": "27:00-27:30",
                "days": "火",
                "cast": ["湊あかね（East Of Eden）"],
                "email": "eden@fmyokohama.jp"
            },

            # 水曜日
            {
                "name": "YOKOHAMA LAGOON",
                "type": "レギュラー",
                "time": "05:30-06:00",
                "days": "水",
                "cast": ["長松清潤"],
                "email": "lagoon@fmyokohama.jp"
            },
            {
                "name": "Tresen",
                "type": "レギュラー",
                "time": "15:00-19:00",
                "days": "水",
                "cast": ["植松哲平", "平沢あくび"],
                "email": "tresen@fmyokohama.jp"
            },
            {
                "name": "PRIME TIME",
                "type": "レギュラー",
                "time": "19:00-21:50",
                "days": "水",
                "cast": ["栗原治久", "川内美月"],
                "email": "prime@fmyokohama.jp"
            },
            {
                "name": "YOKOHAMA RADIO APARTMENT 「ふらっと、道草」",
                "type": "レギュラー",
                "time": "22:00-23:30",
                "days": "水",
                "cast": ["NakamuraEmi"],
                "email": "emi@fmyokohama.jp"
            },
            {
                "name": "E★K radio「超 Radio Waves!!」",
                "type": "レギュラー",
                "time": "23:30-24:00",
                "days": "水",
                "cast": ["ケン（THE AGUL）"],
                "email": "ken@fmyokohama.jp"
            },
            {
                "name": "今夜もおきばりさん！",
                "type": "レギュラー",
                "time": "24:00-24:30",
                "days": "水",
                "cast": ["なかの綾"],
                "email": "aya@fmyokohama.jp"
            },
            {
                "name": "恋する♡クリームパン",
                "type": "レギュラー",
                "time": "24:30-25:00",
                "days": "水",
                "cast": ["手がクリームパン"],
                "email": "koipan@fmyokohama.jp"
            },
            {
                "name": "Midnight CROSSOVER 847",
                "type": "レギュラー",
                "time": "25:00-25:30",
                "days": "水",
                "cast": ["鴉紋ゆうく"],
                "email": "mcro847@fmyokohama.jp"
            },
            {
                "name": "ROMANTIC YOKOHAMI",
                "type": "レギュラー",
                "time": "25:30-26:00",
                "days": "水",
                "cast": ["石井竜也"],
                "email": "hami@fmyokohama.jp"
            },
            {
                "name": "TANSAN HOUR　今夜もシュワシュワ",
                "type": "レギュラー",
                "time": "26:00-26:30",
                "days": "水",
                "cast": ["石川峰生（炭酸王子）", "小林アナ"],
                "email": "tansan@fmyokohama.jp"
            },
            {
                "name": "キイテル「Rest in Bayside」",
                "type": "レギュラー",
                "time": "26:30-27:00",
                "days": "水",
                "cast": ["スタミナパン"],
                "email": "rib@fmyokohama.jp"
            },
            {
                "name": "TY Night Drive",
                "type": "レギュラー",
                "time": "27:00-27:30",
                "days": "水",
                "cast": ["Offo tokyo"],
                "email": "ty@fmyokohama.jp"
            },
            {
                "name": "Romance Port Night",
                "type": "レギュラー",
                "time": "27:30-28:00",
                "days": "水",
                "cast": ["大塚紗英"],
                "email": "saechi@fmyokohama.jp"
            },

            # 木曜日
            {
                "name": "グローバル・シチズン",
                "type": "レギュラー",
                "time": "05:30-06:00",
                "days": "木",
                "cast": ["なかよし先生（中谷よしふみ）", "椎名陽介", "安 慶陽", "橘奈穂", "川島優貴"],
                "email": "nakayoshi@fmyokohama.jp"
            },
            {
                "name": "Kiss & Ride",
                "type": "レギュラー",
                "time": "12:00-14:50",
                "days": "木",
                "cast": ["小林大河", "有華", "長友愛莉"],
                "email": "kr@fmyokohama.jp"
            },
            {
                "name": "LIGHT UP KANAGAWA",
                "type": "レギュラー",
                "time": "14:50-14:58",
                "days": "木",
                "cast": ["柳井麻希", "黒岩祐治（神奈川県知事）"],
                "email": "light@fmyokohama.jp"
            },
            {
                "name": "Tresen",
                "type": "レギュラー",
                "time": "15:00-19:00",
                "days": "木",
                "cast": ["植松哲平", "halca"],
                "email": "tresen@fmyokohama.jp"
            },
            {
                "name": "PRIME TIME",
                "type": "レギュラー",
                "time": "19:00-21:50",
                "days": "木",
                "cast": ["栗原治久", "DJ帝"],
                "email": "prime@fmyokohama.jp"
            },
            {
                "name": "YOKOHAMA RADIO APARTMENT 「無礼ハイツ202」",
                "type": "レギュラー",
                "time": "22:00-23:30",
                "days": "木",
                "cast": ["BREIMEN"],
                "email": "202@fmyokohama.jp"
            },
            {
                "name": "K-style",
                "type": "レギュラー",
                "time": "23:30-24:00",
                "days": "木",
                "cast": ["K"],
                "email": "kst@fmyokohama.jp"
            },
            {
                "name": "Music Rumble",
                "type": "レギュラー",
                "time": "24:00-25:00",
                "days": "木",
                "cast": ["湯川れい子"],
                "email": "rumble@fmyokohama.jp"
            },
            {
                "name": "木曜日の男子会",
                "type": "レギュラー",
                "time": "25:00-25:30",
                "days": "木",
                "cast": ["Lead"],
                "email": "lead@fmyokohama.jp"
            },
            {
                "name": "真夜中のグッドプレイリスト",
                "type": "レギュラー",
                "time": "25:30-26:00",
                "days": "木",
                "cast": ["間慎太郎"],
                "email": "hazama@fmyokohama.jp"
            },
            {
                "name": "癒しのサプリ",
                "type": "レギュラー",
                "time": "26:00-26:30",
                "days": "木",
                "cast": ["中村弥生"],
                "email": "iyashi@fmyokohama.jp"
            },
            {
                "name": "キイテル「神奈川ディス・ラブ」",
                "type": "レギュラー",
                "time": "26:30-27:00",
                "days": "木",
                "cast": ["囲碁将棋"],
                "email": "igoshogi@fmyokohama.jp"
            },
            {
                "name": "四畳半エメラルド supported by ReNY",
                "type": "レギュラー",
                "time": "27:00-27:30",
                "days": "木",
                "cast": ["イマヤス", "なるおさやか（POP ART TOWN）"],
                "email": "yoneme@fmyokohama.jp"
            },
            {
                "name": "同い年の幼なじみ4人が集まると うるさくてねむれない件",
                "type": "レギュラー",
                "time": "27:30-28:00",
                "days": "木",
                "cast": ["@onefive"],
                "email": "15urunemu@fmyokohama.jp"
            },

            # 金曜日
            {
                "name": "ジェイワンホームズ 心にまいう～ 一輪・二輪・サンバ！",
                "type": "レギュラー",
                "time": "05:45-06:00",
                "days": "金",
                "cast": ["石塚英彦", "鈴木まひる", "丹羽一貴"],
                "email": "kkr_maiu@fmyokohama.jp"
            },
            {
                "name": "Brand New! Friday",
                "type": "レギュラー",
                "time": "06:00-09:00",
                "days": "金",
                "cast": ["ZiNEZ-ジンジ-"],
                "email": "bn@fmyokohama.jp"
            },
            {
                "name": "Lovely Day♡～hana金～",
                "type": "レギュラー",
                "time": "09:00-12:00",
                "days": "金",
                "cast": ["はな", "藤田優一"],
                "email": "lovely@fmyokohama.jp"
            },
            {
                "name": "FLAG",
                "type": "レギュラー",
                "time": "12:00-14:45",
                "days": "金",
                "cast": ["石川舜一郎", "トビー"],
                "email": "flag@fmyokohama.jp"
            },
            {
                "name": "Tresen Friday",
                "type": "レギュラー",
                "time": "15:00-19:00",
                "days": "金",
                "cast": ["じゅんご", "舘谷春香"],
                "email": "tresen@fmyokohama.jp"
            },
            {
                "name": "U-MORE！",
                "type": "レギュラー",
                "time": "19:00-22:00",
                "days": "金",
                "cast": ["鈴木裕介"],
                "email": "u@fmyokohama.jp"
            },
            {
                "name": "ZERO-8",
                "type": "レギュラー",
                "time": "22:00-23:30",
                "days": "金",
                "cast": ["REIJI", "八村倫太郎(WATWING)"],
                "email": "08@fmyokohama.jp"
            },
            {
                "name": "JACK STYLE",
                "type": "レギュラー",
                "time": "23:30-24:00",
                "days": "金",
                "cast": ["ジャッキー・ウー"],
                "email": "jack@fmyokohama.jp"
            },
            {
                "name": "+Smile",
                "type": "レギュラー",
                "time": "24:00-24:30",
                "days": "金",
                "cast": ["elliott"],
                "email": "smile@fmyokohama.jp"
            },
            {
                "name": "Life Goes On ～スワサントン BLUES～",
                "type": "レギュラー",
                "time": "24:30-25:00",
                "days": "金",
                "cast": ["夏木マリ"],
                "email": "mari@fmyokohama.jp"
            },
            {
                "name": "懐メロ時間旅行",
                "type": "レギュラー",
                "time": "25:00-25:30",
                "days": "金",
                "cast": ["AIBY"],
                "email": "aiby@fmyokohama.jp"
            },
            {
                "name": "Lovefunky Raydio",
                "type": "レギュラー",
                "time": "25:30-26:00",
                "days": "金",
                "cast": ["Lovefunky", "DJ Dragon"],
                "email": "lovefunky@fmyokohama.jp"
            },
            {
                "name": "Loco Spirits!",
                "type": "レギュラー",
                "time": "26:00-26:30",
                "days": "金",
                "cast": ["有明（レイラ）"],
                "email": "loco@fmyokohama.jp"
            },
            {
                "name": "濱ジャズ",
                "type": "レギュラー",
                "time": "26:30-27:00",
                "days": "金",
                "cast": ["ゴンザレス鈴木"],
                "email": "hamajazz@fmyokohama.jp"
            },
            {
                "name": "あつあつ音楽人",
                "type": "レギュラー",
                "time": "27:00-28:00",
                "days": "金",
                "cast": ["ハセガワ アツシ"],
                "email": "atat@fmyokohama.jp"
            },
            {
                "name": "GREENROOM SELECTION",
                "type": "レギュラー",
                "time": "28:00-28:45",
                "days": "金",
                "cast": []
            },

            # 土曜日
            {
                "name": "The Burn",
                "type": "レギュラー",
                "time": "05:00-08:00",
                "days": "土",
                "cast": ["井手大介"],
                "email": "theburn@fmyokohama.jp"
            },
            {
                "name": "日産神奈川 presents Pick up my town",
                "type": "レギュラー",
                "time": "08:00-08:30",
                "days": "土",
                "cast": ["大枝桃果"],
                "email": "town@fmyokohama.jp"
            },
            {
                "name": "KANAGAWA Muffin",
                "type": "レギュラー",
                "time": "08:30-08:55",
                "days": "土",
                "cast": ["金子 桃"],
                "email": "kanagawa@fmyokohama.jp"
            },
            {
                "name": "鎌倉まめヴィアージュ",
                "type": "レギュラー",
                "time": "08:55-09:00",
                "days": "土",
                "cast": ["影山のぞみ"],
                "email": "mame@fmyokohama.jp"
            },
            {
                "name": "FUTURESCAPE",
                "type": "レギュラー",
                "time": "09:00-11:00",
                "days": "土",
                "cast": ["小山薫堂", "柳井麻希"],
                "email": "future@fmyokohama.jp"
            },
            {
                "name": "Travelin' Light",
                "type": "レギュラー",
                "time": "11:00-12:50",
                "days": "土",
                "cast": ["畠山美由紀"],
                "email": "tl@fmyokohama.jp"
            },
            {
                "name": "God Bless Saturday",
                "type": "レギュラー",
                "time": "13:00-15:55",
                "days": "土",
                "cast": ["じゅんご", "田﨑さくら"],
                "email": "gbs@fmyokohama.jp"
            },
            {
                "name": "NIPPON CHA・茶・CHA",
                "type": "レギュラー",
                "time": "15:55-16:00",
                "days": "土",
                "cast": ["茂木雅世"],
                "email": "ocha@fmyokohama.jp"
            },
            {
                "name": "Route 847",
                "type": "レギュラー",
                "time": "16:00-18:30",
                "days": "土",
                "cast": ["柴田聡"],
                "email": "r847@fmyokohama.jp"
            },
            {
                "name": "Piano Winery ～響きのクラシック～",
                "type": "レギュラー",
                "time": "18:45-19:00",
                "days": "土",
                "cast": ["樋口あゆ子"],
                "email": "piano@fmyokohama.jp"
            },
            {
                "name": "ハートフルラジオ 虫の知らせ",
                "type": "レギュラー",
                "time": "19:00-19:30",
                "days": "土",
                "cast": ["並木良和", "榊原郁恵"],
                "email": "mushi@fmyokohama.jp"
            },
            {
                "name": "CROWN CHAT",
                "type": "レギュラー",
                "time": "19:30-20:00",
                "days": "土",
                "cast": ["CROWN HEAD"],
                "email": "㏄@fmyokohama.jp"
            },
            {
                "name": "THE MOTOR WEEKLY",
                "type": "レギュラー",
                "time": "20:00-20:30",
                "days": "土",
                "cast": ["高橋アキラ", "山下麗奈"],
                "email": "tm@fmyokohama.jp"
            },
            {
                "name": "Startline",
                "type": "レギュラー",
                "time": "20:30-21:00",
                "days": "土",
                "cast": ["坂詰美紗子", "中村豪（やるせなす）"],
                "email": "start@fmyokohama.jp"
            },
            {
                "name": "イケてるタランチュラ",
                "type": "レギュラー",
                "time": "21:00-21:30",
                "days": "土",
                "cast": ["瑛人"],
                "email": "iketara@fmyokohama.jp"
            },
            {
                "name": "ありったけ交差点",
                "type": "レギュラー",
                "time": "21:30-22:00",
                "days": "土",
                "cast": ["Omoinotake"],
                "email": "omoinotake@fmyokohama.jp"
            },
            {
                "name": "LIVE DAM WAO! presents FEEL THE MUSIC",
                "type": "レギュラー",
                "time": "22:00-22:30",
                "days": "土",
                "cast": ["Laco（EOW）", "柄須賀皇司(the paddles)"],
                "email": "ftm@fmyokohama.jp"
            },
            {
                "name": "Flow of Hope",
                "type": "レギュラー",
                "time": "22:30-23:00",
                "days": "土",
                "cast": ["なおこ"],
                "email": "hope@fmyokohama.jp"
            },
            {
                "name": "HONMOKU RED HOT STREET",
                "type": "レギュラー",
                "time": "23:00-24:00",
                "days": "土",
                "cast": ["横山 剣（クレイジーケンバンド）"],
                "email": "045046@fmyokohama.jp"
            },
            {
                "name": "Adult Nostalgic Radioshow ～ANR大人の秘密基地～",
                "type": "レギュラー",
                "time": "24:00-24:30",
                "days": "土",
                "cast": ["IKURA"],
                "email": "ikura@fmyokohama.jp"
            },
            {
                "name": "BAY DREAM",
                "type": "レギュラー",
                "time": "24:30-25:00",
                "days": "土",
                "cast": ["サイプレス上野"],
                "email": "184045@fmyokohama.jp"
            },
            {
                "name": "BANG BANG BANG！",
                "type": "レギュラー",
                "time": "25:00-25:30",
                "days": "土",
                "cast": ["加藤雅也"],
                "email": "masaya@fmyokohama.jp"
            },
            {
                "name": "JOY TO THE WORLD",
                "type": "レギュラー",
                "time": "25:30-26:00",
                "days": "土",
                "cast": ["木村至信"],
                "email": "joy@fmyokohama.jp"
            },
            {
                "name": "Radio HITS Radio",
                "type": "レギュラー",
                "time": "26:00-28:30",
                "days": "土",
                "cast": ["今泉圭姫子"],
                "email": "snu@fmyokohama.jp"
            },

            # 日曜日
            {
                "name": "ほねごり相模原 presents スマッシュラジオ",
                "type": "レギュラー",
                "time": "05:45-06:00",
                "days": "日",
                "cast": ["宮澤　光邦", "陣内貴美子"],
                "email": "smash@fmyokohama.jp"
            },
            {
                "name": "SHONAN by the Sea",
                "type": "レギュラー",
                "time": "06:00-09:13",
                "days": "日",
                "cast": ["秀島史香"],
                "email": "shonan@fmyokohama.jp"
            },
            {
                "name": "SEASIDE CLASSIC",
                "type": "レギュラー",
                "time": "09:13-09:27",
                "days": "日",
                "cast": ["礒 絵里子"],
                "email": "iso@fmyokohama.jp"
            },
            {
                "name": "YOKOHAMA My Choice!",
                "type": "レギュラー",
                "time": "09:30-10:00",
                "days": "日",
                "cast": ["今井友理恵"],
                "email": "choice@fmyokohama.jp"
            },
            {
                "name": "まんてんサンデーズ",
                "type": "レギュラー",
                "time": "10:00-11:33",
                "days": "日",
                "cast": ["NOLOV"],
                "email": "manten@fmyokohama.jp"
            },
            {
                "name": "ウエインズトヨタ神奈川 presents サンデービーコル",
                "type": "レギュラー",
                "time": "11:48-12:00",
                "days": "日",
                "cast": ["杉枝真結"],
                "email": "ybc@fmyokohama.jp"
            },
            {
                "name": "ヤマハ発動機 presents Sunday Ride with Ken",
                "type": "レギュラー",
                "time": "12:00-12:30",
                "days": "日",
                "cast": ["三宅健"],
                "email": "kenmiyake@fmyokohama.jp"
            },
            {
                "name": "ALFALINK presents RADIO LINK",
                "type": "レギュラー",
                "time": "12:30-13:00",
                "days": "日",
                "cast": ["小林千鶴"],
                "email": "link@fmyokohama.jp"
            },
            {
                "name": "Take your time.",
                "type": "レギュラー",
                "time": "13:00-15:20",
                "days": "日",
                "cast": ["武居詩織"],
                "email": "take@fmyokohama.jp"
            },
            {
                "name": "横浜DiscoTrain",
                "type": "レギュラー",
                "time": "15:20-15:30",
                "days": "日",
                "cast": ["DJ OSSHY"],
                "email": "yokohamadisco@fmyokohama.jp"
            },
            {
                "name": "日立システムズエンジニアリングサービス LANDMARK SPORTS HEROES",
                "type": "レギュラー",
                "time": "15:30-16:00",
                "days": "日",
                "cast": ["モリタニブンペイ", "西園寺加栞"],
                "email": "lsh@fmyokohama.jp"
            },
            {
                "name": "Sunset Breeze",
                "type": "レギュラー",
                "time": "16:00-17:48",
                "days": "日",
                "cast": ["北島美穂"],
                "email": "sb@fmyokohama.jp"
            },
            {
                "name": "おうち売却マスター",
                "type": "レギュラー",
                "time": "17:48-17:57",
                "days": "日",
                "cast": ["じゅんご", "齋藤剛", "杉山善昭"],
                "email": "ouchi@fmyokohama.jp"
            },
            {
                "name": "COLORFUL KAWASAKI",
                "type": "レギュラー",
                "time": "18:15-18:30",
                "days": "日",
                "cast": ["松原江里佳"],
                "email": "ck@fmyokohama.jp"
            },
            {
                "name": "RADIO MASHUP",
                "type": "レギュラー",
                "time": "18:30-19:00",
                "days": "日",
                "cast": ["橘ケンチ", "EXILE TETSUYA"],
                "email": "mash@fmyokohama.jp"
            },
            {
                "name": "アレキとか！ドロスとか！",
                "type": "レギュラー",
                "time": "19:00-19:30",
                "days": "日",
                "cast": ["白井眞輝[Alexandros]"],
                "email": "aledro@fmyokohama.jp"
            },
            {
                "name": "YOKOHAMA SYA⇔REE",
                "type": "レギュラー",
                "time": "19:30-20:00",
                "days": "日",
                "cast": ["ReeSya", "杉崎智介"],
                "email": "reesya@fmyokohama.jp"
            },
            {
                "name": "YAMABICO",
                "type": "レギュラー",
                "time": "20:00-21:00",
                "days": "日",
                "cast": ["MITSUMI"],
                "email": "mtm@fmyokohama.jp"
            },
            {
                "name": "サンデーradio 調子 do～yo！！",
                "type": "レギュラー",
                "time": "21:00-21:30",
                "days": "日",
                "cast": ["KIMI（DA PUMP）", "U-YEAH（DA PUMP）"],
                "email": "DAPUMP@fmyokohama.jp"
            },
            {
                "name": "Baile Yokohama",
                "type": "レギュラー",
                "time": "21:30-22:00",
                "days": "日",
                "cast": ["目﨑雅昭", "細木美知代"],
                "email": "baile@fmyokohama.jp"
            },
            {
                "name": "かりゆし☆らんど",
                "type": "レギュラー",
                "time": "22:00-22:30",
                "days": "日",
                "cast": ["柴田聡"],
                "email": "land@fmyokohama.jp"
            },
            {
                "name": "BREAK IT DOWN",
                "type": "レギュラー",
                "time": "22:30-23:00",
                "days": "日",
                "cast": ["CHiCO", "KEN THE 390", "小玉ひかり", "Dickey"],
                "email": "bid@fmyokohama.jp"
            },
            {
                "name": "SORASHIGE BOOK",
                "type": "レギュラー",
                "time": "23:00-23:30",
                "days": "日",
                "cast": ["加藤シゲアキ（NEWS）"],
                "email": "ssb@fmyokohama.jp"
            },
            {
                "name": "Rebellmusik",
                "type": "レギュラー",
                "time": "23:30-24:00",
                "days": "日",
                "cast": ["SUGIZO"],
                "email": "sugizo@fmyokohama.jp"
            },
            {
                "name": "Coastline84.7",
                "type": "レギュラー",
                "time": "24:00-24:30",
                "days": "日",
                "cast": ["河口恭吾"],
                "email": "kyogo@fmyokohama.jp"
            },
            {
                "name": "Sunday Pocket",
                "type": "レギュラー",
                "time": "24:30-25:00",
                "days": "日",
                "cast": ["石渡健文"],
                "email": "sp@fmyokohama.jp"
            },
        ]

        # 番組を追加
        for program in programs_data:
            # 番組を追加
            time_parts = program["time"].split("-")
            cursor.execute("""
                INSERT INTO productions (
                    name, production_type, start_time, end_time, broadcast_days,
                    description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                program["name"],
                program["type"],
                time_parts[0] if len(time_parts) > 0 else None,
                time_parts[1] if len(time_parts) > 1 else None,
                program["days"],
                f"FM横浜番組表（2025年版）\nメール: {program.get('email', '')}"
            ))

            production_id = cursor.lastrowid
            program_ids[program["name"] + "_" + program["days"]] = production_id
            added_programs += 1

            # 出演者を追加
            for cast_name in program.get("cast", []):
                cast_id = get_or_create_cast(cursor, cast_name)
                cursor.execute("""
                    INSERT INTO production_cast (production_id, cast_id, role)
                    VALUES (?, ?, ?)
                """, (production_id, cast_id, "パーソナリティ"))
                cast_relations += 1

            # コーナーを追加
            for corner in program.get("corners", []):
                cursor.execute("""
                    INSERT INTO productions (
                        name, production_type, start_time, broadcast_days,
                        parent_production_id, description,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    corner["name"],
                    "コーナー",
                    corner["time"],
                    program["days"],
                    production_id,
                    f"FM横浜番組表（2025年版）\n親番組: {program['name']}"
                ))

                corner_id = cursor.lastrowid
                added_corners += 1

                # コーナーの出演者を追加
                for cast_name in corner.get("cast", []):
                    cast_id = get_or_create_cast(cursor, cast_name)
                    cursor.execute("""
                        INSERT INTO production_cast (production_id, cast_id, role)
                        VALUES (?, ?, ?)
                    """, (corner_id, cast_id, "出演"))
                    cast_relations += 1

        conn.commit()

        print(f"\n✓ 詳細な番組データのインポートが完了しました")
        print(f"  削除した番組: {deleted_count}件")
        print(f"  追加した番組: {added_programs}件")
        print(f"  追加したコーナー: {added_corners}件")
        print(f"  登録した出演者関連: {cast_relations}件")

        # 現在の番組数を確認
        cursor.execute("SELECT COUNT(*) FROM productions")
        total_count = cursor.fetchone()[0]
        print(f"\n現在の番組・コーナー総数: {total_count}件")

    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    import_detailed_programs()
