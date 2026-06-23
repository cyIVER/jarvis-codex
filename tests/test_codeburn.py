from jarvis_codex.codeburn import CodeburnStatus, parse_codeburn_status


def test_parse_codeburn_status_extracts_usage_fields():
    status = parse_codeburn_status("  Today  $0.00  0 calls    Month  $527.99  5787 calls")

    assert status.available is True
    assert status.today_cost == 0.0
    assert status.today_calls == 0
    assert status.month_cost == 527.99
    assert status.month_calls == 5787
    assert status.error is None


def test_parse_codeburn_status_reports_unrecognized_output():
    status = parse_codeburn_status("not a status line")

    assert status.available is False
    assert status.error == "unrecognized_status_output"
    assert status.raw == "not a status line"


def test_codeburn_status_serializes_non_executing_contract():
    status = CodeburnStatus(
        available=True,
        today_cost=1.23,
        today_calls=4,
        month_cost=5.67,
        month_calls=8,
        raw="status",
    )

    data = status.to_dict()

    assert data["writes_state"] is False
    assert data["shell"] is False
