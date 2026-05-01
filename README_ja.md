[🇺🇸 English](README.md)

# 🌱 GreenCloud Advisor

GreenCloud Advisor は、近接性と環境負荷のバランスを考慮した AWS リージョン サステナビリティ レコメンダーです。
2つのモードがあります：
- **新規ワークロードのリージョン・最適化レコメンダー**：起動予定のワークロードを自然言語で記述し、レイテンシー要件に基づいて候補リージョンを選択します。選択したリージョンで全サービスが利用可能かを確認し、最もカーボン強度が低いリージョンを推奨します。また、選択したサービスに対する最適化提案も行います。最後にPDFレポートをダウンロードできます。
- **既存ワークロードのカーボンフットプリント分析・インサイト・チャット**：[サステナビリティコンソール](https://docs.aws.amazon.com/sustainability/latest/userguide/getting-started.html)から[カーボン排出レポート](https://docs.aws.amazon.com/sustainability/latest/userguide/csv-reports.html)をアップロードします。「AIインサイトを取得」ボタンでカーボン使用量の上位サービスやリージョンスコアなどのインサイトを取得できます。右側のチャットボットでレポートについて質問することもできます。
- **多言語対応**：UIは複数言語に対応しています。日本語と英語はすでに対応済み（デフォルトは英語）。JSONロケールファイルで他の言語も追加できます（詳細は下記）。

ローカルでStreamlitアプリを実行してテストできます。気に入ったら、AWSアカウントにデプロイできます。

## コントリビューター
* [Smita Srivastava](smisriv@amazon.com)
* [Tomoya Tozuka](totozuka@amazon.com)
* [Kayalvizhi Kandasamy](kayalvk@amazon.com)
* [Gaurav Gupta](gauravgp@amazon.com)
* [Shubham Tiwari](twars@amazon.com)

## 機能

- **スマートリージョン選択**：近接性、サービス可用性、カーボンフットプリントを分析
- **デュアルカーボン会計**：ロケーションベースとマーケットベースの両方式に対応
- **カーボン排出レポート連携**：サステナビリティコンソールからダウンロードしたカーボン排出CSVレポートをアップロード・分析
- **インタラクティブWeb UI**：Streamlitベースの使いやすいインターフェース
- **多言語対応（EN/JA）**：UIとPDFレポートがワンクリックで英語・日本語切り替え可能

## ソリューション概要
このソリューションは https://app.electricitymaps.com/ のAPIを使用して、世界の特定リージョンのカーボン数値を取得し、新規ワークロードのリージョンスコアを算出します。electricitymaps APIを使用するには **APIキー** が必要です。
- https://app.electricitymaps.com/settings/api-access でアカウントを作成し、APIトークンを取得してください。サンドボックスキーは無料で利用できます。
- 取得したトークンをルートフォルダの `config` ファイルの `API_TOKEN` パラメータに設定してください。例：`API_TOKEN='Xsxxxxxxxxxxxxxxx7`

このソリューションは **リージョン分析** と **サステナビリティレポート分析** の2つのモードで動作します。**リージョン分析** では https://app.electricitymaps.com/ を使用してリージョンのサステナビリティスコアを取得します。
両モードともGenAIを使用してレコメンデーションとレポートを生成します。

## ローカルでアプリを実行
ターミナルを開いて以下を実行：
- ターミナルでAWS認証情報を設定
- セットアップスクリプトを実行（依存関係と日本語フォントをインストール）：
  ```bash
  ./setup.sh
  ```
  または手動でインストール：
  ```bash
  pip install -r requirements.txt
  ```
  **注意（Linuxのみ）：** PDF/グラフの日本語レンダリングに日本語フォントが必要です。`setup.sh` で自動インストールされます。手動の場合：`sudo apt-get install fonts-noto-cjk`
- Streamlitアプリを起動：`streamlit run streamlit_app.py --server.port 8501`
  <br> 上記コマンドで http://localhost:8501 が開きます。開かない場合はブラウザで直接アクセスしてください。
- 英語・日本語の切り替えは、ページ右上の 🇺🇸 EN / 🇯🇵 JA ボタンをクリック

## AWSへのデプロイ
このアプリはAWSにもデプロイできます。メインフォルダにECS、ALB、CloudFrontへデプロイするCloudFormationテンプレートがあります。

   ### アーキテクチャ図

   ![GreenCloud Advisor アーキテクチャ図](image/Architecture_Diagram.png)

前提条件：
* Docker
* Python >= 3.8
* 開発用ブラウザ

デプロイ手順：
1. bashターミナルを開き、デプロイ先アカウントのAWS認証情報を設定
1. Dockerイメージをビルドし、ECRにアップロード。デフォルトではus-east-1リージョンにECRリポジトリを作成します。`<account-id>` は実際の値に置き換えてください。
   * ECRリポジトリ作成：`aws ecr create-repository --repository-name greencloud --region us-east-1`
   * DockerをECRに認証：`aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com`
   * Dockerイメージビルド：`docker build --platform linux/amd64 -t greencloud .`
   * タグ付け：`docker tag greencloud:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/greencloud:latest`
   * ECRにプッシュ：`docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/greencloud:latest`

   上記の `コンテナイメージ` はステップ3のCloudFormationスタックで必要です。

1. `config` ファイルを開き、`CONTAINER_IMAGE` にECRコンテナイメージパスを設定。例：`123456789.dkr.ecr.us-east-1.amazonaws.com/greencloud:latest`

1. deploy.shを実行してCloudFormationをデプロイ：`./deploy.sh`

## 使い方

### 新規ワークロード向けWebインターフェース
1. AWSサービスまたはワークロードの説明を入力
1. 評価する候補AWSリージョンを選択
1. 「リージョン分析」をクリック
1. サステナビリティと最適化レコメンデーションのサマリーを取得（ダウンロード可能）

### 既存ワークロード向けWebインターフェース
1. サステナビリティコンソールからダウンロードしたカーボン排出レポートをアップロード。詳細：[アカウントのカーボン排出レポート](https://docs.aws.amazon.com/sustainability/latest/userguide/csv-reports.html)
1. 排出レポートからAIインサイトを取得（ダウンロード可能）
1. Amazon Nova Proを使用してレポートについてチャット

## 新しい言語の追加

このアプリケーションは `locales/` ディレクトリのJSONロケールファイルで多言語UIをサポートしています。

新しい言語を追加する場合（例：韓国語 `ko`）：

1. `locales/en.json` を `locales/ko.json` にコピー
2. `ko.json` の全ての値を翻訳（キーはそのまま維持）
3. `streamlit_app.py` の `_load_locales()` に新しい言語コードを追加：
   ```python
   for lang_code in ['en', 'ja', 'ko']:
   ```
4. 言語切り替えボタンのロジックを更新して新しい言語を含める
5. `src/sustainability_insights.py` の `_load_insights_texts()` にも新しい言語コードを追加

ロケールファイル構成：
```
locales/
  en.json   # 英語（デフォルト）
  ja.json   # 日本語
  ko.json   # 韓国語（例）
```

UIテキスト、PDFラベル、グラフラベル、AIプロンプト指示は全てこれらのファイルで定義されています。翻訳にソースコードの変更は不要です — JSONの値のみ変更してください。

## 重要事項
- CloudFrontとALB間の接続はHTTPであり、SSL暗号化されていません。独自ドメイン名とSSL/TLS証明書を使用してALBにHTTPSを設定することを**強く推奨**します。
- electricitymaps.comのAPIキーは迅速なデプロイのためにconfigファイルに設定します。本番環境にデプロイする場合は、**APIキーをAWS Secrets Managerに移行**し、アプリケーションからSecrets Managerを参照するように更新してください。
- このコードはデモおよび出発点として提供されており、本番環境向けではありません。開発者として、全てのサードパーティ依存関係を適切に検証・保守・テストする責任があります。
- AWSはこのデモには実装されていない、アプリケーションのセキュリティを向上させる様々なサービスを提供しています。詳細はAWS共有責任モデルとセキュリティベストプラクティスガイダンスを参照してください。

## ライセンス
このアプリケーションはMIT-0ライセンスの下でライセンスされています。LICENSEファイルを参照してください。

## クリーンアップ
1. CloudFormationでスタックを削除
2. ECRのリポジトリを削除
