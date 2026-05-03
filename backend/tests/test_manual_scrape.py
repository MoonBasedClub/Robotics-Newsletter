from app import manual_scrape


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_manual_scrape_cli_forces_fresh_run(monkeypatch, capsys):
    fake_session = _FakeSession()
    calls = []

    monkeypatch.setattr(
        manual_scrape.Base.metadata,
        "create_all",
        lambda bind: calls.append(("create_all", bind)),
    )
    monkeypatch.setattr(manual_scrape, "engine", object())
    monkeypatch.setattr(manual_scrape, "SessionLocal", lambda: fake_session)

    def fake_run_daily_digest(session, date_override=None, force=False):
        calls.append(("run", session, date_override, force))
        return 42

    monkeypatch.setattr(manual_scrape, "run_daily_digest", fake_run_daily_digest)

    exit_code = manual_scrape.main(["--date", "2026-05-03"])

    assert exit_code == 0
    assert calls[1] == ("run", fake_session, "2026-05-03", True)
    assert fake_session.closed is True
    assert "run_id=42" in capsys.readouterr().out


def test_manual_scrape_cli_returns_failure_code(monkeypatch):
    fake_session = _FakeSession()

    monkeypatch.setattr(manual_scrape.Base.metadata, "create_all", lambda bind: None)
    monkeypatch.setattr(manual_scrape, "SessionLocal", lambda: fake_session)

    def fail_run_daily_digest(session, date_override=None, force=False):
        raise RuntimeError("network broke")

    monkeypatch.setattr(manual_scrape, "run_daily_digest", fail_run_daily_digest)

    assert manual_scrape.main([]) == 1
    assert fake_session.closed is True
