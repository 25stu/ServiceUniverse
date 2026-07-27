# Parking Billing and Payment

- 负责人：成员 E
- 端口：`8302`
- 类型：业务服务
- Gateway：`gateway/app/routers/parking_billing.py`
- 前端：`frontend/templates/services/parking-billing.html`
- 流程分析交接：`analytics/parking_billing/`

最小流程：

1. 创建或查询停车会话；
2. 结束会话并计算费用；
3. 支付符合条件的费用；
4. 生成或模拟成员 C 所需流程事件。

最终日志生成前，成员 C 与 E 共同冻结活动名称和生命周期。

```bash
python -m uvicorn services.parking_billing.app.main:app --reload --port 8302
```

验证：<http://localhost:8302/health>
