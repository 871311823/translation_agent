#!/bin/bash
# 关闭不必要的服务脚本
# 使用前请仔细阅读每个服务的说明

echo "=========================================="
echo "  关闭不必要的服务"
echo "=========================================="
echo ""

# 定义要关闭的服务（可以根据需要注释掉）
SERVICES_TO_DISABLE=(
    "accounts-daemon.service:用户账户服务(桌面环境用，服务器不需要)"
    "unattended-upgrades.service:自动更新服务(如果手动管理更新可关闭)"
    "systemd-networkd-wait-online.service:网络等待服务(网络稳定后可禁用)"
)

echo "将要关闭的服务："
echo ""
for service_info in "${SERVICES_TO_DISABLE[@]}"; do
    service_name=$(echo $service_info | cut -d: -f1)
    service_desc=$(echo $service_info | cut -d: -f2)
    status=$(systemctl is-active $service_name 2>/dev/null || echo "inactive")
    enabled=$(systemctl is-enabled $service_name 2>/dev/null || echo "disabled")
    echo "  - $service_name"
    echo "    描述: $service_desc"
    echo "    状态: $status (enabled: $enabled)"
    echo ""
done

read -p "确认关闭这些服务? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "已取消操作"
    exit 0
fi

echo ""
echo "开始关闭服务..."
echo ""

for service_info in "${SERVICES_TO_DISABLE[@]}"; do
    service_name=$(echo $service_info | cut -d: -f1)
    
    # 停止服务（如果正在运行）
    if systemctl is-active --quiet $service_name 2>/dev/null; then
        echo "停止 $service_name..."
        systemctl stop $service_name
        if [ $? -eq 0 ]; then
            echo "  ✓ 已停止"
        else
            echo "  ✗ 停止失败"
        fi
    fi
    
    # 禁用服务
    if systemctl is-enabled --quiet $service_name 2>/dev/null; then
        echo "禁用 $service_name..."
        systemctl disable $service_name
        if [ $? -eq 0 ]; then
            echo "  ✓ 已禁用"
        else
            echo "  ✗ 禁用失败"
        fi
    else
        echo "$service_name 已经是禁用状态"
    fi
    echo ""
done

echo "=========================================="
echo "操作完成！"
echo "=========================================="
echo ""
echo "验证结果："
for service_info in "${SERVICES_TO_DISABLE[@]}"; do
    service_name=$(echo $service_info | cut -d: -f1)
    status=$(systemctl is-active $service_name 2>/dev/null || echo "inactive")
    enabled=$(systemctl is-enabled $service_name 2>/dev/null || echo "disabled")
    echo "  $service_name: $status (enabled: $enabled)"
done


