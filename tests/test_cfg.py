import pytest
from conftest import make_cfg
from src.cfg_mngr import (ConfigMapUri, ImaginaryPortfolioCfg, PositionsCfg, create_cfg,
                          parse_imaginary_portfolios, parse_positions, parse_projection_cfg)
from src.projection import ProjectionCfg

def test_configs_without_new_blocks_still_load(tmp_path):
    cfg = create_cfg(make_cfg(tmp_path))
    assert cfg.get_param(ConfigMapUri.PROJECTION) is None
    assert cfg.get_param(ConfigMapUri.IMAGINARY_PORTFOLIOS) == []
    assert cfg.get_param(ConfigMapUri.POSITIONS) is None
    assert cfg.get_param(ConfigMapUri.TRANSACTIONS_SOURCE) == 'local'

def test_create_cfg_reads_both_blocks(tmp_path):
    cfg = create_cfg(make_cfg(tmp_path, """
imaginary-portfolios:
  - name: paper
    source: local
    transactions-dir: examples/paper.csv
projection:
  birth-year: 1990
  retirement-age: 65
  return: 7
  start-net-worth: paper
"""))
    assert cfg.get_param(ConfigMapUri.IMAGINARY_PORTFOLIOS) == [
        ImaginaryPortfolioCfg(name='paper', is_local=True, location='examples/paper.csv')]
    assert cfg.get_param(ConfigMapUri.PROJECTION).start_net_worth == 'paper'

def test_projection_block_maps_every_key():
    block = {'birth-year': 1990, 'retirement-age': 65, 'return': 7,
             'start-net-worth': 25000, 'cash': 500, 'income': 50000,
             'income-growth': 2, 'invest-percent': 15, 'fees': 0.5,
             'inflation': 2, 'deposits-withdrawals': {2030: -20000, '2031': 1000}}
    assert parse_projection_cfg(block, ['portfolio'], 2026) == ProjectionCfg(
        birth_year=1990, retirement_age=65, yearly_return=7, start_net_worth=25000,
        cash=500, income=50000, income_growth=2, invest_percent=15, fees=0.5,
        inflation=2, deposits_withdrawals={2030: -20000, 2031: 1000})

def test_projection_defaults():
    cfg = parse_projection_cfg({'birth-year': 1990, 'retirement-age': 65, 'return': 7,
                                'inflation': None}, ['portfolio'], 2026)
    assert cfg == ProjectionCfg(birth_year=1990, retirement_age=65, yearly_return=7)

@pytest.mark.parametrize('block, message', [
    ({'birth-year': 1990, 'retirement-age': 65}, 'return is required'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': 7, 'invest-pct': 10}, 'unknown keys in projection: invest-pct'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': '7%'}, 'return must be a number'),
    ({'birth-year': 1990.5, 'retirement-age': 65, 'return': 7}, 'birth-year must be a whole number'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': 7, 'start-net-worth': 'other'}, 'start-net-worth must be'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': 7, 'invest-percent': 150}, 'invest-percent must be between 0 and 100'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': 7, 'fees': -1}, 'fees must not be negative'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': -100}, 'return must be above -100'),
    ({'birth-year': 1990, 'retirement-age': 65, 'return': 7, 'deposits-withdrawals': {'soon': 5}}, 'deposits-withdrawals must map'),
    ({'birth-year': 1950, 'retirement-age': 65, 'return': 7}, 'nothing to project'),
])
def test_invalid_projection_exits_with_422(block, message, capsys):
    with pytest.raises(Exception, match='^422$'):
        parse_projection_cfg(block, ['portfolio'], 2026)
    assert message in capsys.readouterr().out

def test_imaginary_portfolios_local_and_cloud():
    assert parse_imaginary_portfolios([
        {'name': 'paper', 'source': 'local', 'transactions-dir': 'a.csv'},
        {'name': 'tech_2', 'source': 'cloud', 'shareable-address': 'sheet-id'},
    ]) == [ImaginaryPortfolioCfg('paper', True, 'a.csv'),
           ImaginaryPortfolioCfg('tech_2', False, 'sheet-id')]

@pytest.mark.parametrize('block, message', [
    ({'name': 'paper'}, "source must be 'local' or 'cloud'"),
    ({'name': 'paper', 'source': 'local'}, 'transactions-dir is required'),
    ({'name': 'a/b', 'source': 'local', 'transactions-dir': 'a.csv'}, 'must use only letters'),
    ({'name': 'portfolio', 'source': 'local', 'transactions-dir': 'a.csv'}, 'reserved'),
    ({'name': 'paper', 'source': 'local', 'transactions-dir': 'a.csv', 'dir': 'x'}, 'unknown keys'),
])
def test_invalid_imaginary_portfolio_exits_with_422(block, message, capsys):
    with pytest.raises(Exception, match='^422$'):
        parse_imaginary_portfolios([block])
    assert message in capsys.readouterr().out

def test_imaginary_portfolio_names_must_be_unique(capsys):
    entry = {'name': 'paper', 'source': 'local', 'transactions-dir': 'a.csv'}
    with pytest.raises(Exception, match='^422$'):
        parse_imaginary_portfolios([entry, entry])
    assert 'used twice' in capsys.readouterr().out

def test_positions_local_and_cloud(tmp_path):
    cfg = create_cfg(make_cfg(tmp_path, """
positions:
  source: local
  positions-dir: data/positions.csv
"""))
    assert cfg.get_param(ConfigMapUri.POSITIONS) == PositionsCfg(is_local=True, location='data/positions.csv')
    assert parse_positions({'source': 'cloud', 'shareable-address': 'sheet-id'}) == \
        PositionsCfg(is_local=False, location='sheet-id')

