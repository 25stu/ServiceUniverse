# ServiceUniverse 统一 API 规范

> **文档状态：中文协作过渡版。最终提交前应转换为英文。API 路径、JSON 字段、状态值、错误码和代码标识始终使用英文。**

本规范适用于共享前端、Gateway 和六项服务。任何影响其他成员的接口变更，都必须经过讨论和 Pull Request 评审。

## 1. 基本原则

- 所有外部接口使用 HTTP 和 JSON。
- 前端只与 Gateway 通信。
- Gateway 通过环境变量调用各服务。
- URL 使用面向资源的命名方式，并包含版本号。
- API 字段名统一使用 `snake_case`。
- JSON 键、错误码和接口路径统一使用英文。
- 所有输入必须经过校验。
- 响应中不得暴露堆栈、数据库路径或密钥。
- 服务不得直接访问其他服务的数据库。

## 2. 基础地址与端口

### 公共入口

- Frontend：`http://localhost:8000`
- Gateway：`http://localhost:8080`
- 公共 API 前缀：`/api/v1`

### 六项服务默认端口

- Water Billing：`8101`
- Gas Fault：`8102`
- Attraction Reservation：`8201`
- Library Account：`8202`
- Parking Availability：`8301`
- Parking Billing：`8302`

端口可以通过环境变量调整，但所有成员默认使用以上设置。

## 3. Endpoint 命名

集合使用复数名词：

```text
GET    /api/v1/bills
GET    /api/v1/bills/{bill_id}
POST   /api/v1/payments
GET    /api/v1/fault-reports/{report_id}
POST   /api/v1/fault-reports
GET    /api/v1/attractions
POST   /api/v1/reservations
GET    /api/v1/library-accounts/{account_id}
POST   /api/v1/library-memberships
GET    /api/v1/parking-lots
GET    /api/v1/parking-sessions/{session_id}
POST   /api/v1/parking-payments
```

规则：

- 使用资源名，不使用 `/getBill` 之类的 RPC 命名。
- 路径使用小写字母和连字符。
- 具体资源使用路径参数。
- 筛选、排序和分页使用查询参数。
- 创建资源或发起支付/预约使用 `POST`。
- 局部更新使用 `PATCH`。
- 仅在删除确有业务意义时使用 `DELETE`。

## 4. 请求与响应格式

### 成功响应

Gateway 面向前端的接口统一返回：

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully.",
  "meta": {
    "request_id": "8dba0f0a-5b91-4f8d-9d39-7f6c6a7c6f00"
  }
}
```

规则：

- `success` 固定为 `true`。
- `data` 可以是对象、数组或 `null`。
- `message` 为简短英文提示，必要时可以为 `null`。
- `meta.request_id` 必须存在。
- 分页响应在 `meta` 中加入分页信息。
- `204 No Content` 不返回响应体，因此不使用上述包装。
- `/health` 是基础设施接口，使用第 11 节定义的轻量格式，不使用上述包装。

六项下游服务的成功响应使用各自 OpenAPI 契约中声明的强类型资源 JSON。
Gateway 负责在公共接口边界添加统一包装。不要在服务与 Gateway 两层重复包装。

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "BILL_NOT_FOUND",
    "message": "The requested bill was not found.",
    "details": null
  },
  "meta": {
    "request_id": "8dba0f0a-5b91-4f8d-9d39-7f6c6a7c6f00"
  }
}
```

规则：

- 错误码使用大写 `SNAKE_CASE`。
- 错误消息使用安全、可理解的英文。
- 校验细节可放在 `details` 中。
- 禁止返回堆栈和内部异常信息。

下游服务错误也必须提供稳定的英文错误码和安全消息；Gateway 将其转换为以上公共
格式。FastAPI 默认校验错误不得未经转换直接暴露给公共前端。

## 5. HTTP 状态码

统一使用：

- `200 OK`：读取或更新成功
- `201 Created`：资源创建成功
- `202 Accepted`：已接受异步或较长任务
- `204 No Content`：成功但不返回正文
- `400 Bad Request`：业务请求不合法
- `401 Unauthorized`：需要身份认证
- `403 Forbidden`：没有权限
- `404 Not Found`：资源不存在
- `409 Conflict`：重复、容量冲突或非法状态转换
- `422 Unprocessable Entity`：请求 Schema 校验失败
- `500 Internal Server Error`：未预期的服务错误
- `502 Bad Gateway`：下游服务错误
- `503 Service Unavailable`：服务暂时不可用
- `504 Gateway Timeout`：调用下游服务超时

失败操作不得返回 `200`。

