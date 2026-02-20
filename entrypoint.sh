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

# バージョン情報を表示
echo ""
echo "Environment Info:"
echo "  Node.js: $(node --version)"
echo "  npm: $(npm --version)"
echo "  Python: $(python3 --version)"
echo "  AWS CDK: $(cdk --version 2>/dev/null || echo 'Not initialized')"
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
