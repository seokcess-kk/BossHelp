#!/bin/bash
# BossHelp Railway Environment Setup Script
# Usage: bash setup-railway-env.sh

echo "🚂 Railway 환경변수 설정"
echo "========================"
echo ""

# 사용자 입력 받기
read -p "SUPABASE_URL (https://xxx.supabase.co): " SUPABASE_URL
read -p "SUPABASE_SERVICE_KEY: " SUPABASE_SERVICE_KEY
read -p "ANTHROPIC_API_KEY (sk-ant-...): " ANTHROPIC_API_KEY
read -p "OPENAI_API_KEY (sk-...): " OPENAI_API_KEY
read -p "Frontend URL for CORS (https://xxx.vercel.app): " CORS_ORIGINS
read -p "ADMIN_API_KEY (임의의 보안 키): " ADMIN_API_KEY

echo ""
echo "설정할 환경변수:"
echo "  SUPABASE_URL: $SUPABASE_URL"
echo "  SUPABASE_SERVICE_KEY: [hidden]"
echo "  ANTHROPIC_API_KEY: [hidden]"
echo "  OPENAI_API_KEY: [hidden]"
echo "  CORS_ORIGINS: $CORS_ORIGINS"
echo "  ADMIN_API_KEY: [hidden]"
echo "  ENV: production"
echo ""

read -p "계속 진행하시겠습니까? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "환경변수 설정 중..."

railway variables set SUPABASE_URL="$SUPABASE_URL"
railway variables set SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY"
railway variables set ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set CORS_ORIGINS="$CORS_ORIGINS"
railway variables set ADMIN_API_KEY="$ADMIN_API_KEY"
railway variables set ENV="production"

echo ""
echo "✅ 환경변수 설정 완료!"
echo ""
echo "설정된 변수 확인:"
railway variables

echo ""
echo "다음 명령어로 배포하세요:"
echo "  railway up"
