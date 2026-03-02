import boto3
import sys
import logging
import os
import subprocess
import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME, CLOUDFRONT_DISTRIBUTION_NAME

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# botocore、boto3のDEBUGログを抑止
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def create_s3_bucket():
    """S3バケットを作成"""
    try:
        logger.info("=== S3バケット作成処理開始 ===")
        logger.debug(f"AWS_REGION: {AWS_REGION}")
        logger.debug(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}")
        logger.debug(f"AWS_ACCESS_KEY_ID設定: {bool(AWS_ACCESS_KEY_ID)}")
        
        if not S3_BUCKET_NAME:
            logger.error("S3_BUCKET_NAMEが設定されていません")
            sys.exit(1)
        
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            logger.error("AWSの認証情報が設定されていません")
            sys.exit(1)
        
        logger.info("S3クライアントを初期化中...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        logger.info("S3クライアティアルの初期化完了")
        
        # バケット作成
        logger.info(f"S3バケット '{S3_BUCKET_NAME}' を作成中...")
        if AWS_REGION == 'us-east-1':
            logger.debug("us-east-1リージョン: LocationConstraintなしで作成")
            s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            logger.debug(f"LocationConstraintを {AWS_REGION} に設定")
            s3_client.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
            )
        
        logger.info(f"✓ S3バケット '{S3_BUCKET_NAME}' を作成しました")
        logger.info("=== S3バケット作成処理完了 ===")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'BucketAlreadyOwnedByYou':
            logger.warning(f"✓ S3バケット '{S3_BUCKET_NAME}' は既に存在します（あなたが所有）")
            logger.info("=== S3バケット作成処理完了（スキップ） ===")
        elif error_code == 'BucketAlreadyExists':
            logger.error(f"✗ バケット名'{S3_BUCKET_NAME}'は既に別のユーザーに使用されています")
            logger.error(f"   別のバケト名を使用してください")
            sys.exit(1)
        else:
            logger.error(f"✗ AWSエラー [{error_code}]: {error_message}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


def create_cloudfront_distribution():
    """CloudFrontディストリビューションを作成"""
    try:
        logger.info("=== CloudFront ディストリビューション作成処理開始 ===")
        
        # CloudFront クライアント初期化
        cloudfront_client = boto3.client(
            'cloudfront',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # S3 Origin Domain Name を構築
        s3_origin_domain = f"{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"
        logger.info(f"S3 Origin Domain: {s3_origin_domain}")
        
        # ディストリビューション設定
        distribution_config = {
            'CallerReference': f"frontend-preview-{int(__import__('time').time())}",
            'Comment': CLOUDFRONT_DISTRIBUTION_NAME,
            'DefaultRootObject': 'frontend/index.html',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f'{S3_BUCKET_NAME}-origin',
                        'DomainName': s3_origin_domain,
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': f'{S3_BUCKET_NAME}-origin',
                'ViewerProtocolPolicy': 'allow-all',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000
            },
            'Enabled': True
        }
        
        logger.info("CloudFront ディストリビューションを作成中...")
        response = cloudfront_client.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution_id = response['Distribution']['Id']
        domain_name = response['Distribution']['DomainName']
        
        logger.info(f"✓ CloudFront ディストリビューションを作成しました")
        logger.info(f"  Distribution ID: {distribution_id}")
        logger.info(f"  Domain Name: {domain_name}")
        logger.info(f"  Status: {response['Distribution']['Status']}")
        logger.info(f"  ⏳ ディストリビューションのデプロイ中... (15分～数時間かかる場合があります)")
        logger.info("=== CloudFront ディストリビューション作成処理完了 ===")
        
        return {
            'distribution_id': distribution_id,
            'domain_name': domain_name
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"✗ CloudFrontエラー [{error_code}]: {error_message}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


def set_s3_bucket_policy(cloudfront_id):
    """S3バケットポリシーを設定してCloudFrontからのアクセスを許可"""
    try:
        logger.info("=== S3バケットポリシー設定開始 ===")
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        # Block Public Access を無効化
        logger.info("Block Public Access を無効化中...")
        s3_client.put_public_access_block(
            Bucket=S3_BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        logger.info("✓ Block Public Access を無効化しました")
        
        # S3バケットポリシーを設定
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudFrontAccess",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
                }
            ]
        }
        
        import json
        logger.info("S3バケットポリシーを設定中...")
        s3_client.put_bucket_policy(
            Bucket=S3_BUCKET_NAME,
            Policy=json.dumps(bucket_policy)
        )
        
        logger.info("✓ S3バケットポリシーを設定しました")
        logger.info("=== S3バケットポリシー設定完了 ===")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"✗ S3ポリシー設定エラー [{error_code}]: {error_message}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


