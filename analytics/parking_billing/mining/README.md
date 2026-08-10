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
