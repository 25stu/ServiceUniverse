# Water Billing and Payment

- 负责人：成员 A
- 端口：`8101`
- 类型：重点微服务
- Gateway：`gateway/app/routers/water_billing.py`
- 前端：`frontend/templates/services/water-billing.html`

最小流程：

1. 查询市民账单；
2. 查看单张账单详情并支付符合条件的未支付账单；
3. 查看已支付账单的收据并下载 PDF；
4. 拒绝重复支付和非法状态转换。

## Local API contract

The service owns its API specification at
`contracts/schemas/water-billing.openapi.yaml`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/bills?citizen_id=CITIZEN-1001` | List a citizen's bills |
| `GET` | `/api/v1/bills/{bill_id}` | Retrieve one bill |
| `GET` | `/api/v1/bills/{bill_id}/receipt` | Retrieve a bill's payment receipt |
| `GET` | `/api/v1/bills/{bill_id}/receipt.pdf` | Download the receipt as a PDF |
| `POST` | `/api/v1/payments` | Pay an unpaid bill |
| `GET` | `/api/v1/payments/{payment_id}` | Retrieve a payment receipt |

The service uses a service-owned SQLite database. By default it is stored at
`services/water_billing/data/water_billing.db`; override it with
`WATER_DATABASE_URL` for local development or tests. The database is seeded with
deterministic demonstration bills on first startup.

`POST /api/v1/payments` accepts a `bill_id` and `payment_method` (`card` or
`bank_transfer`). Only an `unpaid` bill is eligible; a second payment attempt
returns `409 BILL_ALREADY_PAID`.

最终交付前，本服务必须拥有独立数据、配置、Dockerfile、测试和 API 契约。

```bash
python -m uvicorn services.water_billing.app.main:app --reload --port 8101
```

验证：<http://localhost:8101/health>

The service-specific container definition is `services/water_billing/Dockerfile`.
