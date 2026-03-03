output "s3_bucket_name" {
  description = "S3 バケット名（deploy.py でアップロード先として使用）"
  value       = aws_s3_bucket.frontend.id
}

output "s3_bucket_arn" {
  description = "S3 バケット ARN（IAM ポリシー等で参照時に使用）"
  value       = aws_s3_bucket.frontend.arn
}

output "origin_access_control_id" {
  description = "Origin Access Control ID（CloudFront 再設定時に参照）"
  value       = aws_cloudfront_origin_access_control.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront ディストリビューション ID（キャッシュ無効化時に使用）"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront ドメイン名（自動生成、AWS で発行）"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_url" {
  description = "フロントエンド アクセス URL（ユーザーに共有するリンク）"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
