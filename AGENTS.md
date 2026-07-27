# ServiceUniverse AI 协作指令

本文件适用于整个仓库。人类成员与 AI 助手遵守同一套集成规则。

## 每次开始任务时

1. 如果存在 `.team-role`，先读取它。
2. 阅读 `docs/TASKS.md`，确认当前角色负责的目录和交接对象。
3. 阅读 `docs/ARCHITECTURE.md`、`API_CONVENTION.md` 和目标服务 README。
4. 修改共享契约、Gateway、共享前端、Compose 或 CI 前，阅读
   `docs/INTEGRATION_PLAYBOOK.md`。
5. 编辑前检查当前分支与工作区状态。

如果 `.team-role` 不存在，不要猜测成员身份。请让用户运行：

```bash
python scripts/select_role.py <A|B|C|D|E|LEADER>
```

## 仓库范围

仓库保存可执行代码、构建配置、API 契约、测试、流程分析脚本、演示数据和技术说明。
最终报告、会议报告、BSRL、BPMN、语义标注、ArchiMate 与 SoaML 在外部
Master Report 工作区维护。

团队技术说明可以使用中文。代码标识、API 路径、JSON 字段、状态、错误码、
交付用代码注释和最终用户界面文字使用英文。

## 架构规则

- 平台共有六项业务服务。
- 三项重点微服务是 `water-billing`、`attraction-reservation` 和
  `parking-availability`。
- 浏览器业务请求只调用 Gateway，不直接调用服务端口。
- 服务不得导入其他服务源码或读取其他服务数据库。
- 服务地址来自环境变量。
- 先修改契约，再修改依赖契约的 Gateway 和前端。
- `contracts/catalog.json` 是 Provider、Service、负责人、端口和重点微服务标记
  的唯一来源。

Compose 将六项服务运行在独立进程中，只是开发集成方式，不代表六项都被认定为
重点微服务。

## 修改边界

- 主要在当前角色负责的目录内工作。
- 修改 `contracts/`、Gateway 公共文件、共享前端、`compose.yaml`、依赖或 CI 时，
  必须在 PR 中说明集成影响，并由 Leader 评审。
- 服务页面只修改
  `frontend/templates/services/<service-slug>.html` 及对应专属资源。
- 不得复制公共导航、页脚、设计变量或错误组件。
- 不得静默重命名 Endpoint、字段、状态、活动名称、端口或 Service slug。
- 工作区已有无关修改时必须保留，不得覆盖或删除。

## 提交评审前验证

```bash
python -m ruff check .
python -m pytest
docker compose config
```

影响集成时还要运行：

```bash
docker compose up --build
python scripts/smoke_test.py
```

## 完成标准

功能的契约、实现、校验、测试、服务 README、Gateway 与前端接入必须保持一致。
PR 中记录执行过的命令和结果。不得提交密钥、`.env`、`.team-role`、数据库、
虚拟环境或自动生成的分析结果。
