"""取引先データベースへのインポートスクリプト

取引先コードと名前のリストをpartnersテーブルに追加します。
既存の取引先は重複登録されません。
"""
import sqlite3


# インポートする取引先リスト（元データから重複を除去）
# 元データ: 79行 → ユニークデータ: 33件
PARTNERS_DATA_RAW = [
    ("065062", "有限会社ボイスワークス"),
    ("032090", "4G"),
    ("014122", "株式会社アルスコード"),
    ("011053", "株式会社アクロスエンタテインメント"),
    ("033008", "鈴木　まひる"),
    ("013005", "有限会社ウルトラ"),
    ("014002", "株式会社エス・オー・プロモーション"),
    ("092011", "有限会社リズミック"),
    ("092011", "有限会社リズミック"),
    ("092011", "有限会社リズミック"),
    ("092011", "有限会社リズミック"),
    ("032039", "株式会社ジョイスタッフ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("055014", "野村　康子"),
    ("034024", "株式会社セント・フォース"),
    ("014012", "株式会社サウンズネクスト"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("032001", "株式会社ジェー・プラネット"),
    ("032001", "株式会社ジェー・プラネット"),
    ("032001", "株式会社ジェー・プラネット"),
    ("032001", "株式会社ジェー・プラネット"),
    ("032001", "株式会社ジェー・プラネット"),
    ("031003", "有限会社さくら"),
    ("072086", "ＷＵＪエンタテインメント合同会社"),
    ("081082", "合同会社山田本家"),
    ("061040", "株式会社浜銀総合研究所"),
    ("063174", "株式会社プラスプラス"),
    ("063174", "株式会社プラスプラス"),
    ("011044", "株式会社浅井企画"),
    ("091016", "株式会社ライムライト"),
    ("092011", "有限会社リズミック"),
    ("042001", "有限会社チャプター"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032179", "城山　光正"),
    ("032179", "城山　光正"),
    ("063174", "株式会社プラスプラス"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("096021", "株式会社ワンダーワーカーズ"),
    ("011053", "株式会社アクロスエンタテインメント"),
    ("014012", "株式会社サウンズネクスト"),
    ("072057", "宮澤　光邦"),
    ("041127", "高島　麻衣子"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("092011", "有限会社リズミック"),
    ("092011", "有限会社リズミック"),
    ("092011", "有限会社リズミック"),
    ("092011", "有限会社リズミック"),
    ("063157", "株式会社プランテック"),
    ("032039", "株式会社ジョイスタッフ"),
    ("032179", "城山　光正"),
    ("032071", "株式会社ジェイタス"),
    ("024001", "株式会社圭三プロダクション"),
    ("032047", "G-インパクト株式会社"),
    ("032047", "G-インパクト株式会社"),
    ("014012", "株式会社サウンズネクスト"),
    ("032039", "株式会社ジョイスタッフ"),
    ("052107", "西出　晴香"),
    ("015171", "小幡　康裕"),
    ("096031", "株式会社ワタナベエンターテインメント"),
    ("032039", "株式会社ジョイスタッフ"),
    ("032039", "株式会社ジョイスタッフ"),
    ("065061", "有限会社日曜日"),
    ("011044", "株式会社浅井企画"),
]

# 重複を除去してユニークなデータのみを取得
def get_unique_partners():
    """重複を除去してユニークな取引先データを返す"""
    seen = set()
    unique_data = []

    for code, name in PARTNERS_DATA_RAW:
        key = (code, name)
        if key not in seen:
            seen.add(key)
            unique_data.append((code, name))

    return unique_data

PARTNERS_DATA = get_unique_partners()


def import_partners():
    """取引先を一括インポート"""
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        added_count = 0
        skipped_count = 0
        updated_count = 0

        print(f"取引先のインポートを開始します（全{len(PARTNERS_DATA)}件のユニークな取引先）\n")

        for code, name in PARTNERS_DATA:
            # コードで既存チェック
            cursor.execute("""
                SELECT id, name FROM partners
                WHERE code = ?
            """, (code,))
            existing = cursor.fetchone()

            if existing:
                existing_id, existing_name = existing
                if existing_name == name:
                    print(f"  スキップ（既存）: [{code}] {name}")
                    skipped_count += 1
                else:
                    # 名前が異なる場合は更新
                    cursor.execute("""
                        UPDATE partners
                        SET name = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE code = ?
                    """, (name, code))
                    print(f"  更新: [{code}] {existing_name} → {name}")
                    updated_count += 1
                continue

            # 名前で既存チェック（コードなしの場合）
            cursor.execute("""
                SELECT id, code FROM partners
                WHERE name = ?
            """, (name,))
            existing = cursor.fetchone()

            if existing:
                existing_id, existing_code = existing
                if not existing_code:
                    # コードがない既存データにコードを追加
                    cursor.execute("""
                        UPDATE partners
                        SET code = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, existing_id))
                    print(f"  更新（コード追加）: [{code}] {name}")
                    updated_count += 1
                else:
                    print(f"  スキップ（既存・異なるコード）: [{existing_code}] {name}")
                    skipped_count += 1
                continue

            # 新規追加
            cursor.execute("""
                INSERT INTO partners (code, name, partner_type, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (code, name, "両方", "取引先リストからインポート"))

            print(f"  追加: [{code}] {name}")
            added_count += 1

        conn.commit()

        print(f"\n✓ 取引先のインポートが完了しました")
        print(f"  新規追加: {added_count}件")
        print(f"  更新: {updated_count}件")
        print(f"  スキップ（既存）: {skipped_count}件")

        # 現在の取引先数を確認
        cursor.execute("SELECT COUNT(*) FROM partners")
        total_count = cursor.fetchone()[0]
        print(f"\n現在の取引先総数: {total_count}件")

    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    import_partners()
