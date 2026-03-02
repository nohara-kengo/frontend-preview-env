"""
Frontend Preview Environment のデプロイスクリプト

Reactアプリをビルドし、AWS S3にアップロード、CloudFrontで配信する
完全自動されたデプロイパイプラインです。

処理フロー：
    1. S3バケット作成（既存の場合はスキップ）
    2. React アプリケーションのビルド
    3. ビルド成果物を S3 にアップロード
    4. CloudFront ディストリビューション作成
    5. Origin Access Control (OAC) 設定
    6. S3 バケットポリシー設定（セキュリティ強化）

セキュリティ対応：
    - OAC による S3 直接アクセス防止
    - HTTPS 強制化
    - Content-Type 自動設定
    - CloudFront キャッシング

実行方法：
    python scripts/deploy.py

環境変数（.envファイルまたはOS環境変数）：
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION
    - S3_BUCKET_NAME
    - CLOUDFRONT_DISTRIBUTION_NAME
"""

import json
import logging
import mimetypes
import os
import subprocess
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    CLOUDFRONT_DISTRIBUTION_NAME,
    S3_BUCKET_NAME,
)

# ===========================
# ロギング設定
# ===========================

logger = logging.getLogger(__name__)


def setup_logging():
    """ロギング設定を初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 外部ライブラリのDEBUGログを抑止
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# ===========================
# AWS クライアント初期化
# ===========================


def get_s3_client():
    """S3クライアントを初期化して返す

    Returns:
        boto3.client: S3クライアント
    """
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def get_cloudfront_client():
    """CloudFrontクライアントを初期化して返す

    Returns:
        boto3.client: CloudFrontクライアント
    """
    return boto3.client(
        "cloudfront",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def get_sts_client():
    """STSクライアントを初期化して返す

    Returns:
        boto3.client: STSクライアント
    """
    return boto3.client(
        "sts",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


# ===========================
# ユーティリティ関数
# ===========================


def get_aws_account_id():
    """AWSアカウントIDを取得

    Returns:
        str: AWSアカウントID

    Raises:
        SystemExit: アカウント取得に失敗した場合
    """
    try:
        sts_client = get_sts_client()
        account_id = sts_client.get_caller_identity()["Account"]
        return account_id
    except Exception as e:
        logger.error(f"✗ アカウントID取得エラー: {e}")
        sys.exit(1)


def validate_environment():
    """環境変数の検証

    Raises:
        SystemExit: 必須環境変数が設定されていない場合
    """
    if not S3_BUCKET_NAME:
        logger.error("S3_BUCKET_NAMEが設定されていません")
        sys.exit(1)

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.error("AWSの認証情報が設定されていません")
        sys.exit(1)

    logger.debug(f"AWS_REGION: {AWS_REGION}")
    logger.debug(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}")
    logger.debug(f"AWS_ACCESS_KEY_ID設定: {bool(AWS_ACCESS_KEY_ID)}")


# ===========================
# S3 処理
# ===========================


def create_s3_bucket():
    """S3バケットを作成

    既存バケットの場合はスキップします。

    Raises:
        SystemExit: バケット作成に失敗した場合
    """
    logger.info("=== S3バケット作成処理開始 ===")
    validate_environment()

    try:
        s3_client = get_s3_client()
        logger.info(f"S3バケット '{S3_BUCKET_NAME}' を作成中...")

        # リージョン設定
        if AWS_REGION == "us-east-1":
            logger.debug("us-east-1リージョン: LocationConstraintなしで作成")
            s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            logger.debug(f"LocationConstraintを {AWS_REGION} に設定")
            s3_client.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )

        logger.info(f"✓ S3バケット '{S3_BUCKET_NAME}' を作成しました")
        logger.info("=== S3バケット作成処理完了 ===")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        if error_code == "BucketAlreadyOwnedByYou":
            logger.warning(
                f"✓ S3バケット '{S3_BUCKET_NAME}' は既に存在します（あなたが所有）"
            )
            logger.info("=== S3バケット作成処理完了（スキップ） ===")
        elif error_code == "BucketAlreadyExists":
            logger.error(
                f"✗ バケット名'{S3_BUCKET_NAME}'は既に別のユーザーに使用されています"
            )
            logger.error("   別のバケト名を使用してください")
            sys.exit(1)
        else:
            logger.error(f"✗ AWSエラー [{error_code}]: {error_message}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


def disable_public_access_block():
    """S3 Block Public Access を無効化

    CloudFrontを経由した公開アクセスを許可するために必要です。

    Raises:
        SystemExit: 設定に失敗した場合
    """
    logger.info("Block Public Access を無効化中...")
    try:
        s3_client = get_s3_client()
        s3_client.put_public_access_block(
            Bucket=S3_BUCKET_NAME,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        logger.info("✓ Block Public Access を無効化しました")
    except Exception as e:
        logger.error(f"✗ Block Public Access 設定エラー: {e}")
        sys.exit(1)


def set_s3_bucket_policy(cloudfront_info):
    """S3バケットポリシーを設定（CloudFront経由のみアクセス許可）

    OACを使用した最新のセキュアな設定を適用します。

    Args:
        cloudfront_info (dict): CloudFront情報
            - distribution_id (str): ディストリビューションID
            - domain_name (str): ドメイン名

    Raises:
        SystemExit: ポリシー設定に失敗した場合
    """
    logger.info("=== S3バケットポリシー設定開始 ===")

    try:
        disable_public_access_block()

        # OAC使用のセキュアなポリシー
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudFrontOACAccess",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudfront.amazonaws.com"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": f"arn:aws:cloudfront::{get_aws_account_id()}:distribution/{cloudfront_info['distribution_id']}"
                        }
                    },
                }
            ],
        }

        s3_client = get_s3_client()
        logger.info("S3バケットポリシーを設定中...")
        s3_client.put_bucket_policy(
            Bucket=S3_BUCKET_NAME, Policy=json.dumps(bucket_policy)
        )

        logger.info(
            "✓ S3バケットポリシーを設定しました（CloudFront経由のみ許可）"
        )
        logger.info("✓ セキュリティベストプラクティス: OAC有効化完了")
        logger.info("=== S3バケットポリシー設定完了 ===")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"✗ S3ポリシー設定エラー [{error_code}]: {error_message}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


# ===========================
# React ビルド・アップロード処理
# ===========================


def build_react_app():
    """Reactアプリケーションをビルド

    Viteを使用してReactアプリをビルドします。

    Returns:
        str: ビルド出力ディレクトリのパス

    Raises:
        SystemExit: ビルドに失敗した場合
    """
    logger.info("Reactアプリをビルド中...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.join(project_root, "app")

    result = subprocess.run(
        ["npm", "run", "build"], cwd=app_dir, capture_output=True, text=True
    )

    if result.returncode != 0:
        logger.error("✗ ビルドが失敗しました")
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")
        sys.exit(1)

    logger.info("✓ ビルド完了")
    return os.path.join(app_dir, "dist")


def install_frontend_dependencies():
    """フロントエンド依存パッケージをインストール

    Raises:
        SystemExit: インストールに失敗した場合
    """
    logger.info("npm 依存関係をインストール中...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.join(project_root, "app")

    result = subprocess.run(
        ["npm", "install"], cwd=app_dir, capture_output=True, text=True
    )

    if result.returncode != 0:
        logger.error("✗ npm install が失敗しました")
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")
        sys.exit(1)

    logger.info("✓ npm install 完了")


def upload_to_s3(dist_dir):
    """ビルド成果物をS3にアップロード

    Content-Typeを自動判定して設定します。

    Args:
        dist_dir (str): ビルド出力ディレクトリのパス

    Raises:
        SystemExit: アップロードに失敗した場合
    """
    logger.info("=== React ビルド・アップロード処理開始 ===")
    logger.info(f"アプリケーションディレクトリ: {os.path.dirname(dist_dir)}")

    try:
        if not os.path.exists(dist_dir):
            logger.error(f"✗ ビルド出力ディレクトリが見つかりません: {dist_dir}")
            sys.exit(1)

        logger.info(f"ビルド出力ディレクトリ: {dist_dir}")

        s3_client = get_s3_client()
        logger.info(f"ファイルをS3 '{S3_BUCKET_NAME}' にアップロード中...")
        upload_count = 0

        for file_path in Path(dist_dir).rglob("*"):
            if file_path.is_file():
                # S3キーを計算（dist相対パス）
                relative_path = file_path.relative_to(dist_dir)
                s3_key = f"frontend/{relative_path}".replace("\\", "/")

                # Content-Type自動判定
                content_type, _ = mimetypes.guess_type(str(file_path))
                if content_type is None:
                    content_type = "application/octet-stream"

                logger.debug(
                    f"アップロード: {relative_path} -> s3://{S3_BUCKET_NAME}/{s3_key} (Content-Type: {content_type})"
                )

                # ファイルをアップロード
                with open(file_path, "rb") as f:
                    s3_client.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=s3_key,
                        Body=f,
                        ContentType=content_type,
                    )
                upload_count += 1

        logger.info(f"✓ {upload_count}個のファイルをアップロードしました")
        logger.info("=== React ビルド・アップロード処理完了 ===")

    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


# ===========================
# CloudFront 処理
# ===========================


def create_origin_access_control(cloudfront_client):
    """Origin Access Control (OAC) を作成

    CloudFrontがS3に安全にアクセスするためのOACを作成します。

    Args:
        cloudfront_client (boto3.client): CloudFrontクライアント

    Returns:
        str: OAC ID

    Raises:
        Exception: OAC作成に失敗した場合
    """
    logger.info("Origin Access Control (OAC) を作成中...")

    oac_config = {
        "Name": f"{S3_BUCKET_NAME}-oac",
        "Description": f"OAC for {S3_BUCKET_NAME}",
        "OriginAccessControlOriginType": "s3",
        "SigningBehavior": "always",
        "SigningProtocol": "sigv4",
    }

    oac_response = cloudfront_client.create_origin_access_control(
        OriginAccessControlConfig=oac_config
    )
    oac_id = oac_response["OriginAccessControl"]["Id"]
    logger.info(f"✓ OAC を作成しました (ID: {oac_id})")

    return oac_id


def create_cloudfront_distribution():
    """CloudFrontディストリビューションを作成

    OACとHTTPS強制化を含む安全な構成で作成します。

    Returns:
        dict: CloudFront情報
            - distribution_id (str): ディストリビューションID
            - domain_name (str): CloudFrontドメイン
            - oac_id (str): OAC ID

    Raises:
        SystemExit: ディストリビューション作成に失敗した場合
    """
    logger.info("=== CloudFront ディストリビューション作成処理開始 ===")

    try:
        cloudfront_client = get_cloudfront_client()

        # OAC作成
        oac_id = create_origin_access_control(cloudfront_client)

        # S3 Origin Domain Name
        s3_origin_domain = f"{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"
        logger.info(f"S3 Origin Domain: {s3_origin_domain}")

        # ディストリビューション設定
        distribution_config = {
            "CallerReference": f"frontend-preview-{int(__import__('time').time())}",
            "Comment": CLOUDFRONT_DISTRIBUTION_NAME,
            "DefaultRootObject": "index.html",
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": f"{S3_BUCKET_NAME}-origin",
                        "DomainName": s3_origin_domain,
                        "OriginPath": "/frontend",
                        "S3OriginConfig": {"OriginAccessIdentity": ""},
                        "OriginAccessControlId": oac_id,
                    }
                ],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": f"{S3_BUCKET_NAME}-origin",
                "ViewerProtocolPolicy": "redirect-to-https",  # HTTPS強制化
                "TrustedSigners": {"Enabled": False, "Quantity": 0},
                "ForwardedValues": {"QueryString": False, "Cookies": {"Forward": "none"}},
                "MinTTL": 0,
                "DefaultTTL": 86400,
                "MaxTTL": 31536000,
            },
            "Enabled": True,
        }

        logger.info("CloudFront ディストリビューションを作成中...")
        response = cloudfront_client.create_distribution(
            DistributionConfig=distribution_config
        )

        distribution_id = response["Distribution"]["Id"]
        domain_name = response["Distribution"]["DomainName"]

        logger.info("✓ CloudFront ディストリビューションを作成しました")
        logger.info(f"  Distribution ID: {distribution_id}")
        logger.info(f"  Domain Name: {domain_name}")
        logger.info(f"  Status: {response['Distribution']['Status']}")
        logger.info("  ⏳ ディストリビューションのデプロイ中...")
        logger.info("     15分～数時間かかる場合があります")
        logger.info("=== CloudFront ディストリビューション作成処理完了 ===")

        return {
            "distribution_id": distribution_id,
            "domain_name": domain_name,
            "oac_id": oac_id,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"✗ CloudFrontエラー [{error_code}]: {error_message}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


# ===========================
# メイン処理
# ===========================


def main():
    """メインデプロイ処理"""
    setup_logging()
    logger.info("🚀 Frontend Preview Environment デプロイ開始")

    # ステップ1: S3バケット作成
    create_s3_bucket()

    # ステップ2: React依存パッケージインストール
    install_frontend_dependencies()

    # ステップ3: React アプリビルド
    dist_dir = build_react_app()

    # ステップ4: S3にアップロード
    upload_to_s3(dist_dir)

    # ステップ5: CloudFront ディストリビューション作成
    cf_info = create_cloudfront_distribution()

    # ステップ6: S3ポリシー設定（最後に設定で、既に作成済みのリソースに対応）
    set_s3_bucket_policy(cf_info)

    # 完了メッセージ
    logger.info(f"\n{'='*50}")
    logger.info("✅ セットアップ完了！")
    logger.info(f"{'='*50}")
    logger.info(f"🌐 アクセスURL: https://{cf_info['domain_name']}")
    logger.info("🔒 セキュリティ: OAC有効化 (CloudFront経由のみアクセス可)")
    logger.info("🔐 HTTPS強制化")
    logger.info("⏳ デプロイ完了まで15分～数時間かかる場合があります")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    main()
