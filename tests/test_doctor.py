from typer.testing import CliRunner

from discovery.cli import app


def test_doctor_reports_local_health(tmp_path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["doctor", "--database", f"sqlite:///{tmp_path / 'doctor.db'}"],
    )
    assert result.exit_code == 0
    assert '"database_healthy": true' in result.stdout
    assert '"gateway_configured": false' in result.stdout
