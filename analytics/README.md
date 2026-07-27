# 流程分析工作区

单独安装分析依赖：

```bash
python -m pip install -r requirements-analytics.txt
```

Gas Fault 由成员 B 负责。Parking Billing 日志生成/导出由成员 E 负责，
挖掘与分析由成员 C 负责。

原始日志是不可修改的输入。数据清洗和生成结果必须写入其他位置，并提供可重复脚本。
