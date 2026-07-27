# Water Billing and Payment

- 负责人：成员 A
- 端口：`8101`
- 类型：重点微服务
- Gateway：`gateway/app/routers/water_billing.py`
- 前端：`frontend/templates/services/water-billing.html`

最小流程：

1. 查询市民账单；
2. 支付符合条件的未支付账单；
3. 查询支付结果或收据；
4. 拒绝重复支付和非法状态转换。

最终交付前，本服务必须拥有独立数据、配置、Dockerfile、测试和 API 契约。

```bash
python -m uvicorn services.water_billing.app.main:app --reload --port 8101
```

验证：<http://localhost:8101/health>
