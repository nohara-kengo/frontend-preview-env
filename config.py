import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
CLOUDFRONT_DISTRIBUTION_NAME = os.getenv('CLOUDFRONT_DISTRIBUTION_NAME', 'frontend-preview')
