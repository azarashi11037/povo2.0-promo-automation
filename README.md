# povo promo automation (experimental)

一个非官方、自托管的 povo promo code 定时执行器，包含单次提交 Worker 和局域网管理面板。

> [!WARNING]
> 本项目使用未公开、可能随 App 更新而变化的后端接口，不受 povo/KDDI 支持或认可。请只操作你本人有权管理的账户，并自行确认服务条款。项目不提供绕过证书固定、Root、越权读取 App 数据或获取他人会话的方式。

## 当前状态

- 会话刷新和只读认证检查可用。
- 每个到期事件最多提交一次；结果不明确时进入 `unknown` 并停止自动重试。
- 响应日志采用字段白名单，不记录兑换码、会话令牌、设备 ID 或用户 ID。
- 已知限制：账户同时存在多个 add-on 时，服务端可能返回 `MULTIPLE_ADDONS_FOUND`。该场景尚未解决，不能视为生产级工具。
- 默认 `POVO_ENABLE_REDEMPTION=0`，不会提交兑换请求。

## 安全设计

- Dashboard 默认只绑定 `127.0.0.1`，不要直接暴露到公网。
- 容器使用只读根文件系统、`cap_drop: ALL`、`no-new-privileges` 和 128 MiB 内存限制。
- 敏感文件只保存在挂载的 `data/`，并被 `.gitignore` 与 `.dockerignore` 排除。
- Dashboard 密码只保存 PBKDF2 哈希。
- 没有“立即兑换”网页按钮；修改时间不会立刻触发提交。

## 准备

需要 Docker Engine 和 Docker Compose。项目不会替你提取账户材料；你必须已经通过合法、获授权的方式持有与自己账户匹配的：

- `credentials.xml`
- `device.xml`
- 可重复使用的 promo code

不要把这些文件发送给他人或提交到 Git。

```bash
cp .env.example .env
python3 tools/init_data.py --data-dir ./data
cp /your/authorized/path/credentials.xml ./data/credentials.xml
cp /your/authorized/path/device.xml ./data/device.xml
chmod 600 ./data/*
docker compose up -d --build
```

打开 `http://127.0.0.1:17820/`，先执行“认证检查”。Linux 主机如使用不同 UID，需要确保容器 UID 1000 可写 `data/`。

## 启用提交

只有在只读认证检查正常、调度时间正确且你理解风险后，才把 `.env` 改为：

```dotenv
POVO_ENABLE_REDEMPTION=1
```

随后执行：

```bash
docker compose up -d
```

失败后不要反复手动重试。先检查 `state.json`、Dashboard 和脱敏历史记录。

## 管理

```bash
docker compose ps
docker compose logs --tail=100 povo-worker
docker compose logs --tail=100 povo-web
docker compose restart povo-worker
docker compose down
```

升级或修改前，先备份整个 `data/`。不要把 `data/`、`.env`、XML、兑换码或日志加入 Git。

## 测试

```bash
python3 -m unittest discover -s tests -v
docker compose config
docker compose build
```

## 免责声明

本项目仅用于研究和个人账户自动化。接口、字段和业务规则随时可能改变；错误使用可能导致会话失效、重复提交或账户限制。使用者承担全部风险。
