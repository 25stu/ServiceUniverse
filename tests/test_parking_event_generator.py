from analytics.parking_billing.simulation_or_export.generate_event_log import event_rows


def test_parking_event_generation_is_deterministic() -> None:
    first = event_rows(12, 927)
    second = event_rows(12, 927)

    assert first == second
    assert {row["source"] for row in first} == {"simulated"}
    assert {row["lifecycle"] for row in first} == {"complete"}
    assert "Confirm Payment" in {row["activity"] for row in first}
    assert "Reject Payment" in {row["activity"] for row in first}
