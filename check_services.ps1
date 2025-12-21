# PowerShell 脚本：检查服务器服务
# 使用方法：在SSH连接到服务器后，将以下命令复制到服务器上执行

Write-Host "=== 正在运行的服务 ===" -ForegroundColor Green
systemctl list-units --type=service --state=running --no-pager

Write-Host "`n=== 所有已启用的服务 ===" -ForegroundColor Green
systemctl list-unit-files --type=service --state=enabled --no-pager

Write-Host "`n=== 按内存使用排序的进程 ===" -ForegroundColor Green
ps aux --sort=-%mem | head -20

Write-Host "`n=== 监听端口的服务 ===" -ForegroundColor Green
netstat -tlnp 2>$null
if ($LASTEXITCODE -ne 0) { ss -tlnp }

Write-Host "`n=== 系统资源使用情况 ===" -ForegroundColor Green
df -h
free -h


