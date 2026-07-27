# Public Parking Availability

- 负责人：成员 E
- 端口：`8301`
- 类型：重点微服务
- Gateway：`gateway/app/routers/parking_availability.py`
- 前端：`frontend/templates/services/parking-availability.html`

最小流程：

1. 列出停车场与当前余位；
2. 查询单个停车场；
3. 提供可重复演示的余位变化。

最终交付前，本服务必须拥有独立数据、配置、Dockerfile、测试和 API 契约。

```bash
python -m uvicorn services.parking_availability.app.main:app --reload --port 8301
```

验证：<http://localhost:8301/health>
