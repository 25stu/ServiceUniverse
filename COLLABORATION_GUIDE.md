# ServiceUniverse Git collaboration guide

本说明面向第一次使用 Git/GitHub 协作的成员，也面向成员使用的 AI 助手。
先理解规则，再复制命令。

## 1. 三条最重要的规则

1. 不直接向 `main` 或 `develop` 提交。
2. 每项功能使用自己的分支和 Pull Request。
3. 修改共享 API 前先修改契约并通知受影响成员。

AI 助手开始工作前必须阅读 `AGENTS.md`、`.team-role`、`docs/TASKS.md`
和目标服务的 README。

## 2. 第一次克隆

```bash
git clone <repository-url>
cd ServiceUniverse
python scripts/select_role.py A
docker compose up --build
python scripts/smoke_test.py
```

将 `A` 替换为自己的角色。只有当初始 smoke test 成功后，才开始编写功能；
否则应先向 Leader 报告环境问题。

## 3. 分支含义

- `main`：经过验证、可用于阶段发布或最终提交的版本；
- `develop`：团队当前可运行的集成版本；
- `feature/<short-name>`：新功能；
- `fix/<short-name>`：问题修复；
- `docs/<short-name>`：仅技术文档修改。

推荐命名：

```text
feature/water-payment
feature/gas-event-log
feature/attraction-reservation
fix/gateway-timeout
```

## 4. 每次开始任务

```bash
git switch develop
git pull origin develop
git switch -c feature/task-name
```

确认自己所在分支：

```bash
git branch --show-current
git status
```

不要在存在不理解的本地修改时继续执行合并、切换或删除操作；先询问修改来源。

## 5. 保存修改

先查看：

```bash
git status
git diff
```

再添加明确文件并提交：

```bash
git add services/water_billing contracts/schemas
git commit -m "feat(water): add bill payment workflow"
```

不要习惯性使用 `git add .`，否则容易提交 `.env`、数据库、截图或无关修改。

Commit 格式：

```text
type(scope): concise English description
```

常用类型：`feat`、`fix`、`test`、`refactor`、`docs`、`build`、`chore`。

## 6. 推送并创建 Pull Request

```bash
git push -u origin feature/task-name
```

在 GitHub 上将该分支创建 Pull Request，目标分支选择 `develop`。完整填写：

- 修改目的和负责角色；
- 修改目录；
- API/Schema 是否变化；
- 执行的测试命令和结果；
- 页面截图；
- 已知限制；
- 需要谁评审。

## 7. 文件归属

完整映射以 `docs/TASKS.md` 为准。简单对应：

- A：Water；
- B：Gas 与 Gas analytics；
- C：Attraction 与 Parking Billing mining；
- D：Library；
- E：两个 Parking 服务及 Parking Billing 原始日志；
- Leader：共享前端、Gateway 主入口、Compose、CI 和最终集成。

成员拥有主要编辑责任，不代表可以跳过评审；其他成员也可以在 Issue 和 PR 中
提供测试、建议和修复。

## 8. API 协作顺序

1. 在 `contracts/` 定义 Endpoint、Schema、状态和错误码。
2. 受影响成员与 Leader 确认。
3. 实现业务服务和测试。
4. 在自己对应的 Gateway router 中接入。
5. 在自己对应的 service template 中接入页面。
6. 运行完整测试和 Compose smoke test。

禁止后端先随意返回一个 JSON，再要求前端适配。

## 9. 前端协作

各成员只编辑：

```text
frontend/templates/services/<service-slug>.html
```

需要额外样式或脚本时创建服务专属文件。不要复制整个 `base.html`，不要建立第二套
导航，不要在浏览器中写死 `8101` 等服务端口。浏览器业务请求必须经过 Gateway。

## 10. 同步 develop

功能开发期间定期同步：

```bash
git fetch origin
git merge origin/develop
```

在自己的功能分支解决冲突，解决后重新运行测试。无法判断冲突内容属于谁时联系
文件负责人；不要通过删除另一方代码来消除冲突。

## 11. Pull Request 合并前验证

```bash
python -m ruff check .
python -m pytest
docker compose config
docker compose up --build
python scripts/smoke_test.py
```

页面修改还需要从主页面实际完成受影响流程并附截图。

## 12. 评审建议

- A 与 B 互相评审 Water/Gas；
- C 与 E 共同评审 Parking Billing 日志交接；
- D 重点检查命名、Schema 和 API 一致性；
- E 评审 C 的 Attraction；
- Leader 评审所有共享文件和最终集成影响。

评审要实际运行代码，而不是只看文件数量和拼写。

## 13. 出错时不要做什么

不熟悉 Git 时不要执行：

```text
git reset --hard
git clean -fd
git push --force
```

这些命令可能永久删除工作或改写共享历史。将 `git status`、分支名和错误信息发给
Leader或让 AI 只做只读诊断。

## 14. 仓库外工作

会议报告、最终报告、BSRL、BPMN、语义标注、ArchiMate 和 SoaML 在外部
Master Report 工作区维护。本仓库不承担 Word/腾讯文档的多人合并。
