import pytest

from dep_watch_agent import __version__
from dep_watch_agent.cli import main


def test_main_runs(capsys):
    assert main([]) == 0
    assert "dep-watch-agent" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
