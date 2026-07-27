# 功能接入流程

以下流程用于将个人服务功能安全接入共享系统。

## 1. 确认角色和负责目录

```bash
python scripts/select_role.py B
git switch develop
git pull origin develop
git switch -c feature/gas-submit-fault
```

修改前阅读 `.team-role`、`docs/TASKS.md`、`AGENTS.md` 和目标服务 README。

## 2. 先定义契约

前端或 Gateway 开发前，先确定：

- URI 与 HTTP Method；
- 请求和响应字段；
- 必填与可选字段；
- 状态及合法状态转换；
- 成功状态码；
- 错误码；
- 至少一个成功示例和失败示例。

将 OpenAPI/JSON Schema 和示例放在 `contracts/`。影响其他成员时，先创建 Issue
并请求 Leader 评审。

## 3. 在服务内部实现

```text
app/api/           HTTP 路由
app/schemas/       Pydantic 请求/响应模型
app/models/        持久化模型
app/repositories/  数据访问
app/services/      业务规则和流程
```

不要把业务规则写在 Gateway 或 Jinja 模板中，不得导入其他服务代码或数据库。

## 4. 增加服务测试

至少测试：

- 正常业务路径；
- 非法输入；
- 资源不存在；
- 非法状态转换或冲突；
- 一项服务特有的边界情况。

开发时可先运行服务自己的测试，提交前运行全部测试。

## 5. 接入 Gateway

只编辑自己负责的 `gateway/app/routers/` 模块。Gateway 应当：

- 从配置读取下游地址；
- 转发 `X-Request-ID`；
- 设置明确超时；
- 将下游错误转换为统一格式；
- 不重复实现业务校验。

除非需要修改共享启动行为，否则不要修改 `gateway/app/main.py`。

## 6. 接入共享前端

编辑：

```text
frontend/templates/services/<service-slug>.html
```

只在必要时增加服务专属 CSS/JavaScript。复用公共导航、文字、颜色、焦点状态、
表单与错误组件。浏览器业务请求必须通过 Gateway。

## 7. 验证集成

```bash
python -m ruff check .
python -m pytest
docker compose config
docker compose up --build
python scripts/smoke_test.py
```

还要从共享主页手动完成受影响的市民流程。

## 8. 创建 Pull Request

PR 中填写：

- 当前角色和服务；
- Issue/契约；
- 修改的 Endpoint 或 Schema；
- 测试命令与结果；
- 页面截图；
- 已知限制；
- 请求的评审人。

Leader 在契约负责人和交叉评审通过后合并到 `develop`。

## Breaking Change

不要只合并破坏性修改的一部分。契约、服务、Gateway、前端、测试、示例和受影响的
流程活动名称必须协调提交，或者提供明确的兼容过渡方案。
