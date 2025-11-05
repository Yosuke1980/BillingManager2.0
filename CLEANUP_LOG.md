# システムクリーンアップ記録

## 2025-11-05 実施

### 目的
無駄な部分（未使用のテーブル・ファイル）を整理し、システムをシンプルにする。

---

## 削除した項目

### 1. ✅ projectsテーブル（order_management.db）

**理由**:
- データ件数: 0件
- 使用状況: 完全に未使用
- 実際に使用されているのは `productions` テーブル

**影響**: なし

**実行内容**:
```sql
DROP TABLE IF EXISTS projects;
```

---

### 2. ✅ order_management_tab.py

**理由**:
- ファイルは存在するが、app.pyから参照されていない
- このタブの機能は既に以下に分散されている:
  - 発注管理タブ（order_contract_widget.py）
  - マスター管理タブ（master_management_tab.py）

**削除した内容**:
- 案件一覧サブタブ → ProjectsMainWidget（ファイル自体が存在しない）
- 取引先マスターサブタブ → partner_master_widget.py（マスター管理タブで使用中）
- 出演者マスターサブタブ → cast_master_widget.py（マスター管理タブで使用中）
- 番組マスターサブタブ → program_master_widget.py（マスター管理タブで使用中）
- 発注書マスタサブタブ → order_contract_widget.py（発注管理タブとして独立）
- 設定サブタブ → settings_widget.py（マスター管理タブで使用中）

**影響**: なし（既に使用されていない）

---

### 3. ✅ supplier_master_widget.py

**理由**:
- `partner_master_widget.py` と完全に重複
- `order_management_tab.py` からのみ参照（そのタブ自体が未使用）
- 実際のデータは `partners` テーブルに統合済み

**影響**: なし

---

## 削除しなかった項目（理由）

### ⚠️ suppliersテーブル

**データ件数**: 0件

**削除しなかった理由**:
- `expenses_order` テーブルから外部キー参照されている
- `expenses_order` には80件のデータが存在し、稼働中
- アラート機能で `LEFT JOIN suppliers` が使用されている

**対応**:
- テーブル自体は残す（外部キー参照のため）
- 新規データは `partners` テーブルを使用
- `suppliers` テーブルは互換性のためだけに残存

---

## クリーンアップによる効果

### メリット

1. **コードベースの簡素化**
   - 未使用ファイル3つを削除
   - 未使用テーブル1つを削除

2. **メンテナンス性の向上**
   - 重複コードが削減
   - システム構造が明確化

3. **混乱の解消**
   - 使われていないタブ・ウィジェットを削除
   - どのファイルを使うべきか明確に

### 削除した総容量
- order_management_tab.py: 約2KB
- supplier_master_widget.py: 約7.5KB
- projectsテーブル: メタデータのみ

---

## 今後の課題

### expenses_order と order_contracts の統合

**現状**:
- `expenses_order`: 80件（旧発注管理、Gmail連携あり）
- `order_contracts`: 15件（新契約管理、自動延長あり）

**問題**:
- 2つのシステムが併存しており、ユーザーが混乱する可能性

**推奨ロードマップ**:

1. **短期（1-2週間）**:
   - UIで両者の使い分けを明確化
   - ドキュメントに明記

2. **中期（1-2ヶ月）**:
   - `order_contracts` にGmail連携・アラート機能を移植
   - テスト運用

3. **長期（3-6ヶ月）**:
   - `expenses_order` のデータを `order_contracts` に移行
   - `expenses_order` を廃止

---

## 実施者
Claude with User

## 実施日
2025-11-05

## バックアップ
- データベースバックアップ: order_management_backup_20251105_180028.db
