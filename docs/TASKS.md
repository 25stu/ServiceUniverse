# 成员任务与代码归属

本文件只描述可执行仓库工作。报告与建模产出不在这里维护。

## Leader

主要目录：

- `frontend/` 共享文件；
- `gateway/app/main.py` 与 Gateway 公共工具；
- `compose.yaml`、根 Docker 配置、依赖和 CI；
- `contracts/catalog.json`；
- 根目录技术说明。

职责：

- 维护可运行的集成基线；
- 评审 Breaking Contract 和共享 UI 修改；
- 保持 `main` 稳定、`develop` 可运行；
- 执行每周集成、smoke test 和最终打包。

## 成员 A — Water Billing and Payment

主要目录：

- `services/water_billing/`；
- `gateway/app/routers/water_billing.py`；
- `frontend/templates/services/water-billing.html`；
- `contracts/` 中的 Water 契约与示例。

最小代码范围：

- 查询市民账单；
- 支付符合条件的未支付账单；
- 查询支付结果或收据；
- 拒绝重复支付和非法状态转换；
- 由于是重点微服务，需要独立数据存储和服务 Dockerfile。

契约变化时通知 Leader，并提供稳定 Endpoint 给共享前端和演示流程。

## 成员 B — Gas Fault Reporting and Repair Tracking

主要目录：

- `services/gas_fault/`；
- `gateway/app/routers/gas_fault.py`；
- `frontend/templates/services/gas-fault.html`；
- `analytics/gas_fault/`；
- Gas 契约与示例。

最小代码范围：

- 创建故障报告；
- 查询报告和维修状态；
- 按合法阶段更新维修状态；
- 生成或模拟活动名称与 BPMN 词典一致的事件日志。

需要提供可重复执行的日志生成和分析命令。

## 成员 C — Attraction Recommendation and Reservation

主要目录：

- `services/attraction_reservation/`；
- `gateway/app/routers/attraction_reservation.py`；
- `frontend/templates/services/attraction-reservation.html`；
- `analytics/parking_billing/mining/` 与解释结果；
- Attraction 契约与示例。

最小代码范围：

- 根据条件列出或推荐景点；
- 创建和查询预约；
- 校验容量冲突和预约状态；
- 由于是重点微服务，需要独立数据存储和服务 Dockerfile。

从 E 接收冻结后的 Parking Billing 活动词典和原始日志；清洗时不得覆盖原始日志。

## 成员 D — Public Library Membership and Account

主要目录：

- `services/library_account/`；
- `gateway/app/routers/library_account.py`；
- `frontend/templates/services/library-account.html`；
- Library 契约与示例。

最小代码范围：

- 创建图书馆会员；
- 查询会员与账户信息；
- 提供代表性的借阅或账户状态信息；
- 实现校验和明确错误状态。

仓库评审职责：检查跨服务命名、Schema 和 API 一致性。ArchiMate 与 SoaML 在
外部报告工作区完成。

## 成员 E — City Parking Management Center

主要目录：

- `services/parking_availability/`；
- `services/parking_billing/`；
- 两个 Parking Gateway router；
- 两个 Parking 前端模板；
- `analytics/parking_billing/simulation_or_export/` 与原始日志；
- Parking 契约与示例。

Parking Availability 最小代码范围：

- 列出停车场和当前余位；
- 查询单个停车场；
- 提供可重复演示的余位变化；
- 由于是重点微服务，需要独立数据存储和服务 Dockerfile。

Parking Billing 最小代码范围：

- 创建或查询停车会话；
- 结束会话并计算费用；
- 支付符合条件的费用；
- 生成或模拟 C 所需流程事件。

正式分析前与 C 冻结活动名称、生命周期、正常/异常路径和日志 Schema。

## 共享文件

下列文件需要 Leader 评审：

- `contracts/catalog.json`；
- `API_CONVENTION.md`；
- `frontend/templates/base.html`；
- `frontend/static/css/site.css`；
- `gateway/app/main.py`；
- `compose.yaml`；
- 依赖文件；
- `.github/workflows/`。

PR 中必须说明角色、契约影响、验证命令与集成结果。
