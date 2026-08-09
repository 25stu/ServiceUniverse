# Parking Billing simulated event export

Member E owns this deterministic generator and the activity dictionary. The dictionary
is frozen by E and marked as pending Member C review before formal process mining.

Generate the raw simulated log from the repository root:

```bash
python analytics/parking_billing/simulation_or_export/generate_event_log.py
```

The default output is
`analytics/parking_billing/event_logs/parking_billing_simulated.csv`. Use `--cases`,
`--seed`, and `--output` to create a separate reproducible dataset. Every generated row
has `source=simulated`; never present it as a production export.

The generator includes normal payment, rejected payment, and still-active paths. Member C
must clean into a new file and must not overwrite the raw event log.
