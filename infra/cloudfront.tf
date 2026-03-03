# ===========================
# Origin Access Control (OAC)
# ===========================
# 用途：CloudFront から S3 へのセキュアなアクセス制御
# sigv4 署名（AWS Signature Version 4）で署名、OAI より新しい方式
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.s3_bucket_name}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
  description                       = "OAC for ${var.s3_bucket_name} frontend preview"
}

# ===========================
# CloudFront ディストリビューション
# ===========================
# 用途：グローバル CDN で React SPA を配信
# プロトコル：HTTPS 必須、HTTP 自動リダイレクト
# キャッシュ：default_ttl 変数で制御可能
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  comment             = var.distribution_comment
  default_root_object = "index.html"
  http_version        = "http2and3"
  price_class         = "PriceClass_All"

  # Origin（S3）の設定
  origin {
    origin_id                = "S3Origin"
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_path              = "/frontend" # S3 内の仮想パス（s3://bucket/frontend/）
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # キャッシュ動作（デフォルト）
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
    target_origin_id       = "S3Origin"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }

      headers = [
        "Accept",
        "Accept-Charset",
        "Accept-Encoding",
        "Accept-Language",
      ]
    }

    min_ttl     = 0
    default_ttl = var.default_ttl
    max_ttl     = 31536000
  }

  # カスタムエラーレスポンス（SPA ルーティング対応）
  # React Router など SPA ライブラリの独自ルーティングで 403/404 が返った場合、
  # index.html を返すことで React 側でルーティング処理させる
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
