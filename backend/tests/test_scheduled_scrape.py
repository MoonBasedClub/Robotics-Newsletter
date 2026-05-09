from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app import scheduled_scrape


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _FixedDateTime(datetime):
    current = datetime(2026, 5, 8, 9, 5, tzinfo=ZoneInfo("America/New_York"))

    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return cls.current.replace(tzinfo=None)
        return cls.current.astimezone(tz)


def _settings():
    return SimpleNamespace(
        scheduler_timezone="America/New_York",
        daily_run_hour=9,
        daily_run_minute=0,
    )


def test_is_in_schedule_window_accepts_github_cron_drift(monkeypatch):
    monkeypatch.setattr(scheduled_scrape, "get_settings", _settings)

    assert scheduled_scrape.is_in_schedule_window(
        datetime(2026, 5, 8, 8, 55, tzinfo=ZoneInfo("America/New_York"))
    )
    assert scheduled_scrape.is_in_schedule_window(
        datetime(2026, 5, 8, 9, 20, tzinfo=ZoneInfo("America/New_York"))
    )
    assert not scheduled_scrape.is_in_schedule_window(
        datetime(2026, 5, 8, 9, 21, tzinfo=ZoneInfo("America/New_York"))
    )


def test_scheduled_scrape_exits_outside_window(monkeypatch):
    calls = []

    class OutsideWindowDateTime(_FixedDateTime):
        current = datetime(2026, 5, 8, 10, 0, tzinfo=ZoneInfo("America/New_York"))

    monkeypatch.setattr(scheduled_scrape, "datetime", OutsideWindowDateTime)
    monkeypatch.setattr(scheduled_scrape, "get_settings", _settings)
    monkeypatch.setattr(scheduled_scrape, "run_daily_digest", lambda *args, **kwargs: calls.append("run"))

    assert scheduled_scrape.main([]) == 0
    assert calls == []


def test_scheduled_scrape_runs_inside_window(monkeypatch):
    fake_session = _FakeSession()
    calls = []

    monkeypatch.setattr(scheduled_scrape, "datetime", _FixedDateTime)
    monkeypatch.setattr(scheduled_scrape, "get_settings", _settings)
    monkeypatch.setattr(scheduled_scrape.Base.metadata, "create_all", lambda bind: calls.append(("create_all", bind)))
    monkeypatch.setattr(scheduled_scrape, "engine", object())
    monkeypatch.setattr(scheduled_scrape, "SessionLocal", lambda: fake_session)
    monkeypatch.setattr(scheduled_scrape, "_resolve_schedule", lambda date_override: datetime(2026, 5, 8, 13, 0))
    monkeypatch.setattr(scheduled_scrape, "get_run_for_schedule", lambda session, scheduled_for: None)

    def fake_run_daily_digest(session, date_override=None, force=False):
        calls.append(("run", session, date_override, force))
        return 42

    monkeypatch.setattr(scheduled_scrape, "run_daily_digest", fake_run_daily_digest)

    assert scheduled_scrape.main([]) == 0
    assert calls[1] == ("run", fake_session, "2026-05-08", False)
    assert fake_session.closed is True


def test_scheduled_scrape_skips_existing_scheduled_run(monkeypatch):
    fake_session = _FakeSession()
    existing = SimpleNamespace(id=7, status="completed")
    calls = []

    monkeypatch.setattr(scheduled_scrape, "datetime", _FixedDateTime)
    monkeypatch.setattr(scheduled_scrape, "get_settings", _settings)
    monkeypatch.setattr(scheduled_scrape.Base.metadata, "create_all", lambda bind: None)
    monkeypatch.setattr(scheduled_scrape, "SessionLocal", lambda: fake_session)
    monkeypatch.setattr(scheduled_scrape, "_resolve_schedule", lambda date_override: datetime(2026, 5, 8, 13, 0))
    monkeypatch.setattr(scheduled_scrape, "get_run_for_schedule", lambda session, scheduled_for: existing)
    monkeypatch.setattr(scheduled_scrape, "run_daily_digest", lambda *args, **kwargs: calls.append("run"))

    assert scheduled_scrape.main([]) == 0
    assert calls == []
    assert fake_session.closed is True
