variable "env" {
  type        = string
  description = "環境識別子（例: preview）"
}

variable "app_name" {
  type        = string
  default     = "frontend-preview"
  description = "アプリ名（default_tags に使用）"
}

variable "region" {
  type        = string
  default     = "ap-northeast-1"
  description = "AWS リージョン"
}

variable "s3_bucket_name" {
  type        = string
  description = "S3 バケット名（Reactビルドファイルを保存）。小文字・数字・ハイフンのみ使用可"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.s3_bucket_name))
    error_message = "小文字、数字、ハイフンのみ使用可。例：frontend-preview-bucket"
  }
}

variable "distribution_comment" {
  type        = string
  default     = "frontend-preview"
  description = "CloudFront ディストリビューションのコメント（識別用）"
}

variable "default_ttl" {
  type        = number
  default     = 86400
  description = "CloudFront キャッシュの有効期限（秒）。デフォルト 86400秒 = 1日"

  validation {
    condition     = var.default_ttl >= 0 && var.default_ttl <= 31536000
    error_message = "default_ttl は 0 〜 31536000 の範囲で指定してください。"
  }
}
