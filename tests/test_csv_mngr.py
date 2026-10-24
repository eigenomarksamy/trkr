from src.csv_mngr import CsvMngr

def read(tmp_path, text, headers):
    path = tmp_path / 'data.csv'
    path.write_text(text, encoding='utf-8')
    return CsvMngr(path, headers).read()

def test_read_maps_columns_by_position_and_drops_the_first_row(tmp_path):
    rows = read(tmp_path, 'symbol,ticker\naaa,AAA.AS\nbbb,BBB\n', ['symbol', 'ticker'])
    assert rows == [{'symbol': 'aaa', 'ticker': 'AAA.AS'}, {'symbol': 'bbb', 'ticker': 'BBB'}]

def test_read_ignores_the_header_names(tmp_path):
    rows = read(tmp_path, 'ticker,symbol\nAAA.AS,aaa\n', ['symbol', 'ticker'])
    assert rows == [{'symbol': 'AAA.AS', 'ticker': 'aaa'}]

def test_read_without_a_header_row_loses_the_first_row(tmp_path):
    rows = read(tmp_path, 'aaa,AAA.AS\nbbb,BBB\n', ['symbol', 'ticker'])
    assert rows == [{'symbol': 'bbb', 'ticker': 'BBB'}]

def test_read_short_long_and_blank_rows(tmp_path):
    rows = read(tmp_path, 'a,b\n1\n1,2,3\n\n', ['a', 'b'])
    assert rows == [{'a': '1'}, {'a': '1', 'b': '2'}, {}]

def test_convert_read_list_to_dict_maps_first_value_to_second():
    rows = [{'symbol': 'aaa', 'ticker': 'AAA.AS', 'extra': 'x'}, {'symbol': 'eur', 'ticker': 'USDEUR=X'}]
    assert CsvMngr.convert_read_list_to_dict(rows) == {'aaa': 'AAA.AS', 'eur': 'USDEUR=X'}
