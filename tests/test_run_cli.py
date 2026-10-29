import logging
import sys
from argparse import Namespace

import pytest

import run
from conftest import make_cfg
from src.utils import parse_arguments


def failing_exec(error):
    def fail(*args, **kwargs):
        raise error

    return fail


@pytest.mark.parametrize('entry', ['cli', 'api'])
@pytest.mark.parametrize(
    'error, status',
    [
        (Exception('503'), (503, 'ServiceNotAvailable')),
        (Exception('422'), (422, 'InvalidConfiguration')),
        (Exception('600'), (600, 'NotMapped')),
        # Only Exception('<code>') carries an exit code; a KeyError on a number is a crash.
        (KeyError(503), (1, 'UnexpectedError')),
        (KeyError('jan24'), (1, 'UnexpectedError')),
        (Exception('Error downloading Google Sheet: 404'), (1, 'UnexpectedError')),
    ],
)
def test_errors_become_exit_codes(monkeypatch, entry, error, status):
    monkeypatch.setattr(run, 'exec', failing_exec(error))
    if entry == 'cli':
        assert run.run_cli(Namespace(cfg_file='cfg.yml', is_quiet=None, log_level=None)) == status
    else:
        assert run.run_api('cfg.yml') == status


def test_an_unexpected_error_prints_its_traceback(monkeypatch, capsys):
    monkeypatch.setattr(run, 'exec', failing_exec(KeyError('jan24')))
    run.run_cli(Namespace(cfg_file='cfg.yml', is_quiet=None, log_level=None))
    err = capsys.readouterr().err
    assert 'Traceback' in err
    assert "KeyError: 'jan24'" in err


def test_success_is_exit_code_0(monkeypatch):
    monkeypatch.setattr(run, 'exec', lambda *args, **kwargs: None)
    assert run.run_cli(Namespace(cfg_file='cfg.yml', is_quiet=None, log_level=None)) == 0


@pytest.mark.parametrize(
    'argv, is_quiet, log_level',
    [
        ([], None, None),
        (['--quiet'], True, None),
        (['-q', '--log-level', 'debug'], True, 'DEBUG'),
    ],
)
def test_flags_are_none_unless_given(monkeypatch, argv, is_quiet, log_level):
    monkeypatch.setattr(sys, 'argv', ['run.py', '--cfg', 'x.yml'] + argv)
    args = parse_arguments()
    assert (args.is_quiet, args.log_level) == (is_quiet, log_level)


def test_an_unknown_log_level_is_refused(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['run.py', '--log-level', 'loud'])
    with pytest.raises(SystemExit):
        parse_arguments()


def test_run_cli_passes_the_flags_on(monkeypatch):
    calls = []
    monkeypatch.setattr(run, 'exec', lambda *args: calls.append(args))
    run.run_cli(Namespace(cfg_file='cfg.yml', is_quiet=True, log_level='DEBUG'))
    assert calls == [('cfg.yml', True, 'DEBUG')]


def chatty_cfg(tmp_path):
    cfg = make_cfg(tmp_path)
    cfg.write_text(
        cfg.read_text(encoding='utf-8').replace('quiet: true', 'quiet: false'), encoding='utf-8'
    )
    return cfg


def test_quiet_flag_overrides_the_config(offline, capsys):
    run.exec(chatty_cfg(offline))
    assert 'Transactions:' in capsys.readouterr().out
    run.exec(chatty_cfg(offline), is_quiet=True)
    assert capsys.readouterr().out == ''


@pytest.fixture
def log_handlers():
    yield
    logger = logging.getLogger('LogManager')
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)


def test_log_level_flag_overrides_the_config(offline, log_handlers):
    # The fixture config has log-level: notset, which writes no log.
    run.exec(make_cfg(offline), log_level='INFO')
    logs = list((offline / 'log').glob('app_*.log'))
    assert len(logs) == 1
    assert 'Transactions retrieved.' in logs[0].read_text(encoding='utf-8')
