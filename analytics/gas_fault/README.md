# Gas Fault 流程分析

负责人：成员 B。

- `simulation/`：确定性的事件日志生成器；
- `event_logs/`：原始日志和明确标记的模拟日志；
- `mining/`：可重复运行的 PM4Py 分析；
- `results/`：生成的图和表，默认忽略。

所有 `activity` 值必须与冻结后的 BPMN 活动词典一致。