def build_and_upload_react_app():
    """Reactアプリをビルドしてs3にアップロード"""
    try:
        logger.info("=== React ビルド・アップロード処理開始 ===")
        
        # パス設定
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_dir = os.path.join(project_root, 'app')
        dist_dir = os.path.join(app_dir, 'dist')
        
        logger.info(f"アプリケーションディレクトリ: {app_dir}")
        
        # npm install 実行
        logger.info("npm 依存関係をインストール中...")
        install_result = subprocess.run(
            ['npm', 'install'],
            cwd=app_dir,
            capture_output=True,
            text=True
        )
        
        if install_result.returncode != 0:
            logger.error(f"✗ npm install が失敗しました")
            logger.error(f"STDOUT: {install_result.stdout}")
            logger.error(f"STDERR: {install_result.stderr}")
            sys.exit(1)
        
        logger.info("✓ npm install 完了")
        
        # ビルド実行
        logger.info("Reactアプリをビルド中...")
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd=app_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"✗ ビルドが失敗しました")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            sys.exit(1)
        
        logger.info("✓ ビルド完了")
        
        # distディレクトリの確認
        if not os.path.exists(dist_dir):
            logger.error(f"✗ ビルド出力ディレクトリが見つかりません: {dist_dir}")
            sys.exit(1)
        
        logger.info(f"ビルド出力ディレクトリ: {dist_dir}")
        
        # S3接続
        logger.info("S3クライアントを初期化中...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        logger.info("S3クライアント初期化完了")
        
        # ファイルをS3にアップロード
        logger.info(f"ファイルをS3 '{S3_BUCKET_NAME}' にアップロード中...")
        upload_count = 0
        
        for file_path in Path(dist_dir).rglob('*'):
            if file_path.is_file():
                # S3キーを計算（dist以下の相対パス）
                relative_path = file_path.relative_to(dist_dir)
                s3_key = f"frontend/{relative_path}".replace('\\', '/')
                
                # Content-Typeを自動判定
                content_type, _ = mimetypes.guess_type(str(file_path))
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                logger.debug(f"アップロード: {relative_path} -> s3://{S3_BUCKET_NAME}/{s3_key} (Content-Type: {content_type})")
                
                # Content-Type を指定してアップロード
                with open(file_path, 'rb') as f:
                    s3_client.put_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=s3_key,
                        Body=f,
                        ContentType=content_type
                    )
                upload_count += 1
        
        logger.info(f"✓ {upload_count}個のファイルをアップロードしました")
        logger.info("=== React ビルド・アップロード処理完了 ===")
        
    except Exception as e:
        logger.error(f"✗ 予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    create_s3_bucket()
    build_and_upload_react_app()
    cf_info = create_cloudfront_distribution()
    set_s3_bucket_policy(cf_info['distribution_id'])
    logger.info(f"\n{'='*50}")
    logger.info(f"✅ セットアップ完了！")
    logger.info(f"{'='*50}")
    logger.info(f"🌐 アクセスURL: https://{cf_info['domain_name']}")
    logger.info(f"⏳ デプロイ完了まで15分～数時間かかる場合があります")
    logger.info(f"{'='*50}")
