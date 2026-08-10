# Public Parking Availability

- 负责人：成员 E
- 端口：`8301`
- 类型：重点微服务
- Gateway：`gateway/app/routers/parking_availability.py`
- 前端：`frontend/templates/services/parking-availability.html`
- 契约：`contracts/schemas/parking-availability.openapi.yaml`

## 功能

- 列出三个确定性 Seed 停车场及当前余位；
- 按 `lot_id` 查询单个停车场；
- 将余位更新为明确数值，便于重复演示；
- 拒绝负数、超出总容量的余位以及未知停车场；
- 使用服务独立的 SQLite 数据库和 Dockerfile。

状态 `available`、`limited` 和 `full` 根据当前余位派生。余位为 0 时是 `full`；
余位不超过容量的 10%（最低阈值为 5）时是 `limited`。

## API

```text
GET   /api/v1/parking-lots
GET   /api/v1/parking-lots/{lot_id}
PATCH /api/v1/parking-lots/{lot_id}/availability
```

更新示例：

```json
{"available_spaces": 21}
```

数据库地址来自 `PARKING_AVAILABILITY_DATABASE_URL`。未配置时写入
`services/parking_availability/data/parking_availability.db`；数据库文件被 Git
忽略。

## 本地运行与验证

```bash
python -m uvicorn services.parking_availability.app.main:app --reload --port 8301
python -m pytest services/parking_availability/tests
```

独立镜像：

```bash
docker build -f services/parking_availability/Dockerfile -t parking-availability .
docker run --rm -p 8301:8301 parking-availability
```

健康检查：<http://localhost:8301/health>；OpenAPI：
<http://localhost:8301/docs>。
