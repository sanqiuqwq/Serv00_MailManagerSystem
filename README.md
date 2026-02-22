# Serv00邮箱注册管理系统

Demo：https://reg.nekoqwq.com/

基于 serv00 的邮箱注册和管理系统，包含用户端和管理后台。

**PS：程序AI写的，有点bug见谅(**

## 安装步骤

1. 克隆项目并安装依赖（建议从release下载）：
```bash
pip install -r requirements.txt
```
国内镜像加速：
https://pan.nekoqwq.com/s/Bnhx

2. 配置环境变量：
```bash
cp .env.example .env
```
编辑 `.env` 文件，填入您的配置信息。

4. 初始化数据库：
```bash
python init_db.py
```
这将创建所有数据表并初始化默认数据（包括Owner账户、前缀黑名单、邮箱后缀白名单等）。

3. 运行项目：
```bash
python app.py
```
## 更新

1.备份旧版数据库(一定要备份！！！！！！！！)

2.停止运行项目

3.删除全部文件，仅保留旧版目录中.env文件

4.到release中下载新版源码

5.解压到旧版目录

6.根据提示更新.env配置文件

7.更新数据库（建议每次更新都使用）：
```bash
python update_db.py
```

8.运行新项目

## 默认Owner账户

- 用户名: admin
- 密码: admin123（可在 .env 中配置）
- 邮箱: admin@example.com（建议更改真实邮箱，便于后期找回密码）

**注意：首次运行后请立即修改Owner密码！**

## 功能特性

### 用户端
- 用户注册/登录（用户名+密码）
- NodeLoc OAuth 登录（需先绑定）
- Telegram 登录（需先绑定）
- 邮箱验证
- reCAPTCHA v2 人机验证
- 创建邮箱（前缀+域名选择）
- 重置邮箱密码
- 查看已注册的邮箱
- 邮箱转移所有权（PUSH功能）
- 卡密兑换（增加邮箱配额）
- 工单系统
- 修改密码
- 忘记密码
- TG交流群入口
- 绑定/解绑 NodeLoc 账户
- 绑定/解绑 Telegram 账户

### 管理后台
- 用户管理（查看/搜索/修改用户组/单独设置用户邮箱配额）
- 卡密管理（创建/删除/查看使用次数/清理过期卡密）
- 工单管理（查看/回复/关闭/重新打开工单）
- 域名管理（添加/启用/禁用/删除）
- 邮箱管理（禁用/启用/删除）
- 公告管理（发布/显示/隐藏/删除）
- 前缀黑名单管理（禁止特定邮箱前缀注册）
- 邮箱后缀限制（只允许特定后缀注册账户）
- 站点设置（编辑站点名称/描述/域名/购买卡密链接/TG群链接/默认邮箱配额/前缀长度限制/邮件服务器配置）
- 邮件服务器配置（SMTP/IMAP/POP3/Webmail）
- 关于页面编辑
- 用户协议编辑
- 
### 权限控制
- **Owner（所有者）**：可访问所有后台功能
- **Pro用户**：享受更少的邮箱前缀限制和更多的邮箱配额
- **普通用户**：基础功能

### 邮箱配额说明
- 新注册用户的邮箱上限根据后台设置的默认值确定
- 已注册用户的邮箱上限不受默认值变化影响
- 可在用户管理中单独修改每个用户的邮箱上限
- 卡密兑换增加额外邮箱配额

## 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| SECRET_KEY | Flask密钥 | random-secret-key |
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 3306 |
| DB_USER | 数据库用户名 | root |
| DB_PASSWORD | 数据库密码 | password |
| DB_NAME | 数据库名称 | email_registration |
| SERV00_PANEL | serv00面板域名 | panel15.serv00.com |
| SERV00_USERNAME | serv00用户名 | your_username |
| SERV00_PASSWORD | serv00密码 | your_password |
| RECAPTCHA_SITE_KEY | reCAPTCHA Site Key | your_site_key |
| RECAPTCHA_SECRET_KEY | reCAPTCHA Secret Key | your_secret_key |
| RECAPTCHA_USE_CN | 是否使用国内reCAPTCHA镜像 | true |
| RECAPTCHA_ENABLED | 是否启用reCAPTCHA验证 | true |
| NODELOC_ENABLED | 是否启用NodeLoc OAuth登录 | false |
| NODELOC_URL | NodeLoc OAuth地址 | https://www.nodeloc.com |
| NODELOC_CLIENT_ID | NodeLoc OAuth Client ID | your-client-id |
| NODELOC_CLIENT_SECRET | NodeLoc OAuth Client Secret | your-client-secret |
| NODELOC_REDIRECT_URI | NodeLoc OAuth回调地址 | http://localhost:5000/auth/nodeloc/callback |
| TELEGRAM_ENABLED | 是否启用Telegram登录 | false |
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | your-bot-token |
| TELEGRAM_BOT_USERNAME | Telegram Bot用户名 | your-bot-username |
| SMTP_SERVER | SMTP服务器 | smtp.example.com |
| SMTP_PORT | SMTP端口 | 587 |
| SMTP_USERNAME | SMTP用户名 | noreply@example.com |
| SMTP_PASSWORD | SMTP密码 | smtp_password |
| ADMIN_USERNAME | Owner用户名 | admin |
| ADMIN_EMAIL | Owner邮箱 | admin@example.com |
| ADMIN_PASSWORD | Owner密码 | admin123 |

## 项目结构

```
Email_Distribution/
├── app.py                      # 主应用文件
├── requirements.txt            # 依赖项
├── .env.example               # 环境变量示例
├── README.md                  # 项目说明
├── templates/                 # 模板文件
│   ├── base.html              # 基础模板
│   ├── index.html             # 首页
│   ├── register.html          # 注册页
│   ├── login.html             # 登录页
│   ├── forgot_password.html   # 忘记密码页
│   ├── reset_password.html    # 重置密码页
│   ├── change_password.html   # 修改密码页
│   ├── redeem_code.html       # 卡密兑换页
│   ├── create_ticket.html     # 创建工单页
│   ├── tickets.html           # 工单列表页
│   ├── view_ticket.html       # 查看工单页
│   ├── dashboard.html         # 用户中心
│   ├── about.html             # 关于页面
│   ├── agreement.html         # 用户协议
│   └── admin/                 # 管理后台模板
│       ├── base.html          # 后台基础模板
│       ├── dashboard.html     # 后台概览
│       ├── users.html         # 用户管理
│       ├── domains.html       # 域名管理
│       ├── emails.html        # 邮箱管理
│       ├── codes.html         # 卡密管理
│       ├── create_code.html   # 创建卡密
│       ├── show_codes.html    # 显示卡密列表
│       ├── tickets.html       # 工单管理
│       ├── announcements.html # 公告管理
│       ├── prefix_blacklist.html # 前缀黑名单管理
│       ├── email_suffixes.html # 邮箱后缀限制
│       ├── about.html         # 关于页面编辑
│       ├── agreement.html     # 用户协议编辑
│       └── settings.html      # 站点设置
└── static/                    # 静态文件（如需要）
```

## NodeLoc OAuth 使用说明

### 配置步骤

1. 在 NodeLoc 创建 OAuth 应用：
   访问：https://www.nodeloc.com/oauth-provider/applications

2. 记录以下信息：
   - Client ID
   - Client Secret
   - Redirect URI（回调地址：https://你的域名/auth/nodeloc/callback）

3. 在 `.env` 中配置：
```env
NODELOC_ENABLED=true
NODELOC_CLIENT_ID=你的Client ID
NODELOC_CLIENT_SECRET=你的Client Secret
NODELOC_REDIRECT_URI=https://你的域名/auth/nodeloc/callback
```

## Telegram 登录使用说明

### 配置步骤

1. 创建 Telegram Bot：
   - 访问 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot` 命令创建机器人
   - 记录 Bot Token 和 Bot 用户名

2. 设置网站域名：
   - 向 @BotFather 发送 `/setdomain` 命令
   - 输入你的网站域名（例如：`yourdomain.com`）
   - 注意：域名不需要加协议头（http/https）

3. 在 `.env` 中配置：
```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=你的Bot Token
TELEGRAM_BOT_USERNAME=你的Bot用户名（例如：your_bot）
```

## Google OAuth 2.0 使用说明

### 配置步骤

1. 创建 Google Cloud 项目：
   - 访问：https://console.cloud.google.com/
   - 点击"创建项目"

2. 启用 OAuth 同意屏幕：
   - 进入"API 和服务" → "OAuth 同意屏幕"
   - 选择"外部"，点击"创建"
   - 填写应用信息（应用名称、用户支持邮箱等）
   - 添加授权范围（至少包含：email、profile、openid）
   - 添加测试用户（如果是测试状态）

3. 创建 OAuth 客户端凭据：
   - 进入"API 和服务" → "凭据"
   - 点击"创建凭据" → "OAuth 客户端 ID"
   - 选择应用类型："Web 应用"
   - 填写授权 JavaScript 来源（例如：`https://yourdomain.com`）
   - 填写授权重定向 URI（例如：`https://yourdomain.com/auth/google/callback`）
   - 点击"创建"，记录 Client ID 和 Client Secret

4. 在 `.env` 中配置：
```env
GOOGLE_ENABLED=true
GOOGLE_CLIENT_ID=你的Client ID
GOOGLE_CLIENT_SECRET=你的Client Secret
GOOGLE_REDIRECT_URI=https://你的域名/auth/google/callback
```


## 许可证

GNU General Public License v2.0 (GPL v2)
