"""The v2 series records new candles with a complete immutable source manifest."""

import asyncio
import hashlib
import sqlite3
from copy import deepcopy
from datetime import timedelta, timezone
from pathlib import Path

import pytest
from paper_journal import PaperJournal, ResearchObservationConflict
from paper_research import ExperimentConfigMismatch, ResearchStore
from paper_scanner import ScannerConfig, baseline_config
from test_paper_journal import analysis
from test_paper_scanner import scanner_for

V2 = "prospective-baseline-v2"


def research_metadata(config):
    return {
        "experiment_id": V2,
        "experiment_config": config,
        "origin": "LIVE",
        "data_source": "BINANCE_SPOT_KLINES",
        "regime": {"version": "regime-v1"},
        "quality_bucket": "7-10",
    }


def test_v2_manifest_has_exact_strategy_and_transport_file_hashes():
    config = baseline_config(ScannerConfig(experiment_id=V2))
    root = Path(__file__).resolve().parents[1] / "backend"
    assert config["strategy_version"] == "technical-v1"
    assert config["source_contract"] == "strategy-and-paper-transport-v2"
    assert set(config["transport_source_sha256"]) == {"binance_http.py", "market_data.py"}
    for category in ("strategy_source_sha256", "transport_source_sha256"):
        for name, digest in config[category].items():
            assert digest == hashlib.sha256((root / name).read_bytes()).hexdigest()


def test_v1_is_immutable_and_v2_is_a_separate_strict_series(tmp_path):
    store = ResearchStore(PaperJournal(tmp_path / "paper.sqlite3"))
    old = {"strategy_version": "technical-v1", "code_sha256": "a" * 64}
    store.register_experiment("prospective-baseline-v1", old)
    new = baseline_config(ScannerConfig(experiment_id=V2))
    store.register_experiment(V2, new)
    assert store.experiment_config("prospective-baseline-v1") == old
    assert store.experiment_config(V2) == new
    with pytest.raises(ExperimentConfigMismatch):
        store.register_experiment("prospective-baseline-v1", {**old, "code_sha256": "b" * 64})
    with pytest.raises(ExperimentConfigMismatch):
        store.register_experiment(V2, {**new, "code_sha256": old["code_sha256"]})
    changed = deepcopy(new)
    changed["transport_source_sha256"]["binance_http.py"] = "0" * 64
    with pytest.raises(ExperimentConfigMismatch):
        store.verify_experiment(V2, changed)
    with pytest.raises(ExperimentConfigMismatch):
        store.register_experiment(V2, changed)


