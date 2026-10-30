from ai_confidence_checker import AIConfidenceChecker


def test_direction_aware_quality():
    checker = AIConfidenceChecker()
    long = checker.analyze_signal_quality("BTCUSDT", dict(volume_ratio=2, confluence=90, direction="LONG"))
    short = checker.analyze_signal_quality("BTCUSDT", dict(volume_ratio=2, confluence=-90, direction="SHORT"))
    conflict = checker.analyze_signal_quality(
        "BTCUSDT", dict(volume_ratio=2, confluence=90, direction="SHORT")
    )
    assert long["ai_confidence_score"] == short["ai_confidence_score"] >= 7.5
    assert conflict["ai_confidence_score"] < 7.5
    assert checker.analyze_signal_quality("BTCUSDT", {})["status"] == "DATA_UNAVAILABLE"


def test_alert_contract():
    checker = AIConfidenceChecker()
    assert not checker.should_send_alert("BTCUSDT", "HOLD", 8)
    alerts = checker.prioritize_alerts(
        [dict(symbol="BTCUSDT", signal_type="BUY", strength=4, confluence_score=80)]
    )
    assert len(checker.filter_duplicate_alerts(alerts)) == 1
    assert checker.filter_duplicate_alerts(alerts) == []
