# ServiceUniverse 可执行系统要求

本仓库只负责项目构建、源代码、集成、测试、流程分析脚本和演示资源。
正式报告与建模产出在外部工作区维护。

## 平台要求

- 一个统一的市民端前端；
- 一个 API Gateway；
- 三个 Provider 下的六项可执行业务服务；
- Water Billing、Attraction Reservation 和 Parking Availability 三项重点微服务；
- 可重复运行的 Gas Fault 与 Parking Billing 流程分析；
- 确定性的演示数据；
- 单元、契约、集成和端到端验证。

## 每项业务服务都需要

- FastAPI 应用；
- `GET /health`；
- 已发布 API 契约；
- `docs/TASKS.md` 中定义的查询和业务操作；
- Pydantic 请求/响应校验；
- 可重复的 Seed/Demo 数据；
- 明确错误处理；
- 核心业务规则测试；
- 服务自己的运行说明。

## 三项重点微服务额外需要

- 单一且内聚的业务职责；
- 独立配置和数据存储；
- 不导入其他服务源码或访问其数据库；
- 最终交付前拥有自己的 Dockerfile 和依赖边界；
- 能独立构建、启动、停止、测试和演示；
- 健康检查、自动化测试和明确契约。

## 集成要求

- 浏览器业务请求调用 Gateway；
- Gateway 从环境变量读取下游地址；
- 下游调用使用超时与请求标识；
- Gateway 错误使用统一格式；
- 先评审契约修改，再修改依赖实现；
- `docker compose up --build` 启动完整系统；
- `python scripts/smoke_test.py` 验证全部入口。

## Definition of Done

功能只有在以下条件满足时才完成：

1. 契约与示例保持最新；
2. 实现在角色负责目录中；
3. 校验、错误和状态转换已测试；
4. 需要时完成 Gateway 与前端接入；
5. Ruff 和 pytest 通过；
6. Compose 有效且 smoke test 通过；
7. 运行说明和已知限制已更新；
8. 评审人可以从干净 Clone 重现结果。

权威说明见 `docs/ARCHITECTURE.md`、`docs/TASKS.md` 与
`docs/INTEGRATION_PLAYBOOK.md`。
