# Translation Agent 部署脚本 (PowerShell版本)
# 使用方法: .\deploy.ps1 [服务器IP] [部署目录]

param(
    [string]$ServerIP = "47.109.82.94",
    [string]$DeployDir = "/opt/translation-agent",
    [string]$RemoteUser = "root"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Translation Agent 部署脚本" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "服务器: $ServerIP"
Write-Host "部署目录: $DeployDir"
Write-Host ""

# 检查本地是否有代码
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "错误: 请在项目根目录执行此脚本" -ForegroundColor Red
    exit 1
}

Write-Host "步骤 1: 检查服务器连接..." -ForegroundColor Yellow
$testConnection = ssh -o ConnectTimeout=5 "$RemoteUser@$ServerIP" "echo '连接成功'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 无法连接到服务器 $ServerIP" -ForegroundColor Red
    exit 1
}

Write-Host "步骤 2: 在服务器上创建部署目录..." -ForegroundColor Yellow
ssh "$RemoteUser@$ServerIP" "mkdir -p $DeployDir"

Write-Host "步骤 3: 传输项目文件到服务器..." -ForegroundColor Yellow
# 使用 scp 传输文件（需要先打包或使用 rsync）
# 注意: Windows 上可能需要安装 rsync 或使用其他工具
Write-Host "提示: 如果 rsync 不可用，请手动使用 scp 或 git clone" -ForegroundColor Cyan

Write-Host "步骤 4-7: 在服务器上执行部署..." -ForegroundColor Yellow
$deployScript = @"
cd $DeployDir

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo '安装 Python3...'
    apt-get update
    apt-get install -y python3 python3-pip
fi

# 检查 Poetry
if ! command -v poetry &> /dev/null; then
    echo '安装 Poetry...'
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="\$HOME/.local/bin:\$PATH"
fi

# 安装依赖
export PATH="\$HOME/.local/bin:\$PATH"
poetry install --with app --no-interaction

# 创建 .env 文件（如果不存在）
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
# OpenAI API Key (必需)
OPENAI_API_KEY="your-openai-api-key-here"
ENVEOF
fi

# 创建 systemd 服务
cat > /etc/systemd/system/translation-agent.service << 'SERVICEEOF'
[Unit]
Description=Translation Agent WebUI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DeployDir
Environment="PATH=$DeployDir/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/bash -c 'cd $DeployDir && export PATH="\$HOME/.local/bin:\$PATH" && poetry run python app/app.py'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
echo "部署完成！"
"@

ssh "$RemoteUser@$ServerIP" $deployScript

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host "1. 编辑服务器上的 .env 文件，添加你的 API Key"
Write-Host "2. 启动服务: systemctl start translation-agent"
Write-Host "3. 设置开机自启: systemctl enable translation-agent"
Write-Host "4. WebUI 将在 http://$ServerIP:7860 运行"


