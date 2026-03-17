#!/bin/bash
# CatGuard 自动提交脚本
# 用法: ./auto_commit.sh "变更描述"

REPO_DIR="/home/clawdbot/CatGuard-GitHub"
J1900_HOST="administrator@192.168.31.80"
J1900_PASS="123654789"
J1900_CODE_DIR="C:\\CatGuard"

# 从参数获取提交信息，或自动生成
if [ -z "$1" ]; then
    COMMIT_MSG="chore: auto sync from J1900 - $(date '+%Y-%m-%d %H:%M')"
else
    COMMIT_MSG="$1"
fi

echo "=========================================="
echo "CatGuard 自动提交"
echo "=========================================="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "提交信息: $COMMIT_MSG"
echo ""

# 1. 从 J1900 同步代码
echo "[1/4] 从 J1900 同步代码..."
mkdir -p "$REPO_DIR/deployment/j1900"

sshpass -p "$J1900_PASS" scp "$J1900_HOST:$J1900_CODE_DIR\\*.py" "$REPO_DIR/deployment/j1900/" 2>/dev/null
sshpass -p "$J1900_PASS" scp "$J1900_HOST:$J1900_CODE_DIR\\*.bat" "$REPO_DIR/deployment/j1900/" 2>/dev/null

echo "同步完成"

# 2. 检查变更
echo ""
echo "[2/4] 检查变更..."
cd "$REPO_DIR"
git status

# 3. 提交
echo ""
echo "[3/4] 提交变更..."
git add -A
git commit -m "$COMMIT_MSG"

# 4. 推送
echo ""
echo "[4/4] 推送到 GitHub..."
git push origin main

echo ""
echo "=========================================="
echo "✅ 提交完成!"
echo "仓库: https://github.com/ColinStayInLife/CatGuard"
echo "=========================================="