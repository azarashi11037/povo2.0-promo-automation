# GitHub Actions 模式

这个模式适合公开 Fork：标准 GitHub-hosted runner 执行时才会临时解密会话，仓库中只保存 `state/session.enc` 密文。

## 它保存什么

- Repository Secret `POVO_BUNDLE_KEY`：唯一长期保留的解密口令。
- `state/session.enc`：AES-256-GCM 密文，包含最小必要的 `credentials.xml`、`device.xml`、promo code 和调度状态。
- runner 临时目录：任务结束后由 GitHub 销毁；工作流不会上传明文 Artifact 或 Cache。

会话包采用 scrypt 派生密钥，并使用随机 salt、nonce 和认证加密。知道公开密文但不知道 `POVO_BUNDLE_KEY`，不能直接还原其中内容。

## 推荐：邮箱验证码初始化

这条路径不需要 Android 虚拟机，也不需要导出 App 文件。邮箱和验证码都使用 Repository Secret，不能作为普通 `workflow_dispatch` 输入。

先在 Fork 的 Settings → Secrets and variables → Actions 中建立：

- `POVO_BUNDLE_KEY`：至少 20 字符，建议随机 32 字节；长期保留。
- `POVO_LOGIN_EMAIL`：本人的 povo 登录邮箱。

然后在 Actions 页面运行 **Start povo email login**。它会发送一封验证码邮件，并且只把短期登录挑战的 AES-256-GCM 密文提交为 `state/login.enc`。

收到最新验证码后，立即再建立：

- `POVO_LOGIN_OTP`：最新邮件中的 6 位验证码。
- `POVO_PROMO_CODE`：需要按计划使用的 promo code。

在 15 分钟内运行 **Finish povo email login**，输入下一次执行时间，例如：

```text
2026-09-06T16:17:00+09:00
```

成功后，工作流会用 `state/session.enc` 替换 `state/login.enc`。随后删除三个一次性 Secret，只保留 `POVO_BUNDLE_KEY`：

```bash
gh secret delete POVO_LOGIN_EMAIL
gh secret delete POVO_LOGIN_OTP
gh secret delete POVO_PROMO_CODE
```

如果验证码失效或登录失败，工作流不会自动重发；重新运行 **Start povo email login** 才会发送新验证码。务必使用最新一封邮件，旧挑战与新验证码不能混用。

## 备用：导入已有 Android 会话

先 Fork 仓库，并在 Fork 的 Settings → Secrets and variables → Actions 中建立：

- `POVO_BUNDLE_KEY`：至少 20 字符，建议随机 32 字节；长期保留。
- `POVO_CREDENTIALS_B64`：本人获授权的 `credentials.xml` 的单行标准 Base64。
- `POVO_DEVICE_B64`：与会话匹配的 `device.xml` 的单行标准 Base64。
- `POVO_PROMO_CODE`：promo code 原文。

安装 [GitHub CLI](https://cli.github.com/) 后，可以避免把内容写进命令历史：

```bash
openssl rand -base64 32 | gh secret set POVO_BUNDLE_KEY
base64 < credentials.xml | tr -d '\n' | gh secret set POVO_CREDENTIALS_B64
base64 < device.xml | tr -d '\n' | gh secret set POVO_DEVICE_B64
gh secret set POVO_PROMO_CODE
```

在 Actions 页面手动运行 **Import encrypted povo session**，输入带时区的下一次执行时间，例如：

```text
2026-09-06T16:17:00+09:00
```

Fork 后还需要在 Actions 页面启用工作流，并在 Settings → Actions → General 允许工作流读写仓库内容，否则密文无法回写。

确认工作流成功并且仓库出现 `state/session.enc` 后，删除三个一次性导入 Secret，只保留解密钥匙：

```bash
gh secret delete POVO_CREDENTIALS_B64
gh secret delete POVO_DEVICE_B64
gh secret delete POVO_PROMO_CODE
```

## 定时执行

**povo session keeper** 默认每天检查四次。每次会：

1. 在临时 runner 中解密会话；
2. 刷新会话；
3. 仅当 `next_due_at` 已到且调度未暂停时，最多提交一次；
4. 把更新后的会话和状态重新加密后提交；
5. 删除 runner 时一并销毁明文。

GitHub 的 cron 不是实时调度器，高峰期可能延迟。当前四次检查意味着到期后的理论检查间隔最长约 6 小时；不要把它用于要求秒级准时的任务。

如果一次提交的结果无法确认，状态会变成 `unknown`，后续自动重试会被阻止。请先查脱敏的 Actions 日志，不要连续重跑。

## 邮箱与验证码的边界

两阶段工作流只调用当前 App 使用的邮箱登录链路，不绕过验证码、证书校验或访问控制。普通工作流输入会显示在运行记录中，所以邮箱与验证码必须放在 Repository Secrets；成功后应立即删除一次性 Secret。接口属于未公开实现，App 更新后可能变化。

## 恢复与轮换

- 丢失 `POVO_BUNDLE_KEY`：密文无法恢复，只能用原始授权会话重新导入。
- 解密钥匙泄露：删除 `state/session.enc`，轮换 Secret，并重新导入；同时视会话为已泄露并在官方 App 侧重新登录。
- Fork 开启分支保护后，bot 可能无法提交密文。需要允许 Actions 写入默认分支，或自行改为专用状态分支。
- 不要在 Pull Request 工作流中使用这些 Secrets，也不要把任何明文会话文件提交到 Git。