def test_v2_new_candle_provenance_and_conflicts_are_atomic(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    store = ResearchStore(journal)
    config = baseline_config(ScannerConfig(experiment_id=V2))
    store.register_experiment(V2, config, snapshot.technical.timestamp - timedelta(seconds=1))
    signal_id = journal.record_signal(
        analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(config)
    )
    with sqlite3.connect(journal.path) as db:
        before = db.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        owner = db.execute(
            "SELECT experiment_id FROM research_observations WHERE signal_id=?", (signal_id,)
        ).fetchone()[0]
    assert before == 1 and owner == V2
    assert (
        journal.record_signal(analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(config))
        == signal_id
    )

    changed = deepcopy(config)
    changed["transport_source_sha256"]["binance_http.py"] = "0" * 64
    with pytest.raises(ResearchObservationConflict, match="V2_SOURCE_CONFIG_MISMATCH"):
        journal.record_signal(analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(changed))
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == before
        assert (
            db.execute(
                "SELECT experiment_id FROM research_observations WHERE signal_id=?", (signal_id,)
            ).fetchone()[0]
            == V2
        )


def test_v2_journal_rechecks_source_bytes_at_write(tmp_path, snapshot, monkeypatch):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    config = baseline_config(ScannerConfig(experiment_id=V2))
    ResearchStore(journal).register_experiment(
        V2, config, snapshot.technical.timestamp - timedelta(seconds=1)
    )
    original_read_bytes = Path.read_bytes

    def changed_transport(path):
        contents = original_read_bytes(path)
        return contents + b"\n" if path.name == "binance_http.py" else contents

    monkeypatch.setattr(Path, "read_bytes", changed_transport)
    with pytest.raises(ResearchObservationConflict, match="V2_SOURCE_CONFIG_MISMATCH"):
        journal.record_signal(analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(config))
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0


def test_v2_rejects_preexisting_and_prestart_candles(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    store = ResearchStore(journal)
    config = baseline_config(ScannerConfig(experiment_id=V2))
    store.register_experiment(V2, config, snapshot.technical.timestamp - timedelta(seconds=1))
    prior = journal.record_signal(analysis(snapshot), origin="SCANNER_LIVE")
    with pytest.raises(ResearchObservationConflict, match="V2_OBSERVATION_OWNER_CONFLICT"):
        journal.record_signal(analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(config))
    with sqlite3.connect(journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM research_observations").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1
        assert db.execute("SELECT id FROM observations").fetchone()[0] == prior

    later = PaperJournal(tmp_path / "later.sqlite3")
    later_store = ResearchStore(later)
    later_store.register_experiment(V2, config, snapshot.technical.timestamp)
    with pytest.raises(ResearchObservationConflict, match="V2_CANDLE_PREDATES_EXPERIMENT"):
        later.record_signal(analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(config))
    with sqlite3.connect(later.path) as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0


def test_v2_scanner_stops_if_source_changes_after_registration(candles, tmp_path, monkeypatch):
    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch, experiment_id=V2)
    scanner.initialize()
    original = baseline_config

    def altered(config):
        result = original(config)
        result["transport_source_sha256"]["binance_http.py"] = "0" * 64
        return result

    monkeypatch.setattr("paper_scanner.baseline_config", altered)
    with pytest.raises(ExperimentConfigMismatch, match="source or configuration changed"):
        asyncio.run(scanner.scan_once())
    with sqlite3.connect(scanner.journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0


def test_v2_scanner_stops_on_preexisting_candle(candles, tmp_path, monkeypatch):
    from analysis_service import analyze_market

    frame = candles(n=130, end="2026-09-28T10:00:00Z")
    scanner = scanner_for(frame, tmp_path, monkeypatch, experiment_id=V2)
    scanner.initialize()
    close = frame.close_time.iloc[-1].to_pydatetime()
    manual = analyze_market(
        "BTCUSDT", "1h", close + timedelta(milliseconds=1), loader=lambda *_, **__: frame.tail(120)
    )
    scanner.journal.record_signal(manual, origin="TELEGRAM_REVIEW")
    with pytest.raises(ResearchObservationConflict, match="V2_OBSERVATION_OWNER_CONFLICT"):
        asyncio.run(scanner.scan_once())
    with sqlite3.connect(scanner.journal.path) as db:
        assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM research_observations").fetchone()[0] == 0


def test_v2_rejects_same_instant_from_other_strategy_and_utc_offset(tmp_path, snapshot):
    journal = PaperJournal(tmp_path / "paper.sqlite3")
    config = baseline_config(ScannerConfig(experiment_id=V2))
    ResearchStore(journal).register_experiment(
        V2, config, snapshot.technical.timestamp - timedelta(seconds=1)
    )
    journal.record_signal(analysis(snapshot), origin="TELEGRAM_REVIEW")
    with sqlite3.connect(journal.path) as db:
        db.execute(
            "UPDATE observations SET id=?, strategy_version=?, candle_close=?",
            (
                "legacy-other-strategy",
                "legacy-v0",
                snapshot.technical.timestamp.astimezone(timezone(timedelta(hours=2))).isoformat(),
            ),
        )
    with pytest.raises(ResearchObservationConflict, match="V2_CANDLE_ALREADY_OBSERVED"):
        journal.record_signal(analysis(snapshot), origin="SCANNER_LIVE", research=research_metadata(config))
