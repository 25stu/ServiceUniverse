# Attraction Recommendation and Reservation

- 负责人：成员 C
- 端口：`8201`
- 类型：重点微服务
- Gateway：`gateway/app/routers/attraction_reservation.py`
- 前端：`frontend/templates/services/attraction-reservation.html`

最小流程：

1. 按有意义的条件列出或推荐景点；
2. 创建和查询预约；
3. 拒绝容量冲突和非法预约状态转换。

最终交付前，本服务必须拥有独立数据、配置、Dockerfile、测试和 API 契约。

```bash
python -m uvicorn services.attraction_reservation.app.main:app --reload --port 8201
```

验证：<http://localhost:8201/health>
