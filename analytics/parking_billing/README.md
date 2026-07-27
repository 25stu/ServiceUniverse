# Parking Billing analytics

Ownership:

- Member E: `simulation_or_export/`, raw event logs, activity dictionary;
- Member C: validation, cleaning, `mining/`, and interpreted results.

Keep raw input immutable. A cleaning script must write a new file rather than
editing the original log.
