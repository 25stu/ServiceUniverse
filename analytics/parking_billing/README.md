# Parking Billing 流程分析

分工：

- 成员 E：`simulation_or_export/`、原始事件日志和活动词典；
- 成员 C：日志验证、清洗、`mining/` 和结果解释。

原始输入必须保持不变。清洗脚本应写入新文件，不得覆盖原日志。
