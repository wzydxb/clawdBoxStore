---
name: network-drive
description: 网盘（Samba）环境初始化。检测挂载状态，引导完成 Samba 部署（SSD 分区→安装→配置→用户→软链），或仅挂载已有共享。
version: 1.0.0
---

# 网盘环境初始化

## 第一步：诊断当前状态

```bash
grep -A5 "知识库" ~/.hermes/USER.md 2>/dev/null || echo "未配置"
ls /Volumes/uploads 2>/dev/null && echo "MOUNTED" || echo "NOT_MOUNTED"
```

| 状态 | 行动 |
|------|------|
| `MOUNTED` | 网盘就绪，返回 system-setup 继续其他检查 |
| `NOT_MOUNTED` + 盒子已有 Samba | → [挂载分支](#mount-only) |
| `NOT_MOUNTED` + 盒子无 Samba | → [完整部署分支](#full-deploy) |

---

## 完整部署分支（盒子首次初始化）{#full-deploy}

> 适用：盒子还没装 Samba，SSD 未格式化

**先问用户确认盒子 IP：**「你的盒子 IP 是多少？（比如 192.168.10.30）」

### 阶段 1：SSD 准备

```bash
parted -s /dev/nvme0n1 mklabel gpt
parted -s /dev/nvme0n1 mkpart primary 0% 100%
sleep 3
mkfs.xfs -f -L box-data /dev/nvme0n1p1
mkdir -p /data
mount -o noatime,nodiratime /dev/nvme0n1p1 /data
df -hT /data
UUID=$(blkid -s UUID -o value /dev/nvme0n1p1)
echo "UUID=$UUID /data xfs noatime,nodiratime 0 0" >> /etc/fstab
```

⚠️ **RK3588S**：分区后不要调 `partprobe`，等内核自动识别。

### 阶段 2：安装 Samba

```bash
apt-get update
apt-get install -y samba samba-common-bin smbclient
```

### 阶段 3：写入配置

```bash
cat > /etc/samba/smb.conf << 'EOF'
[global]
   workgroup = WORKGROUP
   server string = ClawdBox %h
   server role = standalone server
   map to guest = Bad User
   guest account = nobody
   log file = /var/log/samba/log.%m
   max log size = 1000
   logging = file
   server min protocol = SMB2
   unix charset = UTF-8
   veto files = /._*/.DS_Store/
   delete veto files = yes

[uploads]
   comment = ClawdBox Uploads
   path = /data/uploads
   browseable = yes
   writable = yes
   guest ok = yes
   valid users = clawdbox
   create mask = 0666
   directory mask = 0777
   force user = clawdbox
   force group = clawdbox
EOF

testparm -s
```

⚠️ smb.conf 不能有行尾注释，注释必须单独成行。

### 阶段 4：创建用户

```bash
useradd -M -s /usr/sbin/nologin clawdbox
PASSWD="claw1234"
(echo "$PASSWD"; echo "$PASSWD") | smbpasswd -a -s clawdbox
smbpasswd -e clawdbox
mkdir -p /data/uploads
chown -R clawdbox:clawdbox /data/uploads
chmod 0777 /data/uploads
```

### 阶段 5：启动服务

```bash
systemctl enable smbd nmbd
systemctl start smbd nmbd
systemctl is-active smbd nmbd
smbclient -L //127.0.0.1 -N
echo "test $(date)" > /tmp/t.txt
smbclient //127.0.0.1/uploads -U clawdbox%claw1234 -c "put /tmp/t.txt; ls"
```

⚠️ 看 `smbd` / `nmbd`，不是 `samba.service`（那是 AD-DC 模式）。

### 阶段 6：建 Workspace 软链

```bash
# CLI 模式（10.30）
mkdir -p /root/workspace
ln -sfn /data/uploads /root/workspace/uploads

# WebUI 模式（10.151）
ln -sfn /data/uploads /root/.hermes/webui/workspace/uploads
mkdir -p /root/workspace
ln -sfn /data/uploads /root/workspace/uploads
```

---

## 挂载分支（仅客户端挂载）{#mount-only}

**macOS（Finder）**：`⌘K` → `smb://192.168.10.30/uploads` → 用户名 `clawdbox` 密码 `claw1234`

**macOS（命令行）**
```bash
mkdir -p ~/mnt/uploads
mount_smbfs //clawdbox:claw1234@192.168.10.30/uploads ~/mnt/uploads
```

**Windows**
```
net use Z: \\192.168.10.30\uploads /user:clawdbox claw1234 /persistent:yes
```

**Linux**
```bash
apt-get install -y cifs-utils
mkdir -p /mnt/uploads
mount.cifs //192.168.10.30/uploads /mnt/uploads \
  -o username=clawdbox,password=claw1234,uid=root,iocharset=utf8
```

---

## 完成后：更新 USER.md

```yaml
知识库:
  - 名称: uploads
    挂载路径: /Volumes/uploads
    盒子IP: 192.168.10.30
    SMB路径: smb://192.168.10.30/uploads
```

---

## 快速排查

| 现象 | 原因 | 解决 |
|------|------|------|
| macOS「无法连接服务器」 | 445 端口未监听 / smbd 没起 | `ss -tlnp \| grep 445`，`systemctl status smbd` |
| 挂载后容量显示 1.82 GB | 客户端缓存旧值 | macOS 弹出重连；Windows `net use Z: /delete` 后重挂 |
| 账号密码反复弹 | 用户未 enable | `smbpasswd -e clawdbox` |
| 写文件报权限 | 目录权限错 | `chown clawdbox:clawdbox /data/uploads && chmod 0777 /data/uploads` |
| 中文文件名乱码 | charset 未设 | smb.conf 加 `unix charset = UTF-8` |
| 龙虾说没有这个文件 | 软链没建对 | `ls -la /root/workspace/uploads` 确认是 symlink |
| Mac 出现大量 `._foo` 文件 | macOS 元数据 | smb.conf 加 `veto files` + `delete veto files = yes` |
| RK3588S `partprobe` 后重启 | watchdog 敏感 | 分区后不要调 partprobe |
