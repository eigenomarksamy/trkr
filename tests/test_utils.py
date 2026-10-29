import socket

import pytest

from src import utils


class FakeConnection:
    def __init__(self) -> None:
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def connect(self, address) -> None:
        pass

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def connections(monkeypatch):
    """Stubs every way of opening a socket and records the connections made."""
    made = []

    def create_connection(address, timeout=None):
        made.append((address, timeout))
        connection = FakeConnection()
        made.append(connection)
        return connection

    def new_socket(*args, **kwargs):
        connection = FakeConnection()
        made.append(connection)
        return connection

    monkeypatch.setattr(socket, 'create_connection', create_connection)
    monkeypatch.setattr(socket, 'socket', new_socket)
    yield made
    socket.setdefaulttimeout(None)


def test_check_internet_leaves_the_default_timeout_alone(connections):
    assert utils.check_internet()
    # yfinance and requests run after it, and a global 3 s timeout would apply to them too.
    assert socket.getdefaulttimeout() is None
    assert connections[0] == (('8.8.8.8', 53), 3)


def test_check_internet_closes_its_socket(connections):
    utils.check_internet()
    assert [c.closed for c in connections if isinstance(c, FakeConnection)] == [True]


def test_check_internet_is_false_without_a_connection(monkeypatch, capsys):
    def refuse(address, timeout=None):
        raise ConnectionRefusedError('refused')

    monkeypatch.setattr(socket, 'create_connection', refuse)
    assert not utils.check_internet()
    assert 'refused' in capsys.readouterr().out
