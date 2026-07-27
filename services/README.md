# 业务服务实现说明

每个子目录由对应成员负责，并使用统一内部结构：

```text
app/main.py       FastAPI 启动与路由注册
app/api/          HTTP 路由
app/schemas/      Pydantic API 模型
app/models/       持久化模型
app/repositories/ 数据访问
app/services/     业务规则
tests/            服务内部测试
data/             可重复的 Seed/Demo 数据
```

六个目录代表六项业务服务。只有 Water Billing、Attraction Reservation 和
Parking Availability 是三项重点微服务，详见 `docs/ARCHITECTURE.md`。

兄弟服务目录之间禁止互相导入。
