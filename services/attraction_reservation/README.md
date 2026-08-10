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

当前实现提供可重复的内置景点数据、服务自有 SQLite 预约存储、服务专用
Dockerfile、单元测试和 API 契约。预约在服务重启后仍然保留；数据库地址通过
`ATTRACTION_DATABASE_URL` 配置。

## API

- `GET /api/v1/attractions`
  - 查询参数：`category`、`district`、`indoor`、`min_rating`、`visit_date`、
    `visitor_count`、`recommend`
  - 返回按筛选条件匹配的景点；`recommend=true` 时按推荐分排序。
- `POST /api/v1/reservations`
  - 创建预约，校验景点存在、开放日和当日剩余容量。
- `GET /api/v1/reservations/{reservation_id}`
  - 查询预约详情。
- `PATCH /api/v1/reservations/{reservation_id}/status`
  - 支持 `confirmed -> completed|cancelled` 等合法状态转换，拒绝非法回退。

主要错误码：

- `ATTRACTION_NOT_FOUND`
- `ATTRACTION_CLOSED`
- `CAPACITY_CONFLICT`
- `RESERVATION_NOT_FOUND`
- `INVALID_RESERVATION_STATUS`

```bash
python -m uvicorn services.attraction_reservation.app.main:app --reload --port 8201
```

验证：<http://localhost:8201/health>

默认数据库位于
`services/attraction_reservation/data/attraction_reservation.db`。Compose 使用独立
命名卷挂载 `/data`，不会读取其他服务的数据。

```bash
python -m pytest services/attraction_reservation tests/test_service_scaffolds.py
```
