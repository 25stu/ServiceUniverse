# API 契约

本目录是服务负责人、Gateway、共享前端、测试和流程分析之间的集成边界。

实现业务 Endpoint 前，需要增加：

- `schemas/<service-slug>.openapi.yaml` 或对应 JSON Schema；
- 一个成功请求/响应示例；
- 至少一个代表性错误示例；
- 允许的枚举与状态值；
- 涉及流程分析时使用的事件活动名称。

`catalog.json` 是六项服务身份与端口的信息来源。Service slug、负责人、
Provider 分组、端口或重点微服务标记的修改必须由 Leader 评审。