@pytest.mark.parametrize('block, message', [
    ({'positions-dir': 'a.csv'}, "positions: source must be 'local' or 'cloud'"),
    ({'source': 'cloud', 'positions-dir': 'a.csv'}, 'shareable-address is required'),
    ({'source': 'local', 'positions-dir': 'a.csv', 'file': 'b.csv'}, 'unknown keys in positions: file'),
    (['a.csv'], 'positions must be a mapping'),
])
def test_invalid_positions_block_exits_with_422(block, message, capsys):
    with pytest.raises(Exception, match='^422$'):
        parse_positions(block)
    assert message in capsys.readouterr().out

def write_source_cfg(tmp_path, transactions_source, symbols_standard, map_source):
    symbols_map = f"""
symbols-map:
  source: {map_source}
  shareable-address: made-up-map-sheet
""" if map_source else ''
    path = tmp_path / 'cfg.yml'
    path.write_text(f"""
market-data-origin: yahoo
comp:
  default-currency: USD
  history-variant: full
directories:
  generation-dir: out/
  log-dir: logs/
  transactions-dir: trans.csv
  symbols-map-dir: symbols.csv
transactions:
  source: {transactions_source}
  symbols-standard: {symbols_standard}
  shareable-address: made-up-trans-sheet
cli-exec:
  quiet: true
  log-level: debug
""" + symbols_map, encoding='utf-8')
    return path

SOURCE_KEYS = [ConfigMapUri.TRANSACTIONS_DIRECTORY, ConfigMapUri.TRANSACTIONS_SHEET,
               ConfigMapUri.SYMBOLS_MAP_SOURCE, ConfigMapUri.SYMBOLS_MAP_DIRECTORY,
               ConfigMapUri.SYMBOLS_MAP_SHEET]

@pytest.mark.parametrize('transactions_source, symbols_standard, map_source, expected', [
    ('local', 'custom', 'local', {ConfigMapUri.TRANSACTIONS_DIRECTORY: 'trans.csv',
                                  ConfigMapUri.SYMBOLS_MAP_SOURCE: 'local',
                                  ConfigMapUri.SYMBOLS_MAP_DIRECTORY: 'symbols.csv'}),
    ('local', 'custom', 'cloud', {ConfigMapUri.TRANSACTIONS_DIRECTORY: 'trans.csv',
                                  ConfigMapUri.SYMBOLS_MAP_SOURCE: 'cloud',
                                  ConfigMapUri.SYMBOLS_MAP_SHEET: 'made-up-map-sheet'}),
    ('cloud', 'custom', 'local', {ConfigMapUri.TRANSACTIONS_SHEET: 'made-up-trans-sheet',
                                  ConfigMapUri.SYMBOLS_MAP_SOURCE: 'local',
                                  ConfigMapUri.SYMBOLS_MAP_DIRECTORY: 'symbols.csv'}),
    ('cloud', 'custom', 'cloud', {ConfigMapUri.TRANSACTIONS_SHEET: 'made-up-trans-sheet',
                                  ConfigMapUri.SYMBOLS_MAP_SOURCE: 'cloud',
                                  ConfigMapUri.SYMBOLS_MAP_SHEET: 'made-up-map-sheet'}),
    # With Yahoo symbols the symbols-map block isn't read, so it can be left out.
    ('local', 'yahoo', None, {ConfigMapUri.TRANSACTIONS_DIRECTORY: 'trans.csv'}),
    ('cloud', 'yahoo', None, {ConfigMapUri.TRANSACTIONS_SHEET: 'made-up-trans-sheet'}),
])
def test_create_cfg_reads_only_the_keys_of_the_chosen_sources(
        tmp_path, transactions_source, symbols_standard, map_source, expected):
    cfg = create_cfg(write_source_cfg(tmp_path, transactions_source, symbols_standard, map_source))
    assert {key: cfg.get_param(key) for key in SOURCE_KEYS} == \
        {key: expected.get(key) for key in SOURCE_KEYS}

def test_create_cfg_common_keys(tmp_path):
    cfg = create_cfg(write_source_cfg(tmp_path, 'local', 'custom', 'local'))
    assert {key: cfg.get_param(key) for key in [
        ConfigMapUri.MARKET_ORIGIN, ConfigMapUri.DEFAULT_CURRENCY,
        ConfigMapUri.GENERATION_DIRECTORY, ConfigMapUri.LOG_DIRECTORY,
        ConfigMapUri.HISTORY_VARIANT, ConfigMapUri.TRANSACTIONS_SOURCE,
        ConfigMapUri.SYMBOLS_STANDARD, ConfigMapUri.LOG_LEVEL, ConfigMapUri.QUIET]} == {
        ConfigMapUri.MARKET_ORIGIN: 'yahoo', ConfigMapUri.DEFAULT_CURRENCY: 'USD',
        ConfigMapUri.GENERATION_DIRECTORY: 'out/', ConfigMapUri.LOG_DIRECTORY: 'logs/',
        ConfigMapUri.HISTORY_VARIANT: 'full', ConfigMapUri.TRANSACTIONS_SOURCE: 'local',
        ConfigMapUri.SYMBOLS_STANDARD: 'custom', ConfigMapUri.LOG_LEVEL: 'DEBUG',
        ConfigMapUri.QUIET: True}
