# Security policy

## Do not report secrets in public issues

Never attach `credentials.xml`, `device.xml`, promo codes, JWTs, dashboard credentials, `state.json`, `runtime.json`, `history.jsonl`, packet captures, or screenshots containing account data.

If a secret is committed, revoke or refresh it first, then remove it from the complete Git history. Deleting only the latest file is not sufficient.

## Supported deployment boundary

- Bind the dashboard to loopback or a trusted private network.
- Use an authenticated HTTPS reverse proxy before any remote exposure.
- Keep `POVO_ENABLE_REDEMPTION=0` during setup and diagnosis.
- Never retry an uncertain submission automatically.

This project does not accept features that bypass TLS pinning, extract another user's credentials, or conceal unauthorized access.
