# GitHub Actions ガイド

[简体中文](GITHUB_ACTIONS.md) | [繁體中文](GITHUB_ACTIONS.zh-Hant.md) | 日本語 | [English](GITHUB_ACTIONS.en.md)

公開 Fork 向けの実行方法です。リポジトリに保存されるのは認証付き暗号化ファイル `state/login.enc` または `state/session.enc` だけです。メール、OTP、promo code、平文セッションは Git、Artifact、Cache に保存されません。

## 事前設定

1. リポジトリを Fork し、Actions を有効にします。
2. **Settings → Actions → General** を開きます。
3. **Workflow permissions** で **Read and write permissions** を選択します。
4. **Settings → Secrets and variables → Actions** を開きます。

## Web UI：メール OTP で初期化

### 1. OTP を送信する

Repository Secret を二つ作成します。

- `POVO_BUNDLE_KEY`：20 文字以上。ランダムな 32 バイト値を推奨し、長期保存します。
- `POVO_LOGIN_EMAIL`：自分の povo ログイン用メールアドレス。

**Actions → Start povo email login → Run workflow** を実行します。成功すると OTP メールが届き、暗号化された `state/login.enc` が作成されます。

### 2. ログインを完了する

必ず最新メールを使い、すぐに次の Repository Secret を作成します。

- `POVO_LOGIN_OTP`：6 桁 OTP。
- `POVO_PROMO_CODE`：スケジュール実行する promo code。

**Actions → Finish povo email login → Run workflow** を開き、タイムゾーン付きの次回実行日時を入力します。

```text
2026-09-06T16:17:00+09:00
```

OTP チャレンジは 15 分間だけ有効です。Start を再実行した場合、以前のメールは使わず、新しいメールだけを使用してください。

成功すると `state/login.enc` が `state/session.enc` に置き換わります。`POVO_LOGIN_EMAIL`、`POVO_LOGIN_OTP`、`POVO_PROMO_CODE` を削除し、`POVO_BUNDLE_KEY` だけを残します。

## GitHub CLI

`gh secret set` は端末上で値を安全に入力できます。Secret をコマンド引数に直接書かないでください。

```bash
openssl rand -base64 32 | gh secret set POVO_BUNDLE_KEY
gh secret set POVO_LOGIN_EMAIL
gh workflow run login-start.yml
```

最新の OTP メールを受信した後：

```bash
gh secret set POVO_LOGIN_OTP
gh secret set POVO_PROMO_CODE
gh workflow run login-finish.yml \
  -f next_due_at='2026-09-06T16:17:00+09:00'
```

成功後：

```bash
gh secret delete POVO_LOGIN_EMAIL
gh secret delete POVO_LOGIN_OTP
gh secret delete POVO_PROMO_CODE
```

## 自動実行

**povo session keeper** は既定で日本時間 `10:17`、`16:17`、`22:17`、翌日 `04:17` に確認します。`next_due_at` を過ぎた場合だけ最大 1 回送信し、更新したセッションを再暗号化します。

GitHub cron は遅延する場合があります。理論上の確認間隔は最大約 6 時間です。結果を確認できない場合は `unknown` へ移行し、自動再試行を停止します。

## 保存されるもの

- `POVO_BUNDLE_KEY`：長期保存する Repository Secret。
- `state/login.enc`：ログインの二段階の間だけ存在する短期チャレンジ暗号文。
- `state/session.enc`：セッション、端末、promo code、スケジュール状態を含む AES-256-GCM 暗号文。

鍵は `POVO_BUNDLE_KEY` から scrypt で導出され、ランダムな salt と nonce を使用します。

## 代替インポートと復旧

メール API が変更された場合は **Import encrypted povo session** で、既存の正当な Android セッションを取り込めます。`POVO_CREDENTIALS_B64`、`POVO_DEVICE_B64`、`POVO_PROMO_CODE` を一時的に設定し、成功後に削除します。

- OTP が無効：最後に Start を実行した後の最新メールか確認します。
- `state/login.enc` が期限切れ：Start を一度だけ再実行します。
- `POVO_BUNDLE_KEY` を紛失：暗号文は復旧できないため、再ログインします。
- 鍵が漏えい：暗号文を削除して Secret をローテーションし、公式アプリでセッションを更新します。
- Bot が push できない：Workflow permissions とブランチ保護を確認します。
- `MULTIPLE_ADDONS_FOUND`：未解決のため、連続再実行しないでください。

認証情報を workflow input、Issue、Pull Request、Actions ログ、公開テストデータへ記載しないでください。
