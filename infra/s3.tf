# ===========================
# S3 バケット
# ===========================
# 用途：Vite ビルド出力（index.html, JS, CSS等）を保存
# セキュリティ：CloudFront OAC 経由のみアクセス可能
resource "aws_s3_bucket" "frontend" {
  bucket = var.s3_bucket_name
}

# バージョニング有効化：前のバージョンを保持、ロールバック可能
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

# パブリックアクセスブロック設定
# CFn テンプレートと同等：ポリシーベースで制御（CloudFront OAC 経由のみ許可）
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

# ===========================
# S3 バケットポリシー
# ===========================
# 用途：CloudFront ディストリビューションのみアクセス許可
# CloudFront distribution が作成された後に設定する必要があるため depends_on を指定
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  depends_on = [
    aws_cloudfront_distribution.frontend,
    aws_s3_bucket_public_access_block.frontend,
  ]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOACAccess"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            # このディストリビューション ARN 経由のアクセスのみ許可
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}
