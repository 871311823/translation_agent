#!/bin/bash
# Translation Agent 部署脚本
# 使用方法: ./deploy.sh [服务器IP] [部署目录]

set -e

SERVER_IP="${1:-47.109.82.94}"
DEPLOY_DIR="${2:-/opt/translation-agent}"
REMOTE_USER="root"

echo "=========================================="
echo "  Translation Agent 部署脚本"
echo "=========================================="
echo "服务器: $SERVER_IP"
echo "部署目录: $DEPLOY_DIR"
echo ""

# 检查本地是否有代码
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 请在项目根目录执行此脚本"
    exit 1
fi

echo "步骤 1: 检查服务器连接..."
ssh -o ConnectTimeout=5 $REMOTE_USER@$SERVER_IP "echo '连接成功'" || {
    echo "错误: 无法连接到服务器 $SERVER_IP"
    exit 1
}

echo "步骤 2: 在服务器上创建部署目录..."
ssh $REMOTE_USER@$SERVER_IP "mkdir -p $DEPLOY_DIR"

echo "步骤 3: 传输项目文件到服务器..."
# 使用 rsync 传输文件（排除不必要的文件）
rsync -avz --progress \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='outputs' \
    --exclude='check_services.*' \
    --exclude='disable_services.sh' \
    --exclude='服务*.md' \
    ./ $REMOTE_USER@$SERVER_IP:$DEPLOY_DIR/

echo "步骤 4: 检查服务器上的 Python 和 Poetry..."
ssh $REMOTE_USER@$SERVER_IP "bash -s" << 'EOF'
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo "安装 Python3..."
        apt-get update
        apt-get install -y python3 python3-pip
    fi
    
    # 检查 Poetry
    if ! command -v poetry &> /dev/null; then
        echo "安装 Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
EOF

echo "步骤 5: 在服务器上安装依赖..."
ssh $REMOTE_USER@$SERVER_IP "bash -s" << EOF
    cd $DEPLOY_DIR
    export PATH="\$HOME/.local/bin:\$PATH"
    
    # 安装依赖（包括 WebUI）
    poetry install --with app --no-interaction
    
    echo "依赖安装完成"
EOF

echo "步骤 6: 创建 .env 文件模板（如果不存在）..."
ssh $REMOTE_USER@$SERVER_IP "bash -s" << EOF
    cd $DEPLOY_DIR
    if [ ! -f .env ]; then
        cat > .env << 'ENVEOF'
# OpenAI API Key (必需)
OPENAI_API_KEY="your-openai-api-key-here"

# 可选: 其他 API Keys
# GROQ_API_KEY="your-groq-api-key"
# TOGETHER_API_KEY="your-together-api-key"
ENVEOF
        echo "已创建 .env 文件模板，请编辑 $DEPLOY_DIR/.env 添加你的 API Key"
    else
        echo ".env 文件已存在，跳过创建"
    fi
EOF

echo "步骤 7: 创建 systemd 服务文件..."
ssh $REMOTE_USER@$SERVER_IP "bash -s" << EOF
    cat > /etc/systemd/system/translation-agent.service << 'SERVICEEOF'
[Unit]
Description=Translation Agent WebUI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/bash -c 'cd $DEPLOY_DIR && export PATH="\$HOME/.local/bin:\$PATH" && poetry run python app/app.py'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

    systemctl daemon-reload
    echo "systemd 服务文件已创建"
EOF

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 编辑服务器上的 .env 文件，添加你的 API Key:"
echo "   ssh $REMOTE_USER@$SERVER_IP 'nano $DEPLOY_DIR/.env'"
echo ""
echo "2. 启动服务:"
echo "   ssh $REMOTE_USER@$SERVER_IP 'systemctl start translation-agent'"
echo ""
echo "3. 设置开机自启:"
echo "   ssh $REMOTE_USER@$SERVER_IP 'systemctl enable translation-agent'"
echo ""
echo "4. 查看服务状态:"
echo "   ssh $REMOTE_USER@$SERVER_IP 'systemctl status translation-agent'"
echo ""
echo "5. 查看日志:"
echo "   ssh $REMOTE_USER@$SERVER_IP 'journalctl -u translation-agent -f'"
echo ""
echo "WebUI 将在 http://$SERVER_IP:7860 运行"
echo "（如果无法访问，请检查防火墙设置）"


