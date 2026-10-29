import logging

from src.csv_mngr import CsvMngr, write_csv_lazy, write_markdown_table
from src.log_mngr import LogManager
from src.report_mngr import generate_transactions_html
from src.utils import get_yaml_parameter

# Sheets export UTF-8, and Windows defaults to cp1252, in which byte 0x81 (the second byte of
# 'Á' in UTF-8) is undefined and '₿' doesn't exist.
TEXT = 'Société Á €'


def test_csv_reads_utf8(tmp_path):
    path = tmp_path / 'transactions.csv'
    path.write_bytes(f'platform,currency\n{TEXT},EUR\n'.encode())
    assert CsvMngr(path, ['platform', 'currency']).read() == [{'platform': TEXT, 'currency': 'EUR'}]


def test_csv_reads_utf8_with_a_byte_order_mark(tmp_path):
    # Excel's "CSV UTF-8" starts with one.
    path = tmp_path / 'symbols.csv'
    path.write_bytes('﻿symbol,ticker\nvwce,VWCE.DE\n'.encode())
    assert CsvMngr(path, ['symbol', 'ticker']).read() == [{'symbol': 'vwce', 'ticker': 'VWCE.DE'}]


def test_yaml_reads_utf8(tmp_path):
    path = tmp_path / 'cfg.yml'
    path.write_bytes(f'# {TEXT}\ncomp:\n  default-currency: EUR\n'.encode())
    assert get_yaml_parameter(path) == {'comp': {'default-currency': 'EUR'}}


def test_csv_and_markdown_are_written_as_utf8(tmp_path):
    CsvMngr(tmp_path / 'a.csv', ['name']).write([['₿ ' + TEXT]])
    write_markdown_table(tmp_path / 'b.md', 'Total', 'Metric', 'Value', {'₿': TEXT})
    write_csv_lazy(tmp_path / 'c.csv', {'₿': {'exchange': TEXT}}, 'symbol')
    for name in ('a.csv', 'b.md', 'c.csv'):
        written = (tmp_path / name).read_bytes()
        assert '₿'.encode() in written
        assert TEXT.encode() in written


def test_the_html_report_is_written_as_utf8(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    transaction = {
        'date': '2024-01-15',
        'type': 'buy',
        'exchange': 'XPAR',
        'symbol': '₿',
        'quantity': 1.0,
        'price': 1.0,
        'wallet': TEXT,
    }
    generate_transactions_html([transaction], f'{tmp_path.as_posix()}/')
    html = (tmp_path / 'transactions.html').read_bytes().decode('utf-8')
    assert TEXT in html
    assert '<td>₿</td>' in html


def test_the_log_file_is_written_as_utf8(tmp_path):
    log_file = tmp_path / 'log' / 'app.log'
    logger = LogManager(log_file=str(log_file), log_level='INFO').get_logger()
    try:
        logger.info('₿ ' + TEXT)
        for handler in logger.handlers:
            handler.flush()
        assert ('₿ ' + TEXT).encode() in log_file.read_bytes()
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)
