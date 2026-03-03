# Python スクリプトを使ったプレビュー環境の手順書

`scripts/deploy.py` を使ってプレビュー環境を自動構築・削除する手順です。

S3バケット作成・Reactビルド・S3アップロード・CloudFront作成まで1コマンドで実行できます。

---

## 前提条件

- Python 3.x がインストールされていること
- Node.js / npm がインストールされていること
- AWSアカウントへのアクセス権限（S3・CloudFront・STSの操作権限）
- AWS アクセスキーとシークレットキーが手元にあること

---

## 環境構築（作成）

### 全体の流れ

```mermaid
flowchart TD
    A[.envファイルを作成] --> B[依存パッケージをインストール]
    B --> C[python scripts/deploy.py を実行]
    C --> D[S3バケット作成]
    D --> E[npm install & npm run build]
    E --> F[S3にアップロード]
    F --> G[CloudFrontディストリビューション作成]
    G --> H[S3バケットポリシー設定]
    H --> I[CloudFront URLでアクセス確認]
```

---

### ステップ1: `.env` ファイルを作成する

プロジェクトルートに `.env` ファイルを作成し、AWS認証情報を設定します。

```bash
# プロジェクトルートで実行
cp .env.example .env   # .env.example がある場合
# または直接作成
```

`.env` の内容：

```
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-bucket-name
CLOUDFRONT_DISTRIBUTION_NAME=Frontend Preview Distribution
```

| 項目 | 説明 | 例 |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | AWSアクセスキーID | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWSシークレットアクセスキー | `wJalrXUtnFEMI/...` |
| `AWS_REGION` | AWSリージョン | `ap-northeast-1`（東京） |
| `S3_BUCKET_NAME` | 作成するS3バケット名（全世界で一意） | `41th-frontend-preview` |
| `CLOUDFRONT_DISTRIBUTION_NAME` | CloudFrontの説明（任意） | `Frontend Preview Distribution` |

> `.env` ファイルは `.gitignore` に含まれています。AWSキーをGitにコミットしないよう注意してください。

---

### ステップ2: 依存パッケージをインストールする

```bash
pip install -r requirements.txt
```

---

### ステップ3: デプロイスクリプトを実行する

```bash
python scripts/deploy.py
```

スクリプトが以下を自動で実行します：

1. S3バケットの作成（既存の場合はスキップ）
2. `npm install`（Reactの依存パッケージインストール）
3. `npm run build`（Reactのビルド）
4. ビルド成果物（`app/dist/`）をS3の `frontend/` にアップロード
5. CloudFrontディストリビューションの作成（OAC設定込み）
6. S3バケットポリシーの設定（CloudFront経由のみアクセス許可）

---

### ステップ4: アクセス確認

スクリプト完了後にターミナルに表示されるURLでアクセスします。

```
==================================================
✅ セットアップ完了！
==================================================
🌐 アクセスURL: https://d123xyz.cloudfront.net
🔒 セキュリティ: OAC有効化 (CloudFront経由のみアクセス可)
🔐 HTTPS強制化
⏳ デプロイ完了まで15分～数時間かかる場合があります
==================================================
```

> CloudFrontのデプロイ完了まで15分〜数時間かかる場合があります。

---

## コンテンツの更新（再デプロイ）

Reactを修正した場合はスクリプトを再実行するだけです。

```bash
python scripts/deploy.py
```

S3バケットとCloudFrontは既存のものを再利用し、ビルド＆アップロードのみ実行します。

キャッシュが残っている場合はAWSコンソールからCloudFrontの無効化（Invalidation）を実行してください：
- AWSコンソール → CloudFront → ディストリビューション → 「無効化」タブ
- オブジェクトパス: `/*`

---

## 環境削除

Python スクリプトによる自動削除機能はないため、AWSコンソールから手動で削除します。

### 全体の流れ

```mermaid
flowchart TD
    A[CloudFrontディストリビューションを削除] --> B[S3バケットを空にする]
    B --> C[S3バケットを削除]
    C --> D[全リソース削除完了]
```

---

### ステップ1: CloudFront ディストリビューションを削除する

1. AWSコンソール → **CloudFront** → 対象ディストリビューションを選択

2. 「無効化」をクリック（Enabled → Disabled）

3. ステータスが `Disabled` になるまで待機（数分〜数十分）

4. 「削除」をクリックして削除

---

### ステップ2: S3バケットを空にして削除する

1. AWSコンソール → **S3** → 対象バケットを選択

2. 「空にする」ボタンをクリック → `permanently delete` と入力して実行

3. 「削除」ボタンをクリックしてバケットを削除

---

### （参考）AWS CLI で削除する場合

```bash
# S3バケットを空にして削除
aws s3 rm s3://your-bucket-name --recursive
aws s3 rb s3://your-bucket-name

# CloudFrontディストリビューションの無効化・削除
# （コンソールからの操作を推奨）
```
