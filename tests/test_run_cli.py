from argparse import Namespace

import pytest

import run


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
        assert run.run_cli(Namespace(cfg_file='cfg.yml')) == status
    else:
        assert run.run_api('cfg.yml') == status


def test_an_unexpected_error_prints_its_traceback(monkeypatch, capsys):
    monkeypatch.setattr(run, 'exec', failing_exec(KeyError('jan24')))
    run.run_cli(Namespace(cfg_file='cfg.yml'))
    err = capsys.readouterr().err
    assert 'Traceback' in err
    assert "KeyError: 'jan24'" in err


def test_success_is_exit_code_0(monkeypatch):
    monkeypatch.setattr(run, 'exec', lambda *args, **kwargs: None)
    assert run.run_cli(Namespace(cfg_file='cfg.yml')) == 0
