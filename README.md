# 邮箱注册系统

基于 serv00 的邮箱注册和管理系统，包含用户端和管理后台。

## 功能特性

### 用户端
- 用户注册/登录（用户名+密码）
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

### 管理后台
- 用户管理（查看/搜索/修改用户组/单独设置用户邮箱配额）
- 卡密管理（创建/删除/查看使用次数/清理过期卡密）
- 工单管理（查看/回复/关闭/重新打开工单）
- 域名管理（添加/启用/禁用/删除）
- 邮箱管理（禁用/启用/删除）
- 公告管理（发布/显示/隐藏/删除）
- 前缀黑名单管理（禁止特定邮箱前缀注册）
- 邮箱后缀限制（只允许特定后缀注册账户）
- 站点设置（编辑站点名称/描述/域名/购买卡密链接/TG群链接/默认邮箱配额/前缀长度限制）
- 关于页面编辑
- 用户协议编辑

### 权限控制
- **Owner（所有者）**：可访问所有后台功能
- **Pro用户**：享受更少的邮箱前缀限制和更多的邮箱配额
- **普通用户**：基础功能

### 邮箱配额说明
- 新注册用户的邮箱上限根据后台设置的默认值确定
- 已注册用户的邮箱上限不受默认值变化影响
- 可在用户管理中单独修改每个用户的邮箱上限
- 卡密兑换增加额外邮箱配额

## 安装步骤

1. 克隆项目并安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
```
编辑 `.env` 文件，填入您的配置信息。

3. 创建 MySQL 数据库：
```sql
CREATE DATABASE email_registration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. 运行项目：
```bash
python app.py
```

## 默认Owner账户

- 用户名: admin
- 密码: admin123（可在 .env 中配置）
- 邮箱: admin@example.com

**注意：首次运行后请立即修改Owner密码！**

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
| SMTP_SERVER | SMTP服务器 | smtp.example.com |
| SMTP_PORT | SMTP端口 | 587 |
| SMTP_USERNAME | SMTP用户名 | noreply@example.com |
| SMTP_PASSWORD | SMTP密码 | smtp_password |
| ADMIN_USERNAME | Owner用户名 | admin |
| ADMIN_EMAIL | Owner邮箱 | admin@example.com |
| ADMIN_PASSWORD | Owner密码 | admin123 |

## serv00 API 接口说明

### 1. 登录页面获取
- 地址: `https://{panel}/login/?next=/mail/add`
- 方法: GET

### 2. 登录提交
- 地址: `https://{panel}/login/`
- 方法: POST

### 3. 邮箱创建页面获取
- 地址: `https://{panel}/mail/add`
- 方法: GET

### 4. 邮箱创建提交
- 地址: `https://{panel}/mail/add`
- 方法: POST

### 5. 邮箱列表页面
- 地址: `https://{panel}/mail`
- 方法: GET

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

## 数据库模型

### User（用户表）
- id: 主键
- username: 用户名
- email: 邮箱
- password_hash: 密码哈希
- is_admin: 是否为管理员（保留字段）
- is_verified: 是否已验证邮箱
- uid: 用户唯一ID
- role: 用户角色（user/pro/owner）
- max_emails: 最大邮箱数量
- extra_emails: 额外邮箱数量（卡密兑换）
- pro_expires_at: Pro到期时间
- is_permanent: 是否永久Pro
- temp_extra_emails: 临时额外邮箱
- temp_expires_at: 临时额外邮箱到期时间
- created_at: 创建时间

### RegisteredEmail（已注册邮箱表）
- id: 主键
- email_address: 邮箱地址
- email_password: 邮箱密码
- prefix: 邮箱前缀
- domain_id: 域名ID
- user_id: 用户ID
- is_disabled: 是否禁用
- created_at: 创建时间

### Domain（域名表）
- id: 主键
- domain: 域名
- is_active: 是否激活
- created_at: 创建时间

### RedemptionCode（卡密表）
- id: 主键
- code: 卡密
- extra_emails: 增加的邮箱数量
- duration_days: 有效期天数
- is_permanent: 是否永久
- is_used: 是否已使用
- max_uses: 最大使用次数
- used_count: 已使用次数
- expires_at: 过期时间
- user_id: 最后使用的用户ID
- used_at: 使用时间
- created_at: 创建时间

### Ticket（工单表）
- id: 主键
- title: 工单标题
- user_id: 用户ID
- status: 状态（open/closed）
- created_at: 创建时间
- closed_at: 关闭时间

### TicketReply（工单回复表）
- id: 主键
- ticket_id: 工单ID
- user_id: 用户ID
- content: 回复内容
- is_admin: 是否为管理员回复
- created_at: 创建时间

### Announcement（公告表）
- id: 主键
- title: 公告标题
- content: 公告内容
- is_active: 是否显示
- created_at: 创建时间

### SiteSettings（站点设置表）
- id: 主键
- site_name: 站点名称
- site_description: 站点描述
- site_url: 网站域名
- purchase_code_url: 购买卡密链接
- tg_group_url: TG交流群链接
- default_user_max_emails: 普通用户默认邮箱数量
- default_pro_max_emails: Pro用户默认邮箱数量
- min_user_prefix_length: 普通用户前缀最小长度
- min_pro_prefix_length: Pro用户前缀最小长度

### PrefixBlacklist（前缀黑名单表）
- id: 主键
- prefix: 禁止的前缀
- created_at: 创建时间

### AllowedEmailSuffix（允许邮箱后缀表）
- id: 主键
- suffix: 允许的后缀
- created_at: 创建时间

### AboutPage（关于页面）
- id: 主键
- content: 页面内容

### UserAgreement（用户协议）
- id: 主键
- content: 协议内容

### VerificationToken（验证令牌表）
- id: 主键
- token: 令牌
- user_id: 用户ID
- token_type: 令牌类型
- expires_at: 过期时间
- is_used: 是否已使用
- created_at: 创建时间

## 安全提示

1. 请妥善保管.env文件，不要提交到版本控制
2. 首次运行后立即修改Owner密码
3. 配置强SECRET_KEY
4. 定期备份数据库
5. 及时清理过期和已使用的卡密
6. 监控异常登录和操作

## 许可证

GNU General Public License v2.0 (GPL v2)
