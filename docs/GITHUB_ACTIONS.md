# GitHub Actions 使用说明

简体中文 | [繁體中文](GITHUB_ACTIONS.zh-Hant.md) | [日本語](GITHUB_ACTIONS.ja.md) | [English](GITHUB_ACTIONS.en.md)

GitHub Actions 模式适合公开 Fork。仓库只保存认证加密的 `state/login.enc` 或 `state/session.enc`；邮箱、验证码、兑换码和明文会话不会提交到 Git、Artifact 或 Cache。

## 前置设置

1. Fork 仓库并启用 Actions。
2. 打开 **Settings → Actions → General**。
3. 在 **Workflow permissions** 选择 **Read and write permissions** 并保存。
4. 打开 **Settings → Secrets and variables → Actions**。

## 网页方式：邮箱验证码初始化

### 第一步：发送验证码

建立两个 Repository Secret：

- `POVO_BUNDLE_KEY`：至少 20 字符；建议使用随机 32 字节值，长期保留。
- `POVO_LOGIN_EMAIL`：本人 povo 账户的登录邮箱。

进入 **Actions → Start povo email login → Run workflow**。成功后会收到邮件，仓库中会出现加密的 `state/login.enc`。

### 第二步：完成登录

只使用最新一封邮件，并立即建立：

- `POVO_LOGIN_OTP`：6 位验证码。
- `POVO_PROMO_CODE`：需要按计划使用的 promo code。

进入 **Actions → Finish povo email login → Run workflow**，输入带时区的下一次执行时间，例如：

```text
2026-09-06T16:17:00+09:00
```

验证码挑战有效期为 15 分钟。不要再次运行发码工作流后继续使用旧邮件；新发码会建立新的挑战。

成功后，`state/login.enc` 会被 `state/session.enc` 替换。删除以下一次性 Secret：

- `POVO_LOGIN_EMAIL`
- `POVO_LOGIN_OTP`
- `POVO_PROMO_CODE`

只保留 `POVO_BUNDLE_KEY`。

若初始化账户还需要立即兑换一次，请手动运行 **povo session keeper**，并明确勾选 `redeem_now`。这是单次确认开关；定时触发时始终为关闭状态。兑换确认成功后，下一次时间会设置为成功时刻加 7 天 1 分钟。

## GitHub CLI 方式

以下命令会让 `gh secret set` 在终端中安全提示输入值，不要把 Secret 直接写在命令参数里：

```bash
openssl rand -base64 32 | gh secret set POVO_BUNDLE_KEY
gh secret set POVO_LOGIN_EMAIL
gh workflow run login-start.yml
```

收到最新邮件后：

```bash
gh secret set POVO_LOGIN_OTP
gh secret set POVO_PROMO_CODE
gh workflow run login-finish.yml \
  -f next_due_at='2026-09-06T16:17:00+09:00'
```

确认登录工作流成功后：

```bash
gh secret delete POVO_LOGIN_EMAIL
gh secret delete POVO_LOGIN_OTP
gh secret delete POVO_PROMO_CODE
```

可以用 `gh run list` 和 `gh run watch` 查看状态；日志只应显示脱敏结果。

## 初始化完成后如何运行

**povo session keeper** 默认在 UTC `01:17`、`07:17`、`13:17`、`19:17` 检查，即日本时间 `10:17`、`16:17`、`22:17`、次日 `04:17`。每次运行会：

1. 在临时 runner 中解密会话；
2. 刷新会话；
3. 仅当 `next_due_at` 已到且未暂停时最多提交一次；
4. 把更新后的会话和状态重新加密并提交；
5. 随 runner 销毁明文。

GitHub cron 可能排队或延迟。当前设计的理论检查间隔最长约 6 小时，不适用于要求秒级准时的任务。若结果无法确认，状态会变为 `unknown` 并阻止自动重试。

## 仓库中保存什么

- `POVO_BUNDLE_KEY`：Repository Secret，长期解密钥匙。
- `state/login.enc`：仅在两阶段登录之间存在的短期挑战密文。
- `state/session.enc`：包含最小必要会话、设备、promo code 和调度状态的 AES-256-GCM 密文。

加密密钥通过 scrypt 从 `POVO_BUNDLE_KEY` 派生，并使用随机 salt、nonce。知道公开密文但不知道钥匙，不能直接还原内容。

## 备用：导入现有 Android 会话

如果邮箱登录接口因 App 更新失效，可以改用 **Import encrypted povo session**。需要临时建立：

- `POVO_CREDENTIALS_B64`
- `POVO_DEVICE_B64`
- `POVO_PROMO_CODE`
- 已有的 `POVO_BUNDLE_KEY`

```bash
base64 < credentials.xml | tr -d '\n' | gh secret set POVO_CREDENTIALS_B64
base64 < device.xml | tr -d '\n' | gh secret set POVO_DEVICE_B64
gh secret set POVO_PROMO_CODE
gh workflow run import-session.yml \
  -f next_due_at='2026-09-06T16:17:00+09:00'
```

成功后删除三个一次性导入 Secret。

## 故障恢复

- OTP 无效：确认使用的是最后一次发码后的最新邮件；重新开始时只运行一次发码工作流。
- `state/login.enc` 过期：重新运行 **Start povo email login**，旧验证码作废。
- 丢失 `POVO_BUNDLE_KEY`：无法恢复密文，只能重新登录或重新导入。
- 钥匙泄露：删除密文、轮换 Secret，并通过官方 App 更新账户会话。
- Bot 无法 push：检查 Workflow permissions 和默认分支保护规则。
- `MULTIPLE_ADDONS_FOUND`：当前未解决，不要连续重跑。

不要在 workflow input、Issue、Pull Request、Actions 日志或公开测试数据中提交认证材料。
