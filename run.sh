#!/bin/bash
# Terraform ラッパースクリプト
#
# 使い方: ./run.sh <root> <env> <action>
# 例:     ./run.sh infra preview plan
#
# root    : Terraform ファイルのあるディレクトリ（例: infra）
# env     : 環境識別子（例: preview）。envs/<env>/ にバックエンド設定と tfvars を配置
# action  : 実行するアクション（下記一覧参照）
#
# Actions:
#   plan        - 差分確認（terraform plan）
#   apply       - インタラクティブな apply（確認あり）
#   apply-auto  - 自動 apply（確認なし。CI/CD 向け）
#   fmt         - コードフォーマット
#   fmt-check   - フォーマットチェックのみ（CI 向け）
#   validate    - 構文チェック
#   lint        - TFLint による静的解析
#   security    - Trivy による設定セキュリティスキャン

set -euo pipefail

ROOT=${1:?"Error: root directory が指定されていません。使い方: ./run.sh <root> <env> <action>"}
ENV=${2:?"Error: env が指定されていません。使い方: ./run.sh <root> <env> <action>"}
ACTION=${3:?"Error: action が指定されていません。使い方: ./run.sh <root> <env> <action>"}

cd "$ROOT"

terraform init -backend-config="./envs/${ENV}/backend.conf" -reconfigure

case "$ACTION" in
  plan)
    terraform plan -var-file="./envs/${ENV}/default.tfvars"
    ;;
  apply)
    terraform apply -var-file="./envs/${ENV}/default.tfvars"
    ;;
  apply-auto)
    terraform apply -var-file="./envs/${ENV}/default.tfvars" -auto-approve
    ;;
  fmt)
    terraform fmt -recursive
    ;;
  fmt-check)
    terraform fmt -check -recursive
    ;;
  validate)
    terraform validate
    ;;
  lint)
    tflint --init && tflint
    ;;
  security)
    trivy config .
    ;;
  *)
    echo "Error: 不明なアクション '${ACTION}'"
    echo "利用可能なアクション: plan, apply, apply-auto, fmt, fmt-check, validate, lint, security"
    exit 1
    ;;
esac
