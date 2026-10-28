import os
import pathlib

import pytest

from src.sheets_mngr import get_google_sheet


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b'') -> None:
        self.status_code = status_code
        self.content = content


@pytest.fixture
def requested_urls(monkeypatch):
    urls = []

    def fake_get(url, *args, **kwargs):
        urls.append(url)
        return FakeResponse(200, b'symbol,ticker\naaa,AAA.AS\n')

    monkeypatch.setattr('src.sheets_mngr.requests.get', fake_get)
    return urls


def test_sheet_id_becomes_a_csv_export_url(tmp_path, requested_urls):
    out_dir = f'{tmp_path.as_posix()}/sheets/'
    path = get_google_sheet('made-up-sheet-id', out_dir, 'symbols.csv')
    assert requested_urls == [
        'https://docs.google.com/spreadsheets/d/made-up-sheet-id/export?format=csv'
    ]
    assert path == os.path.join(out_dir, 'symbols.csv')
    assert pathlib.Path(path).read_bytes() == b'symbol,ticker\naaa,AAA.AS\n'


def test_https_address_is_used_as_is(tmp_path, requested_urls):
    get_google_sheet('https://example.com/made-up.csv', str(tmp_path), 'symbols.csv')
    assert requested_urls == ['https://example.com/made-up.csv']


@pytest.mark.parametrize(
    'link, export',
    [
        (
            'https://docs.google.com/spreadsheets/d/made-up-id/edit?gid=123#gid=123',
            'https://docs.google.com/spreadsheets/d/made-up-id/export?format=csv&gid=123',
        ),
        (
            'https://docs.google.com/spreadsheets/d/made-up-id/edit#gid=45',
            'https://docs.google.com/spreadsheets/d/made-up-id/export?format=csv&gid=45',
        ),
        (
            'https://docs.google.com/spreadsheets/u/0/d/made-up-id/edit?usp=sharing',
            'https://docs.google.com/spreadsheets/d/made-up-id/export?format=csv',
        ),
        (
            'https://docs.google.com/spreadsheets/d/made-up-id/',
            'https://docs.google.com/spreadsheets/d/made-up-id/export?format=csv',
        ),
    ],
)
def test_browser_link_to_a_sheet_or_tab_becomes_its_csv_export(
    tmp_path, requested_urls, link, export
):
    get_google_sheet(link, str(tmp_path), 'positions.csv')
    assert requested_urls == [export]


@pytest.mark.parametrize(
    'link',
    [
        'https://docs.google.com/spreadsheets/d/made-up-id/export?format=csv&gid=7&range=A1:D9',
        'https://docs.google.com/spreadsheets/d/e/2PACX-made-up/pub?gid=0&single=true&output=csv',
    ],
)
def test_export_and_publish_links_are_used_as_is(tmp_path, requested_urls, link):
    get_google_sheet(link, str(tmp_path), 'positions.csv')
    assert requested_urls == [link]


def test_http_address_is_treated_as_a_sheet_id(tmp_path, requested_urls):
    get_google_sheet('http://example.com/made-up.csv', str(tmp_path), 'symbols.csv')
    assert requested_urls == [
        'https://docs.google.com/spreadsheets/d/http://example.com/made-up.csv/export?format=csv'
    ]


def test_failed_download_raises_with_the_status_code(tmp_path, monkeypatch):
    monkeypatch.setattr('src.sheets_mngr.requests.get', lambda url: FakeResponse(404))
    with pytest.raises(Exception, match='^Error downloading Google Sheet: 404$'):
        get_google_sheet('made-up-sheet-id', str(tmp_path), 'symbols.csv')
    assert not (tmp_path / 'symbols.csv').exists()
