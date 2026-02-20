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

# React プロジェクトの初期化チェック
if [ ! -f /workspace/package.json ]; then
    echo "⚠ React project not initialized."
    echo "  Run: npm create vite@latest app -- --template react"
else
    echo "✓ React project found"
fi

echo ""
echo "========================================="
echo "Ready for development!"
echo "========================================="
echo ""

# コマンドを実行
exec "$@"
