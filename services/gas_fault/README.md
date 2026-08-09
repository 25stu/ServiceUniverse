# Gas Fault Reporting and Repair Tracking

- 负责人：成员 B
- 端口：`8102`
- 类型：业务服务
- Gateway：`gateway/app/routers/gas_fault.py`
- 前端：`frontend/templates/services/gas-fault.html`
- API 契约：`contracts/schemas/gas-fault.openapi.yaml`

## 已实现功能

1. 市民提交燃气故障报告并获得唯一 `report_id`；
2. 用户按 `citizen_id` 查看自己的全部报告，并点击查看完整维修时间线；
3. 管理员查看所有报告并按状态机更新维修进度；
4. 用户可以取消自己的活动报告，用户和管理员看到同一条取消时间线事件；
5. 对非法输入、不存在的报告、越权操作和非法状态转换返回稳定英文错误码；
6. 使用 Gas Fault 服务专属 SQLite 数据库存储报告与状态历史。

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/fault-reports` | 创建故障报告 |
| `GET` | `/api/v1/fault-reports` | 用户查询个人列表或管理员查询全部列表 |
| `GET` | `/api/v1/fault-reports/{report_id}` | 查询报告和维修历史 |
| `PATCH` | `/api/v1/fault-reports/{report_id}/status` | 更新维修状态 |
| `POST` | `/api/v1/fault-reports/{report_id}/cancel` | 用户取消自己的活动报告 |

## 角色与权限

课程原型通过请求头表达演示身份，不将其描述为生产级认证：

- 用户请求发送 `X-Citizen-ID`，只能创建、列出和查看属于该编号的报告；
- 管理员请求发送 `X-User-Role: gas_operator`，可以列出和查看全部报告；
- 只有 `gas_operator` 或 `gas_admin` 可以调用状态更新接口；
- 用户可以取消自己的 `reported`、`assigned`、`inspection_in_progress` 或
  `repair_in_progress` 报告；
- `resolved`、`closed` 和已经 `cancelled` 的报告不能取消；
- 缺少身份返回 `401`，越权读取或更新返回 `403`。

真实部署应将这些演示请求头替换为可信登录会话或身份提供商签发的 Token。

创建示例：

```json
{
  "citizen_id": "CITIZEN-001",
  "reporter_name": "Alex Chen",
  "contact_phone": "0400 000 000",
  "address": "12 King Street",
  "description": "A strong gas smell is coming from the kitchen meter.",
  "severity": "high"
}
```

状态更新示例：

```json
{
  "status": "assigned",
  "resource": "Dispatch Officer",
  "note": "Assigned to Gas Repair Team 1."
}
```

## 状态机

主流程：

```text
reported
  -> assigned
  -> inspection_in_progress
  -> repair_in_progress
  -> resolved
  -> closed
```

用户允许从 `reported`、`assigned`、`inspection_in_progress` 或
`repair_in_progress` 转为 `cancelled`。复检未通过时允许从 `resolved` 返回
`repair_in_progress`。服务会以 `409` 和
`INVALID_FAULT_STATUS_TRANSITION` 拒绝其他转换。

状态对应的流程活动名称已经固定为：

| Status | Activity |
|---|---|
| `reported` | `Submit Fault Report` |
| `assigned` | `Assign Repair Team` |
| `inspection_in_progress` | `Inspect Fault` |
| `repair_in_progress` | `Repair Fault` |
| `resolved` | `Resolve Fault` |
| `closed` | `Close Fault Report` |
| `cancelled` | `Cancel Fault Report` |

后续事件日志和 BPMN 必须使用相同活动名称。

## 数据存储

默认数据库位于操作系统临时数据目录中的
`serviceuniverse/gas_fault.sqlite3`。部署时可通过 `GAS_DATABASE_URL` 指定独立的
SQLAlchemy 数据库地址，例如：

```powershell
$env:GAS_DATABASE_URL = "sqlite:///C:/serviceuniverse-data/gas_fault.sqlite3"
```

演示数据不得包含真实个人身份或联系方式。

## 启动与使用

启动服务：

```bash
python -m uvicorn services.gas_fault.app.main:app --reload --port 8102
```

直接查看服务文档：<http://localhost:8102/docs>

通过共享平台使用：

- 身份选择：<http://localhost:8000/services/gas-fault>
- 用户工作台：<http://localhost:8000/services/gas-fault/user>
- 管理员工作台：<http://localhost:8000/services/gas-fault/admin>
- Gateway API：`http://localhost:8080/api/v1/fault-reports`

浏览器只调用 Gateway，不直接调用 `8102`。

## 验证

```bash
python -m ruff check services/gas_fault gateway/app/routers/gas_fault.py
python -m pytest services/gas_fault/tests/test_gas_fault.py
python scripts/smoke_test.py
```

测试覆盖创建、查询、输入校验、资源不存在、合法状态转换和非法转换不修改数据。