## 6. 标识符

- 面向外部的标识符统一使用字符串。
- 新建资源推荐使用 UUID。
- 示例数据可使用可读前缀，例如 `BILL-0001`。
- 字段名必须体现含义，例如 `bill_id`、`citizen_id`、`reservation_id`。
- 一个响应中存在多个标识符时，不要只使用模糊的 `id`。

## 7. 日期与时间

- 统一使用 ISO 8601。
- API 时间戳必须包含时区。
- 交换和存储优先使用 UTC。
- 示例：`2026-08-05T09:30:00Z`。
- 仅日期使用 `YYYY-MM-DD`。
- 前端可以显示本地时间，但不得改变原始时间含义。

## 8. 金额

- 不使用二进制浮点数直接表示金额。
- API 统一传输最小货币单位整数。

示例：

```json
{
  "amount_minor": 12550,
  "currency": "AUD"
}
```

表示 AUD 125.50。

规则：

- `currency` 使用三字母货币代码。
- 除非团队另行决定，项目默认使用 `AUD`。
- Python 内部使用整数最小单位或 `Decimal`。
- 前端负责格式化展示。

## 9. 布尔值、枚举和状态

- 布尔值使用 JSON 的 `true` 和 `false`。
- 不使用 `"yes"`、`"no"`、`0` 或 `1` 表示布尔值。
- 状态值统一使用小写英文字符串。

示例：

```text
pending
confirmed
in_progress
completed
cancelled
failed
```

每项服务需要明确允许的状态值和合法状态转换。

## 10. 分页、筛选与排序

集合接口建议支持：

```text
?page=1&page_size=20
```

可选规范：

```text
?status=pending
?sort_by=created_at
?sort_order=desc
```

分页元数据：

```json
{
  "page": 1,
  "page_size": 20,
  "total_items": 53,
  "total_pages": 3,
  "request_id": "..."
}
```

默认值：

- `page = 1`
- `page_size = 20`
- `page_size` 最大为 `100`

## 11. 健康检查

每项服务提供：

```text
GET /health
```

响应：

```json
{
  "status": "healthy",
  "service": "water_billing",
  "version": "0.1.0"
}
```

Gateway 提供：

```text
GET /api/v1/health
```

返回 Gateway 以及各下游服务的可用状态。

## 12. 请求标识

- Gateway 在请求没有 `X-Request-ID` 时创建该 Header。
- 同一标识转发给下游服务。
- 服务日志和响应元数据都记录该标识。
- 用于跨前端、Gateway 和服务追踪问题。

## 13. 服务间调用

- 使用 HTTPX，并显式设置超时。
- 服务地址来自环境变量。
- 不得导入其他服务的 Python 模块。
- 不得读取其他服务的数据库文件。
- 只有安全的幂等请求可以进行少量重试。
- 下游错误必须转换为统一错误格式。

## 14. 校验与安全

- 校验长度、格式、必填字段、数值范围和状态转换。
- 对不合法数据明确拒绝，不得静默接受。
- 不提交密码、Token、API Key 或真实个人数据。
- 配置使用环境变量。
- 数据库操作使用 SQLAlchemy 参数化查询。
- 前端安全渲染用户输入。
- 课程原型可以简化认证，但模拟身份必须与真实凭据分离。

## 15. 事件日志规范

Gas Fault 和 Parking Billing 日志至少包含：

```text
case_id
activity
timestamp
resource
lifecycle
outcome
```

推荐增加：

```text
service
citizen_id
cost_minor
duration_seconds
status
```

规则：

- 一行对应一个事件。
- `case_id` 表示一个流程实例。
- `activity` 必须与最终 BPMN 活动词典一致。
- `timestamp` 使用 ISO 8601。
- 同一 case 的事件时间顺序必须合理。
- 模拟日志必须在代码和报告中明确标注为 simulated。
- C 开始流程分析前，C 和 E 必须冻结 Parking Billing 活动名称。

## 16. API 变更流程

以下变化属于 Breaking Change：

- 删除或重命名 Endpoint
- 删除或重命名字段
- 修改字段类型
- 修改状态值含义
- 修改必填/可选规则
- 修改前端依赖的错误码

发生 Breaking Change 时：

1. 创建 Issue，说明原因和受影响成员。
2. 更新本规范或对应契约示例。
3. 获得 Gateway/前端负责人和受影响服务负责人的确认。
4. 在同一个或协调好的 Pull Request 中同步更新代码和测试。
5. 合并后在团队沟通渠道通知所有人。

禁止直接在 `develop` 中进行未通知的接口变更。
