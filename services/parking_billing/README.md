# Parking Billing and Payment

- 负责人：成员 E
- 端口：`8302`
- 类型：业务服务
- Gateway：`gateway/app/routers/parking_billing.py`
- 前端：`frontend/templates/services/parking-billing.html`
- 契约：`contracts/schemas/parking-billing.openapi.yaml`
- 流程分析交接：`analytics/parking_billing/`

## 状态与业务规则

停车会话从 `active/not_due` 转为 `completed/unpaid`，付款后变为
`completed/paid`。同一车牌不能同时创建两个活动会话；已结束的会话不能重复结束；
活动会话不能付款；已付款会话不能重复付款。

费用按每个开始小时 AUD 4.00（`400` cents）计算，每个会话上限 AUD 40.00。
API 始终使用整数 `amount_minor` 和货币代码 `AUD`。

## API

```text
POST /api/v1/parking-sessions
GET  /api/v1/parking-sessions
GET  /api/v1/parking-sessions/{session_id}
POST /api/v1/parking-sessions/{session_id}/end
GET  /api/v1/parking-sessions/{session_id}/events
POST /api/v1/parking-payments
GET  /api/v1/parking-payments/{payment_id}
```

创建会话的 `started_at` 和结束会话的 `ended_at` 均可省略，此时使用当前 UTC
时间；显式提供时间可用于可重复的计费演示。

数据库地址来自 `PARKING_BILLING_DATABASE_URL`。未配置时写入
`services/parking_billing/data/parking_billing.db`；数据库文件被 Git 忽略。

## 流程事件

运行时为正常路径记录 `Register Parking Entry`、`Close Parking Session`、
`Calculate Parking Fee`、`Initiate Payment` 和 `Confirm Payment`。确定性模拟器还
包含 `Reject Payment` 异常路径；活动词典位于
`analytics/parking_billing/simulation_or_export/activity_dictionary.json`。

```bash
python analytics/parking_billing/simulation_or_export/generate_event_log.py
```

## 本地运行与验证

```bash
python -m uvicorn services.parking_billing.app.main:app --reload --port 8302
python -m pytest services/parking_billing/tests
```

健康检查：<http://localhost:8302/health>；OpenAPI：
<http://localhost:8302/docs>。
