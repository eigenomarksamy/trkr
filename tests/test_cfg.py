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
