#!/bin/bash
set -e

echo "========================================="
echo "Frontend Preview Environment - Initializing"
echo "========================================="

# ロードしてない場合は .env をロード
if [ -f /workspace/.env ]; then
    echo "✓ Loading .env configuration..."
    set -a
    source /workspace/.env
    set +a
else
    echo "⚠ .env file not found. Using defaults."
    echo "  Create .env from .env.example to configure AWS credentials."
fi

# LocalStack ヘルスチェック（10秒待機）
echo ""
echo "⏳ Waiting for LocalStack to be ready..."
for i in {1..30}; do
    if curl -s http://localstack:4566/_localstack/health | grep -q "running"; then
        echo "✓ LocalStack is ready"
        break
    fi
    echo "  Attempt $i/30..."
    sleep 1
    if [ $i -eq 30 ]; then
        echo "⚠ LocalStack health check timed out (will proceed anyway)"
    fi
done

# S3 セットアップスクリプト
echo ""
echo "Note: S3 buckets can be created manually with:"
echo "  python3 setup_s3.py"
echo ""

# バージョン情報を表示
echo ""
echo "Environment Info:"
echo "  Node.js: $(node --version)"
echo "  npm: $(npm --version)"
echo "  Python: $(python3 --version)"
echo "  AWS CDK: $(cdk --version 2>/dev/null || echo 'Not initialized')"
echo "  AWS CLI: $(aws --version 2>/dev/null || echo 'Not installed')"
echo ""

# CDKプロジェクトの初期化チェック
if [ ! -f /workspace/cdk.json ]; then
    echo "⚠ CDK project not initialized."
    echo "  Run: cdk init --language python"
else
    echo "✓ CDK project found"
fi

# React + Vite プロジェクトの確認
if [ -d /workspace/app ] && [ -f /workspace/app/package.json ]; then
    echo "✓ React + Vite project found"
    echo "  Installing dependencies..."
    cd /workspace/app
    npm install --quiet
    echo "✓ Dependencies installed"
    cd /workspace
else
    echo "⚠ React + Vite project not found at /workspace/app"
fi

echo ""
echo "========================================="
echo "Ready for development!"
echo "========================================="
echo ""

# コマンドを実行
exec "$@"
