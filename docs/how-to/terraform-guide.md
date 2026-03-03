# Terraform 手順書

Terraform を使ってフロントエンドプレビュー環境（S3 + CloudFront）を構築・管理する手順書です。

---

## 前提条件

- Terraform >= 1.9 がインストール済み
- AWS CLI が設定済み（`aws configure` 済み、または環境変数で認証情報を設定）
- S3 バケット（State 保存用）と DynamoDB テーブル（State ロック用）が事前作成済み

### 事前リソースの作成

Terraform の State を保存するバックエンドリソースを手動で作成してください。

```bash
# State 保存用 S3 バケット（バージョニング・暗号化を有効化）
aws s3api create-bucket \
  --bucket your-tfstate-bucket \
  --region ap-northeast-1 \
  --create-bucket-configuration LocationConstraint=ap-northeast-1

aws s3api put-bucket-versioning \
  --bucket your-tfstate-bucket \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket your-tfstate-bucket \
  --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# State ロック用 DynamoDB テーブル
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-1
```

---

## ファイル構成

```
infra/
├── main.tf                        # Provider・バックエンド定義
├── variables.tf                   # 変数定義
├── outputs.tf                     # 出力定義
├── s3.tf                          # S3 バケット・バージョニング・バケットポリシー
├── cloudfront.tf                  # OAC + CloudFront ディストリビューション
├── .tflint.hcl                    # TFLint 設定
├── frontend-stack.yaml            # CloudFormation テンプレート（参照用）
└── envs/
    └── preview/
        ├── backend.conf           # State バックエンド設定（S3 + DynamoDB）
        └── default.tfvars         # preview 環境の変数値
```

---

## セットアップ手順

### 1. 変数ファイルの設定

```bash
# envs/preview/backend.conf を編集
# bucket, dynamodb_table を実際の値に変更
vi infra/envs/preview/backend.conf

# envs/preview/default.tfvars を編集
# s3_bucket_name を実際のバケット名に変更
vi infra/envs/preview/default.tfvars
```

`infra/envs/preview/default.tfvars` の設定項目：

| 変数名 | 説明 | 例 |
|---|---|---|
| `env` | 環境識別子 | `"preview"` |
| `app_name` | アプリ名（タグ用） | `"frontend-preview"` |
| `region` | AWS リージョン | `"ap-northeast-1"` |
| `s3_bucket_name` | S3 バケット名（必須・ユニーク） | `"myteam-frontend-preview"` |
| `distribution_comment` | CloudFront コメント | `"frontend-preview"` |
| `default_ttl` | キャッシュ TTL（秒） | `86400` |

### 2. 動作確認

```bash
# 構文チェック
./run.sh infra preview validate

# フォーマットチェック
./run.sh infra preview fmt-check

# 差分確認（実際のリソース変更はしない）
./run.sh infra preview plan
```

### 3. インフラ構築

```bash
# インタラクティブ（確認あり）
./run.sh infra preview apply

# 自動承認（CI/CD 向け）
./run.sh infra preview apply-auto
```

apply 完了後、出力値（Outputs）に CloudFront URL が表示されます。

```
cloudfront_url = "https://d1234abcd.cloudfront.net"
```

---

## Reactビルドのアップロード

インフラ構築後、React ビルドファイルを S3 の `/frontend/` パスにアップロードします。

```bash
# 1. React アプリをビルド
cd app
npm install
npm run build

# 2. S3 にアップロード（バケット名は出力値から取得）
aws s3 sync dist/ s3://<s3_bucket_name>/frontend/ --delete

# 3. CloudFront キャッシュを無効化（新しいコンテンツを即時反映）
aws cloudfront create-invalidation \
  --distribution-id <cloudfront_distribution_id> \
  --paths "/*"
```

`<s3_bucket_name>` と `<cloudfront_distribution_id>` は `terraform output` で確認できます。

```bash
cd infra
terraform output s3_bucket_name
terraform output cloudfront_distribution_id
terraform output cloudfront_url
```

---

## インフラ削除

```bash
# preview 環境のリソースを全削除
cd infra
terraform init -backend-config="./envs/preview/backend.conf" -reconfigure
terraform destroy -var-file="./envs/preview/default.tfvars"
```

> **注意**: バケット内にオブジェクトがある場合、S3 バケットの削除に失敗します。
> 先に `aws s3 rm s3://<バケット名>/ --recursive` で空にしてください。

---

## GitHub Actions による CI/CD

### 必要な設定

1. **OIDC プロバイダーの設定**
   AWS IAM コンソールで GitHub Actions 用の OIDC プロバイダーを作成してください。
   プロバイダー URL: `https://token.actions.githubusercontent.com`

2. **IAM ロールの作成**
   GitHub Actions から引き受けられる IAM ロールを作成し、必要な権限（S3、CloudFront 操作）を付与してください。

3. **シークレットの設定**
   リポジトリの Settings > Secrets and variables > Actions に以下を追加：

   | シークレット名 | 値 |
   |---|---|
   | `AWS_ROLE_ARN` | IAM ロールの ARN（例: `arn:aws:iam::123456789012:role/github-actions-terraform`） |

### ワークフロー動作

| イベント | ワークフロー | 内容 |
|---|---|---|
| PR to main（infra/ 変更） | `terraform-plan.yml` | `plan` を実行し PR にコメント |
| push to main（infra/ 変更） | `terraform-apply.yml` | `apply-auto` を自動実行 |

---

## 静的解析・セキュリティチェック

```bash
# TFLint（静的解析）
./run.sh infra preview lint

# Trivy（セキュリティスキャン）
./run.sh infra preview security
```

TFLint のインストール：https://github.com/terraform-linters/tflint
Trivy のインストール：https://trivy.dev/latest/getting-started/installation/

---

## CloudFormation との比較

| | CloudFormation | Terraform |
|---|---|---|
| **State 管理** | AWS マネージド | S3 + DynamoDB（自前） |
| **マルチクラウド** | AWS のみ | AWS 含む複数プロバイダー対応 |
| **差分確認** | Change Set | `terraform plan` |
| **ドリフト検出** | CloudFormation ドリフト検出 | `terraform plan` で確認 |
| **学習コスト** | 低（AWS コンソール操作） | 中（HCL 言語習得が必要） |
| **CI/CD 連携** | CodePipeline 等 | GitHub Actions / CircleCI 等 |
