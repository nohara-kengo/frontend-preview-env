#!/bin/bash

echo "========================================="
echo "Frontend Preview Env - Project Initializer"
echo "========================================="
echo ""

# .env ファイルの作成
if [ ! -f .env ]; then
    echo "1️⃣  Creating .env file from template..."
    cp .env.example .env
    echo "   ✓ .env created. Update with your AWS credentials."
else
    echo "1️⃣  .env file already exists. Skipping..."
fi

# AWS CDK プロジェクトの初期化
if [ ! -f cdk.json ]; then
    echo ""
    echo "2️⃣  Initializing AWS CDK project..."
    cdk init --language python
    echo "   ✓ CDK project initialized"
else
    echo ""
    echo "2️⃣  CDK project already exists. Skipping..."
fi

# React アプリケーションの初期化
if [ ! -f app/package.json ]; then
    echo ""
    echo "3️⃣  Initializing React application..."
    npm create vite@latest app -- --template react
    cd app && npm install && cd ..
    echo "   ✓ React app initialized"
else
    echo ""
    echo "3️⃣  React project already exists. Skipping..."
fi

echo ""
echo "========================================="
echo "✅ Project initialization complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Update .env with your AWS credentials"
echo "  2. Review cdk/lib/cdk_stack.py and customize as needed"
echo "  3. Test: npm run build (in app directory)"
echo "  4. Deploy: cdk deploy"
echo ""
