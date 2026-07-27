# Process analytics workspaces

Install analytics dependencies separately:

```bash
python -m pip install -r requirements-analytics.txt
```

Gas Fault is owned by Member B. Parking Billing log generation/export is owned by
Member E and its mining/analysis is owned by Member C.

Raw logs are immutable inputs. Cleaned data and generated results must be written
to separate locations with reproducible scripts.
