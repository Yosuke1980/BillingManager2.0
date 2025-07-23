# Generic PyQt5 Application Framework

このプロジェクトは、より一般的で再利用可能なPyQt5アプリケーションフレームワークにリファクタリングされました。

## アーキテクチャの改善点

### 1. 設定駆動型アプリケーション
- すべてのメニュー、ツールバー、アクションが`config/app_config.json`で設定可能
- アプリケーションタイトル、ウィンドウサイズなども外部設定
- 異なるビジネス領域に容易に適応可能

### 2. プラグインベースのタブシステム
- `BaseTabPlugin`抽象クラスによる統一インターフェース
- 動的なタブの読み込み・アンロード
- 依存関係の自動解決
- プラグイン間通信システム

### 3. 一元化されたアクション管理
- `ActionManager`による全アクションの統合管理
- QActionGroupによるアクションのグループ化
- ショートカット、アイコン、多言語対応
- プラグイン機能に応じた動的なアクション有効/無効化

### 4. MVP（Model-View-Presenter）パターン
- UIロジックとビジネスロジックの分離
- テスタビリティの向上
- 再利用可能なコンポーネント設計

## フォルダ構造

```
/core/              # コアフレームワーク
  action_manager.py # アクション管理システム
  application.py    # 汎用アプリケーションクラス
  mvp.py           # MVPパターン基底クラス
  tab_manager.py   # プラグインタブ管理システム

/ui/               # UI定義
/plugins/          # タブプラグイン
  legacy_adapter.py # 既存タブのアダプター
  
/models/           # データモデル
/presenters/       # プレゼンター
/config/           # 設定ファイル
  app_config.json  # アプリケーション設定
```

## 使用方法

### 基本的な起動
```bash
python3 app_generic.py
```

### 新しいプラグインの作成

1. `BaseTabPlugin`を継承したクラスを作成
```python
from core.tab_manager import BaseTabPlugin

class MyPlugin(BaseTabPlugin):
    def get_display_name(self) -> str:
        return "My Plugin"
    
    def get_description(self) -> str:
        return "My plugin description"
    
    def initialize(self) -> bool:
        # プラグインの初期化処理
        return True
    
    def cleanup(self) -> None:
        # リソースのクリーンアップ
        pass
```

2. プラグインをアプリケーションに登録
```python
main_window.register_plugin(MyPlugin)
main_window.load_plugin('MyPlugin')
```

### 設定のカスタマイズ

`config/app_config.json`を編集してアプリケーションをカスタマイズ：

```json
{
  "application": {
    "name": "My Business App",
    "window": {
      "title": "My Business Management System"
    }
  },
  "menus": {
    "File": [
      {"type": "action", "action_id": "file_open"},
      {"type": "separator"},
      {"type": "action", "action_id": "file_exit"}
    ]
  }
}
```

## 従来版との比較

### 従来版（app.py）の問題
- ビジネスロジックとUIが密結合
- メニュー/ツールバーコードの重複
- ハードコードされた設定
- タブ間の一貫性不足

### 改善版（app_generic.py）の利点
- **再利用可能性**: 他のビジネス領域でも使用可能
- **保守性**: 設定とコードが分離
- **拡張性**: プラグインシステムによる柔軟性
- **テスト性**: MVPパターンによるテストの容易さ
- **一貫性**: 統一されたUI/UX

## マイグレーション

既存のタブクラスは`LegacyTabAdapter`によってプラグインシステムに自動適応されるため、段階的な移行が可能です。

## カスタマイズ例

### 別のビジネス領域への適用

1. 新しい設定ファイルを作成（例：`config/inventory_config.json`）
2. ビジネス固有のプラグインを実装
3. メインアプリケーションファイルで設定パスを指定

```python
main_window = create_application("config/inventory_config.json")
```

このフレームワークにより、在庫管理、顧客管理、プロジェクト管理など、様々なビジネス領域に適用できる汎用的なアプリケーションが構築可能です。