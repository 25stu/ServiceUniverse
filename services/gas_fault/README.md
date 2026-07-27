# Gas Fault Reporting and Repair Tracking

- 负责人：成员 B
- 端口：`8102`
- 类型：业务服务
- Gateway：`gateway/app/routers/gas_fault.py`
- 前端：`frontend/templates/services/gas-fault.html`
- 流程分析：`analytics/gas_fault/`

最小流程：

1. 提交故障报告；
2. 查询报告与当前维修状态；
3. 执行合法状态转换；
4. 生成或模拟可重复的流程事件日志。

生成正式日志前，需要冻结 BPMN 活动名称。

```bash
python -m uvicorn services.gas_fault.app.main:app --reload --port 8102
```

验证：<http://localhost:8102/health>
