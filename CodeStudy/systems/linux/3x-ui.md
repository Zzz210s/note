# 3x-ui
---
### 🚀 优化 Ubuntu 系统文件句柄限制

# 将以下配置追加到 /etc/security/limits.conf
sudo bash -c 'cat >> /etc/security/limits.conf << EOF
* soft nofile 512000
* hard nofile 512000
* soft nproc 512000
* hard nproc 512000
root soft nofile 512000
root hard nofile 512000
EOF'

# 开启内核转发（确保流量中转顺畅）
sudo bash -c 'cat >> /etc/sysctl.conf << EOF
net.ipv4.ip_forward = 1
net.ipv4.tcp_fastopen = 3
EOF'
sudo sysctl -p