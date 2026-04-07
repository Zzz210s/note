# 3X-UI安装与使用

---

## 安装3X-UI

前往 [GitHub 3X-UI 项目](https://github.com/MHSanaei/3x-ui)获取最新的安装命令<sub>注:在`sudo模式`下</sub>

`bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)`

## 安装过程

全部默认即可

## 记录面板登录信息

```textile
Username（用户名）: admin
Password（密码）: admin
Access URL（面板地址）: http://你的服务器IP:端口号/路径
```

## 打开端口号

打开面板端口和节点端口

- 开放单个端口号
  
  `ufw allow 端口号`

- 开放连续端口号
  
  `ufw allow 起始端口号:末尾端口号/tcp`

## 搭建节点

### 搭建Vless+TCP+Reality节点
