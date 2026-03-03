terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # バックエンド設定は envs/<env>/backend.conf から注入する
  # 初期化コマンド: terraform init -backend-config="./envs/preview/backend.conf"
  backend "s3" {}
}

provider "aws" {
  region = var.region

  # 全リソースに共通タグを付与
  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.env
      ManagedBy   = "terraform"
    }
  }
}
