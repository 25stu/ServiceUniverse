# ServiceUniverse

ServiceUniverse 是一个统一的市民服务平台，将 3 个市政服务提供商的
6 项业务服务放在同一套前端体验和 API Gateway 后面。

当前仓库是团队开发的**可运行初始化骨架**：页面、Gateway、六项服务的
健康检查、Docker Compose、测试和协作边界已经建立；具体业务功能由各负责人
在自己的目录中实现。

## 项目范围

| Provider | Service | Owner | Implementation |
|---|---|---:|---|
| Municipal Utilities Authority | Water Billing and Payment | A | Selected microservice |
| Municipal Utilities Authority | Gas Fault Reporting and Repair Tracking | B | Business service |
| Municipal Culture & Recreation Services | Attraction Recommendation and Reservation | C | Selected microservice |
| Municipal Culture & Recreation Services | Public Library Membership and Account | D | Business service |
| City Parking Management Center | Public Parking Availability | E | Selected microservice |
| City Parking Management Center | Parking Billing and Payment | E | Business service |

项目共有六项业务服务；其中 Water Billing、Attraction Reservation 和
Parking Availability 是 Part E 选定的三项重点微服务。详见
[架构说明](docs/ARCHITECTURE.md)。

## 一条命令启动

需要安装 Git 和 Docker Desktop。

```bash
git clone <repository-url>
cd ServiceUniverse
docker compose up --build
```

启动完成后：

- 主页面：<http://localhost:8000>
- Gateway 文档：<http://localhost:8080/docs>
- 平台健康检查：<http://localhost:8080/api/v1/health>

验证全部入口：

```bash
python scripts/smoke_test.py
```

停止系统：

```bash
docker compose down
```

## 第一次参与开发

每位成员克隆后先设置自己的本地角色；该角色文件不会提交到 Git：

```bash
python scripts/select_role.py A
```

将 `A` 替换为 `B`、`C`、`D`、`E` 或 `LEADER`。随后按顺序阅读：

1. [成员任务与代码边界](docs/TASKS.md)
2. [本地开发环境](docs/DEVELOPMENT.md)
3. [功能接入流程](docs/INTEGRATION_PLAYBOOK.md)
4. [统一 API 规范](API_CONVENTION.md)
5. 自己服务目录中的 `README.md`

AI 助手必须先阅读根目录 [AGENTS.md](AGENTS.md) 和本地 `.team-role`，再修改代码。

## 验证代码

```bash
python -m pip install -r requirements.txt
python -m ruff check .
python -m pytest
docker compose config
```

分析 Gas Fault 或 Parking Billing 流程时，额外安装：

```bash
python -m pip install -r requirements-analytics.txt
```

## 仓库只负责什么

本仓库保存：

- 可执行系统与源代码
- 构建和运行配置
- API 契约与示例
- 自动化测试
- 流程模拟、事件日志生成和流程分析脚本
- 演示数据及技术运行说明

最终报告、会议报告、BSRL、BPMN、语义效果标注、ArchiMate 和 SoaML 在团队的
外部 Master Report 工作区维护，不在此仓库中多人编辑。

## 当前骨架不代表功能已完成

六个服务当前仅提供：

- `GET /health`
- `GET /api/v1/service-info`

这些接口用于证明环境、端口、Gateway 和 Compose 已经接通。业务 Endpoint、
数据库、状态转换、事件日志和具体页面仍由对应负责人完成。
