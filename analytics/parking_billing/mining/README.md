# 流程挖掘

成员 C 在此维护可重复运行的数据验证、清洗、流程发现、一致性和性能分析。

当前仓库还没有成员 E 冻结并提交的 Parking Billing 原始日志，因此这里先提供
可重复运行的分析入口。原始输入必须放在 `analytics/parking_billing/event_logs/`
或由命令显式传入；脚本不会覆盖原始日志。

## 期望输入 Schema

必填列：

- `case_id`
- `activity`
- `timestamp`
- `resource`
- `lifecycle`
- `outcome`

可选列：

- `service`
- `citizen_id`
- `cost_minor`
- `duration_seconds`
- `status`

`timestamp` 使用 ISO 8601，建议包含时区，例如 `2026-08-05T09:30:00+10:00`。

## 运行

```bash
python analytics/parking_billing/mining/analyze_parking_billing.py \
  analytics/parking_billing/event_logs/<raw-log>.csv
```

输出：

- `analytics/parking_billing/results/parking_billing_cleaned.csv`
- `analytics/parking_billing/results/parking_billing_summary.json`

## 当前限制

在 E 提供原始日志和活动词典前，C 只能完成脚本、Schema 校验、清洗规则和结果解释
模板；不能声称已经完成真实 Parking Billing 流程挖掘结论。

## 报告解释模板

拿到 E 的原始日志后，报告可按以下结构补齐：

1. 数据来源：说明日志由 Parking Billing 服务模拟或导出，标注为 simulated 或
   exported。
2. 数据质量：报告 case 数、event 数、activity 数、缺失值、时间戳顺序和异常行。
3. 流程变体：列出最常见的 top variants，解释正常支付路径与异常支付路径。
4. 性能分析：比较 case duration 的最小值、中位数和最大值，指出耗时活动或等待点。
5. 一致性分析：将活动序列与最终 BPMN 活动词典对齐，说明缺失活动、额外活动或顺序
   偏差。
6. 结论：总结 Parking Billing 流程是否稳定、是否存在重复支付、失败支付或长等待
   问题。
