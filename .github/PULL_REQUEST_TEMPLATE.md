## 修改目的

- 成员角色：
- 服务或共享组件：
- 相关 Issue/契约：

请描述一个明确、集中的结果。

## 修改范围

- 修改的负责目录：
- 修改的共享目录：
- 有意暂不修改的内容：

## 契约与集成影响

- [ ] 不修改 API、Schema 或活动名称
- [ ] 向后兼容，并已更新契约
- [ ] Breaking Change，已获得相关负责人和 Leader 同意

列出修改的 Endpoint、字段、状态、错误码、端口或流程活动：

## 验证

- [ ] `python -m ruff check .`
- [ ] `python -m pytest`
- [ ] `docker compose config`
- [ ] 影响集成时执行 `docker compose up --build`
- [ ] 影响集成时执行 `python scripts/smoke_test.py`
- [ ] 前端修改已附截图
- [ ] 未提交密钥、`.env`、`.team-role`、数据库或生成结果

粘贴相关命令结果：

## 人工业务流程

说明从哪个页面开始、执行哪些操作、预期得到什么结果。

## 已知限制

列出尚未完成或明确推迟的内容。

## 评审

- 契约/服务负责人：
- 交叉评审人：
- 是否需要 Leader 评审：
