from io import StringIO

from django.core.management import call_command


def test_system_checks_pass() -> None:
    call_command("check", verbosity=0)


def test_run_integration_cycle_interval_dry_run() -> None:
    stdout = StringIO()
    call_command("run_integration_cycle", "--dry-run", "--interval=60", stdout=stdout)
    output = stdout.getvalue()
    assert "event_limit=100" in output
    assert "every 60s" in output
