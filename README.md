# hermes-opc · 数字分身部署包

## 是什么

这是一个**开箱即用的数字分身配置包**。把它部署到一台盒子上，盒子就变成某个人的专属数字分身，通过微信与他对话。

**一台盒子 = 一个人的分身。**

小程序是管理端，负责把这套东西自动部署到新盒子上。部署完成后，用户第一次发微信消息，分身自动引导完成初始化，无需人工干预。

---

## 部署后盒子上发生了什么

```
盒子
├── Hermes Agent（已安装）
├── ~/.hermes/
│   ├── SOUL.md        ← 分身人格（初始阶段是引导流程）
│   ├── AGENTS.md      ← 路由逻辑
│   ├── USER.md        ← 用户数据（初始为空，引导完成后自动填充）
│   ├── .env           ← 微信账号 + API Key
│   ├── skills/        ← 技能包（报告/画布/复盘等）
│   └── config.yaml    ← LLM 配置
└── hermes-gateway（systemd 常驻，监听微信消息）
```

用户发微信 → gateway 收到 → 触发 SOUL.md 里的引导流程 → 5步初始化 → 写入 USER.md → 分身就绪。

---

## 小程序部署一台新盒子的步骤

以下是小程序需要自动执行的完整流程，按顺序：

### 第一步：推送配置文件

把本仓库的文件推送到盒子的 `~/.hermes/`：

```bash
# 核心配置
scp SOUL.md      root@<盒子IP>:/root/.hermes/SOUL.md
scp AGENTS.md    root@<盒子IP>:/root/.hermes/AGENTS.md
scp USER.md      root@<盒子IP>:/root/.hermes/USER.md
scp config/hermes.yaml root@<盒子IP>:/root/.hermes/config.yaml

# Skills（画布渲染 + 报告 + 其他基础技能）
scp -r skills/base/canvas/      root@<盒子IP>:/root/.hermes/skills/canvas/
scp -r skills/base/reporting/   root@<盒子IP>:/root/.hermes/skills/reporting/
scp -r skills/base/output-format/ root@<盒子IP>:/root/.hermes/skills/output-format/
scp -r skills/base/retrospective/ root@<盒子IP>:/root/.hermes/skills/retrospective/
```

或者直接用脚本：

```bash
./scripts/deploy.sh root@<盒子IP>
```

### 第二步：写入微信账号配置

每台盒子绑定一个微信账号（ilinkai 平台分配），写入 `.env`：

```bash
ssh root@<盒子IP> "cat > /root/.hermes/.env << 'EOF'
HERMES_API_KEY=<clawdbox_api_key>
WEIXIN_ACCOUNT_ID=<微信账号ID>
WEIXIN_TOKEN=<微信token>
WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com
WEIXIN_DM_POLICY=open
WEIXIN_ALLOW_ALL_USERS=true
GATEWAY_ALLOW_ALL_USERS=true
PYTHONHTTPSVERIFY=0
EOF"
```

### 第三步：安装画布渲染依赖

```bash
ssh root@<盒子IP> "pip3 install playwright --break-system-packages -q && python3 -m playwright install chromium"
```

> 如果盒子是标准镜像且已预装，这步可以跳过。建议把 playwright 打进盒子镜像，省去每次安装。

### 第四步：启动微信网关

```bash
ssh root@<盒子IP> "hermes gateway install && hermes gateway start"
```

验证：

```bash
ssh root@<盒子IP> "hermes gateway status"
# 应显示 active (running)
```

### 第五步：验证

```bash
ssh root@<盒子IP> "hermes status"
```

完成。用户发第一条微信消息，分身自动开始引导。

---

## 用户初始化流程（自动，无需干预）

部署完成后，用户第一次发消息触发：

```
第1步  问职业（产品经理 / 财务 / HR / 运营 / CEO…）
第2步  问行业（分两条消息：行业 + 核心业务）
第3步  3道选择题（每道单独发，等回答再发下一道）
第4步  匹配认知原型 → 展示推荐 → 用户确认
第5步  写入 USER.md + 生成正式人格 + 创建定时提醒
```

完成后 USER.md 里 `Onboarding Status` 变为 `role_assigned`，后续对话进入正常工作模式。

---

## 盒子前置要求

| 项目 | 要求 |
|------|------|
| 系统 | Linux（Debian/Ubuntu） |
| Hermes | v0.8.0+，已安装（`hermes --version` 可用） |
| Python | 3.9+ |
| 网络 | 能访问 `ilinkai.weixin.qq.com` 和 `llm.clawdbox.cn` |
| 微信账号 | ilinkai 平台分配的账号 + token |
| API Key | clawdbox 平台的 `HERMES_API_KEY` |

---

## 目录结构

```
hermes-opc/
├── SOUL.md                  # 分身人格模板（含完整初始化引导流程）
├── AGENTS.md                # 路由逻辑
├── USER.md                  # 用户数据模板（空白，引导后自动填充）
├── config/
│   └── hermes.yaml          # LLM + MCP 配置
├── scripts/
│   ├── deploy.sh            # 一键部署脚本
│   └── sync-skills.sh       # 更新 Skills（不覆盖用户数据）
└── skills/
    └── base/
        ├── canvas/           # 画布渲染
        │   ├── render.py
        │   └── templates/    # 10个输出模板
        ├── reporting/        # 报告生成技能
        ├── output-format/    # 微信渠道输出规范
        └── retrospective/    # 复盘技能
```

---

## 更新已部署的盒子

修改了 Skills 或配置后，推送到指定盒子（不覆盖用户已积累的数据）：

```bash
./scripts/sync-skills.sh root@<盒子IP>
```

批量更新所有盒子：

```bash
for ip in <IP1> <IP2> <IP3>; do
  ./scripts/sync-skills.sh root@$ip
done
```

---

## 常见问题

**Q: 图片渲染失败**
```bash
ssh root@<盒子IP> "python3 -c 'from playwright.sync_api import sync_playwright; print(\"OK\")'"
# 失败则重装：
ssh root@<盒子IP> "pip3 install playwright --break-system-packages && python3 -m playwright install chromium"
```

**Q: 微信网关没在跑**
```bash
ssh root@<盒子IP> "hermes gateway restart && hermes gateway status"
```

**Q: 想让某个用户重新初始化**
```bash
# 把 USER.md 恢复为空白模板（Onboarding Status: pending）
scp USER.md root@<盒子IP>:/root/.hermes/USER.md
# 用户下次发消息自动重新引导
```

**Q: 定时报告时区不对**
```bash
ssh root@<盒子IP> "timedatectl set-timezone Asia/Shanghai"
```
