#!/bin/bash
# 检查服务器运行中的服务并分析

# 定义可能不必要的服务列表
UNNECESSARY_SERVICES=(
    "postfix.service"
    "sendmail.service"
    "dovecot.service"
    "cups.service"
    "cups-browsed.service"
    "gdm.service"
    "lightdm.service"
    "accounts-daemon.service"
    "bluetooth.service"
    "avahi-daemon.service"
    "ModemManager.service"
    "snapd.service"
    "unattended-upgrades.service"
    "NetworkManager-wait-online.service"
)

echo "=========================================="
echo "  服务器服务检查与分析"
echo "=========================================="
echo ""

echo "=== 正在运行的服务 ==="
RUNNING_SERVICES=$(systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print $1}')
echo "$RUNNING_SERVICES"
echo ""

echo "=== 已启用的服务（开机自启动） ==="
ENABLED_SERVICES=$(systemctl list-unit-files --type=service --state=enabled --no-pager --no-legend | awk '{print $1}')
echo "$ENABLED_SERVICES"
echo ""

echo "=== 可能不必要的服务分析 ==="
echo ""
FOUND_UNNECESSARY=0

for service in "${UNNECESSARY_SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "⚠️  运行中: $service"
        echo "   状态: $(systemctl is-active $service)"
        echo "   描述: $(systemctl show -p Description --value $service 2>/dev/null || echo 'N/A')"
        echo "   关闭命令: systemctl stop $service && systemctl disable $service"
        echo ""
        FOUND_UNNECESSARY=1
    elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
        echo "⚠️  已启用（未运行）: $service"
        echo "   状态: $(systemctl is-enabled $service)"
        echo "   描述: $(systemctl show -p Description --value $service 2>/dev/null || echo 'N/A')"
        echo "   禁用命令: systemctl disable $service"
        echo ""
        FOUND_UNNECESSARY=1
    fi
done

if [ $FOUND_UNNECESSARY -eq 0 ]; then
    echo "✅ 未发现常见的不必要服务"
fi

echo ""
echo "=== 监听端口的服务 ==="
if command -v ss &> /dev/null; then
    ss -tlnp | head -20
else
    netstat -tlnp 2>/dev/null | head -20
fi

echo ""
echo "=== 系统资源使用情况 ==="
echo "磁盘使用:"
df -h | grep -E '^/dev|Filesystem'
echo ""
echo "内存使用:"
free -h
echo ""
echo "CPU和内存占用最高的进程:"
ps aux --sort=-%mem | head -10

echo ""
echo "=========================================="
echo "检查完成！"
echo "=========================================="

