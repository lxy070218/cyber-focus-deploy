#!/bin/bash
# ============================================================
# Cyber Focus - CodeArts 流水线部署脚本
# 功能：拉取最新代码 → 安装后端依赖 → 打包前端 → 重启服务
# 用法：在 CodeArts 流水线 Shell 步骤中执行 bash deploy.sh
# ============================================================
set -euo pipefail

# ---------- 部署配置 ----------
DEPLOY_ROOT="/opt/cyber-focus"
BACKEND_DIR="$DEPLOY_ROOT/backend"
FRONTEND_DIR="$DEPLOY_ROOT/frontend"
REPO_URL="https://atomgit.com/2502_93773167/cyber-focus.git"
BRANCH="main"
SERVICE_NAME="cyber-focus-backend.service"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ---------- 1. 拉取最新代码 ----------
log "==> [1/5] 拉取最新代码 (分支: $BRANCH)"
if [ -d "$BACKEND_DIR/.git" ]; then
    git -C "$BACKEND_DIR" fetch --prune origin
    git -C "$BACKEND_DIR" checkout "$BRANCH"
    git -C "$BACKEND_DIR" reset --hard "origin/$BRANCH"
    log "已更新现有仓库"
else
    git clone -b "$BRANCH" "$REPO_URL" "$BACKEND_DIR"
    log "已克隆新仓库"
fi

# ---------- 2. 安装后端依赖 ----------
log "==> [2/5] 安装后端依赖"
if [ ! -d "$BACKEND_DIR/venv" ]; then
    python3 -m venv "$BACKEND_DIR/venv"
fi
"$BACKEND_DIR/venv/bin/pip" install --upgrade pip
"$BACKEND_DIR/venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

# ---------- 3. 打包前端 ----------
log "==> [3/5] 打包前端"
if [ -f "$FRONTEND_DIR/package.json" ]; then
    cd "$FRONTEND_DIR"
    npm ci
    npm run build
    log "前端构建完成 → $FRONTEND_DIR/dist"
else
    log "未找到前端 package.json，跳过前端构建"
fi

# ---------- 4. 重启后端服务 ----------
log "==> [4/5] 重启后端服务 ($SERVICE_NAME)"
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "后端服务已启动"
else
    log "ERROR: 后端服务启动失败"
    sudo journalctl -u "$SERVICE_NAME" -n 30 --no-pager
    exit 1
fi

# ---------- 5. 重载 Nginx ----------
log "==> [5/5] 重载 Nginx"
sudo nginx -t
sudo systemctl reload nginx
log "Nginx 已重载"

# ---------- 完成 ----------
log "=========================================="
log "部署完成！"
log "  后端: http://127.0.0.1:8000"
log "  前端: http://localhost (Nginx 80)"
log "=========================================="
