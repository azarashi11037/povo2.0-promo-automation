# GitHub Actions guide

[简体中文](GITHUB_ACTIONS.md) | [繁體中文](GITHUB_ACTIONS.zh-Hant.md) | [日本語](GITHUB_ACTIONS.ja.md) | English

This mode is suitable for a public fork. The repository stores only authenticated ciphertext in `state/login.enc` or `state/session.enc`. Email addresses, OTPs, promo codes, and plaintext sessions are never committed to Git or uploaded as artifacts or caches.

## Prerequisites

1. Fork the repository and enable Actions.
2. Open **Settings → Actions → General**.
3. Under **Workflow permissions**, select **Read and write permissions**.
4. Open **Settings → Secrets and variables → Actions**.

## Web UI: initialize with email OTP

### 1. Send the OTP

Create two repository secrets:

- `POVO_BUNDLE_KEY`: at least 20 characters; a random 32-byte value is recommended and should be retained.
- `POVO_LOGIN_EMAIL`: your povo login email address.

Run **Actions → Start povo email login → Run workflow**. A successful run sends the email and commits encrypted `state/login.enc`.

### 2. Finish login

Use only the newest email and immediately create:

- `POVO_LOGIN_OTP`: the six-digit OTP.
- `POVO_PROMO_CODE`: the promo code to use on schedule.

Run **Actions → Finish povo email login → Run workflow** and enter the next execution time with a timezone:

```text
2026-09-06T16:17:00+09:00
```

The OTP challenge is valid for 15 minutes. If Start is run again, the old email must not be reused because a new challenge has been created.

On success, `state/login.enc` is replaced by `state/session.enc`. Delete `POVO_LOGIN_EMAIL`, `POVO_LOGIN_OTP`, and `POVO_PROMO_CODE`; keep only `POVO_BUNDLE_KEY`.

If the initialized account must redeem once immediately, manually run **povo session keeper** and explicitly enable `redeem_now`. This is a one-run confirmation switch and is always off for scheduled triggers. After a confirmed success, the next due time is set to 7 days and 1 minute after that success.

## GitHub CLI

`gh secret set` securely prompts for a value. Do not put secrets directly in command arguments.

```bash
openssl rand -base64 32 | gh secret set POVO_BUNDLE_KEY
gh secret set POVO_LOGIN_EMAIL
gh workflow run login-start.yml
```

After receiving the newest email:

```bash
gh secret set POVO_LOGIN_OTP
gh secret set POVO_PROMO_CODE
gh workflow run login-finish.yml \
  -f next_due_at='2026-09-06T16:17:00+09:00'
```

After a successful run:

```bash
gh secret delete POVO_LOGIN_EMAIL
gh secret delete POVO_LOGIN_OTP
gh secret delete POVO_PROMO_CODE
```

Use `gh run list` and `gh run watch` to inspect run status. Logs should contain only sanitized results.

## Scheduled operation

By default, **povo session keeper** checks at `01:17`, `07:17`, `13:17`, and `19:17` UTC, corresponding to `10:17`, `16:17`, `22:17`, and `04:17` the next day in Japan. Each run:

1. decrypts the session inside an ephemeral runner;
2. refreshes the session;
3. submits at most once only when `next_due_at` has passed and the schedule is not paused;
4. re-encrypts and commits updated state; and
5. destroys plaintext with the runner.

GitHub cron may queue or run late. The theoretical maximum check interval is about six hours, so this is not appropriate for second-level timing. An uncertain result changes the state to `unknown` and blocks automatic retries.

## Stored data

- `POVO_BUNDLE_KEY`: the long-lived repository secret.
- `state/login.enc`: short-lived encrypted challenge between the two login stages.
- `state/session.enc`: AES-256-GCM ciphertext containing the minimum session, device, promo-code, and schedule state.

The encryption key is derived from `POVO_BUNDLE_KEY` using scrypt with random salt and nonce.

## Fallback import and recovery

If the email API changes, **Import encrypted povo session** can import an existing authorized Android session. Temporarily set `POVO_CREDENTIALS_B64`, `POVO_DEVICE_B64`, and `POVO_PROMO_CODE`, then delete them after success.

- Invalid OTP: confirm it came from the newest email after the last Start run.
- Expired `state/login.enc`: run Start once again; the old OTP is invalid.
- Lost `POVO_BUNDLE_KEY`: the ciphertext cannot be recovered; log in again.
- Exposed key: delete ciphertext, rotate the secret, and update the account session in the official app.
- Bot cannot push: check workflow permissions and branch protection.
- `MULTIPLE_ADDONS_FOUND`: unresolved; do not rerun repeatedly.

Never place authentication material in workflow inputs, issues, pull requests, Actions logs, or public test data.
