# Public Library Membership and Account

- 负责人：成员 D
- 默认端口：`8202`
- 类型：业务服务（非 Part E 选定的重点微服务）
- Gateway：`gateway/app/routers/library_account.py`
- 前端：`frontend/templates/services/library-account.html`
- 契约：`contracts/schemas/library-account.openapi.yaml`

## 已实现范围

本服务覆盖 Library BSRL 中的主要前置条件、输出和时限：

1. 校验市民身份已验证、条款已接受、必填申请资料完整；
2. 拒绝重复会员，以及已有 `restricted` 或 `suspended` 账户的市民；
3. 确认并模拟收取固定 AUD 5.00 会员费；
4. 创建并立即激活会员账户；
5. 同步签发数字卡，或将实体卡标记为 `ready_for_delivery`；
6. 返回英文或中文会员确认通知；
7. 查询账户、会员卡、缴费与代表性的借阅状态；
8. 更新邮箱、电话、语言偏好和常用分馆。

当前原型会立即完成申请响应和账户激活，因此满足 BSRL 的 10 分钟响应以及 1 天激活
上限。由于不存在延迟激活任务，逾期后的人工补偿流程不会在正常路径触发。

## API

```text
POST  /api/v1/library-memberships
GET   /api/v1/library-accounts/{account_id}
PATCH /api/v1/library-accounts/{account_id}
GET   /health
GET   /api/v1/service-info
```

下游服务返回强类型资源 JSON。浏览器只调用 Gateway 的同名 `/api/v1` 路径；Gateway
负责增加统一的 `success`、`data`、`message` 和 `meta.request_id` 包装。

稳定错误码：

```text
IDENTITY_NOT_VERIFIED
TERMS_NOT_ACCEPTED
ACCOUNT_RESTRICTED
MEMBERSHIP_ALREADY_EXISTS
PAYMENT_REQUIRED
LIBRARY_ACCOUNT_NOT_FOUND
VALIDATION_ERROR
```

## 会费策略

会员费固定为 AUD 5.00，即 API 中的 `amount_minor: 500`。申请人必须确认
`payment_confirmed: true`；服务随即模拟完成支付并生成 `SIM-PAY-...` 付款编号。
原型不接收或保存银行卡、账户等真实支付凭据，也不接入真实支付处理器。

## 本地运行与验证

```bash
python -m uvicorn services.library_account.app.main:app --reload --port 8202
python -m pytest services/library_account/tests
```

健康检查：<http://localhost:8202/health>

用于演示受限账户前置条件的固定市民编号为 `CIT-RESTRICTED`。测试和演示数据均为虚构。

## 当前限制

账户存储为进程内存，服务重启后新建账户会清空。这符合当前业务服务原型的简化部署
范围，但正式生产部署应替换为服务自有数据库，并增加真实身份提供方、通知通道、支付
网关及后台账户限制管理。
