import re
from os import PathLike
from datetime import date
from dataclasses import dataclass
from typing import Optional, Any
from src.utils import get_yaml_parameter
from src.projection import ProjectionCfg

class ConfigMapUri:
    MARKET_ORIGIN = 'market-origin'
    DEFAULT_CURRENCY = 'def-currency'
    GENERATION_DIRECTORY = 'gen-dir'
    LOG_DIRECTORY = 'log-dir'
    HISTORY_VARIANT = 'history-var'
    TRANSACTIONS_SOURCE = 'trans-src'
    SYMBOLS_STANDARD = 'sym-std'
    TRANSACTIONS_DIRECTORY = 'trans-dir'
    TRANSACTIONS_SHEET = 'trans-sheet'
    SYMBOLS_MAP_SOURCE = 'sym-map-src'
    SYMBOLS_MAP_DIRECTORY = 'sym-map-dir'
    SYMBOLS_MAP_SHEET = 'sym-map-sheet'
    LOG_LEVEL = 'log-level'
    QUIET = 'quiet'
    IMAGINARY_PORTFOLIOS = 'imaginary'
    PROJECTION = 'projection'
    POSITIONS = 'positions'

@dataclass
class ImaginaryPortfolioCfg:
    name: str
    is_local: bool
    # The transactions file for a local source, the sheet address for a cloud one.
    location: str

@dataclass
class PositionsCfg:
    is_local: bool
    # The positions file for a local source, the sheet address for a cloud one.
    location: str

# YAML key -> ProjectionCfg field
PROJECTION_KEYS = {
    'birth-year': 'birth_year',
    'retirement-age': 'retirement_age',
    'return': 'yearly_return',
    'start-net-worth': 'start_net_worth',
    'cash': 'cash',
    'income': 'income',
    'income-growth': 'income_growth',
    'invest-percent': 'invest_percent',
    'fees': 'fees',
    'inflation': 'inflation',
    'deposits-withdrawals': 'deposits_withdrawals',
}

def config_error(message: str) -> Exception:
    print(f'Configuration error: {message}')
    return Exception("422")

def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def parse_imaginary_portfolios(block: Optional[list]) -> list[ImaginaryPortfolioCfg]:
    if block is None:
        return []
    if not isinstance(block, list):
        raise config_error('imaginary-portfolios must be a list.')
    portfolios = []
    for entry in block:
        if not isinstance(entry, dict):
            raise config_error('each imaginary-portfolios entry must be a mapping.')
        unknown = set(entry) - {'name', 'source', 'transactions-dir', 'shareable-address'}
        if unknown:
            raise config_error(f'unknown keys in imaginary-portfolios: {", ".join(sorted(unknown))}.')
        name = entry.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise config_error(f'imaginary portfolio name {name!r} must use only letters, digits, "-" and "_".')
        if name == 'portfolio':
            raise config_error("imaginary portfolio name 'portfolio' is reserved for the real portfolio.")
        if name in [portfolio.name for portfolio in portfolios]:
            raise config_error(f"imaginary portfolio name '{name}' is used twice.")
        is_local, location = parse_source(entry, 'transactions-dir', f"imaginary portfolio '{name}'")
        portfolios.append(ImaginaryPortfolioCfg(name=name, is_local=is_local, location=location))
    return portfolios

def parse_positions(block: Optional[dict]) -> Optional[PositionsCfg]:
    if block is None:
        return None
    if not isinstance(block, dict):
        raise config_error('positions must be a mapping.')
    unknown = set(block) - {'source', 'positions-dir', 'shareable-address'}
    if unknown:
        raise config_error(f'unknown keys in positions: {", ".join(sorted(unknown))}.')
    is_local, location = parse_source(block, 'positions-dir', 'positions')
    return PositionsCfg(is_local=is_local, location=location)

def parse_source(block: dict, local_key: str, context: str) -> tuple[bool, str]:
    """Reads 'source: local' with a file under local_key, or 'source: cloud' with a sheet address."""
    source = block.get('source')
    if source == 'local':
        location_key = local_key
    elif source == 'cloud':
        location_key = 'shareable-address'
    else:
        raise config_error(f"{context}: source must be 'local' or 'cloud'.")
    if not block.get(location_key):
        raise config_error(f"{context}: {location_key} is required for source '{source}'.")
    return source == 'local', str(block[location_key])

def parse_projection_cfg(block: Optional[dict], portfolio_names: list[str],
                         current_year: int) -> Optional[ProjectionCfg]:
    if block is None:
        return None
    if not isinstance(block, dict):
        raise config_error('projection must be a mapping.')
    unknown = set(block) - set(PROJECTION_KEYS)
    if unknown:
        raise config_error(f'unknown keys in projection: {", ".join(sorted(unknown))}.')
    # An empty value (e.g. "inflation:") means the key is not set.
    block = {key: value for key, value in block.items() if value is not None}
    for key in ('birth-year', 'retirement-age', 'return'):
        if key not in block:
            raise config_error(f'projection: {key} is required.')
    for key, value in block.items():
        if key not in ('start-net-worth', 'deposits-withdrawals') and not is_number(value):
            raise config_error(f'projection: {key} must be a number, not {value!r}.')
    for key in ('birth-year', 'retirement-age'):
        if not isinstance(block[key], int):
            raise config_error(f'projection: {key} must be a whole number.')
    start = block.get('start-net-worth', 'portfolio')
    if not is_number(start) and start not in portfolio_names:
        raise config_error("projection: start-net-worth must be a number, 'portfolio' or "
                           f"an imaginary portfolio's name, not {start!r}.")
    if not 0 <= block.get('invest-percent', 0) <= 100:
        raise config_error('projection: invest-percent must be between 0 and 100.')
    if block.get('fees', 0) < 0:
        raise config_error('projection: fees must not be negative.')
    for key in ('return', 'income-growth', 'inflation'):
        if block.get(key, 0) <= -100:
            raise config_error(f'projection: {key} must be above -100.')
    plan = {}
    try:
        for year, amount in block.get('deposits-withdrawals', {}).items():
            if not is_number(amount):
                raise ValueError(amount)
            plan[int(year)] = amount
    except (AttributeError, ValueError):
        raise config_error('projection: deposits-withdrawals must map calendar years to amounts.')
    block['deposits-withdrawals'] = plan
    if block['birth-year'] + block['retirement-age'] <= current_year:
        raise config_error('projection: retirement-age is reached this year or earlier, '
                           'so there is nothing to project.')
    return ProjectionCfg(**{PROJECTION_KEYS[key]: value for key, value in block.items()})

class CfgParam:

    def __init__(self, name: str, default: Optional[Any]=None,
                 value: Optional[Any]=None) -> None:
        self.name = name
        self.value = value if value else default

class CfgParams:

    def __init__(self, cfg: list[CfgParam]) -> None:
        self.params = {}
        for name in cfg:
            self.params[name.name] = name.value

    def add(self, cfg: list[CfgParam]) -> None:
        for name in cfg:
            self.params[name.name] = name.value

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if key in self.params:
                self.params[key] = value

    def get(self, key: str) -> Any:
        return self.params.get(key)

    def to_str(self) -> str:
        ret = ''
        for key, value in self.params.items():
            ret += f'{key}: {value}  '
        return ret

class CfgManager:

    def __init__(self, cfg_params: CfgParams) -> None:
        self.params = cfg_params

    def print(self) -> None:
        print(self.params.to_str())

    def to_str(self) -> str:
        return self.params.to_str()

    def get_param(self, key: str) -> Any:
        return self.params.get(key)

def create_cfg(yml_file: PathLike) -> CfgManager:
    yml_dict = get_yaml_parameter(yml_file)
    conf = [
        CfgParam(name=ConfigMapUri.MARKET_ORIGIN, default='yahoo', value=yml_dict['market-data-origin']),
        CfgParam(name=ConfigMapUri.DEFAULT_CURRENCY, default='EUR', value=yml_dict['comp']['default-currency']),
        CfgParam(name=ConfigMapUri.GENERATION_DIRECTORY, value=yml_dict['directories']['generation-dir']),
        CfgParam(name=ConfigMapUri.LOG_DIRECTORY, value=yml_dict['directories']['log-dir']),
        CfgParam(name=ConfigMapUri.HISTORY_VARIANT, default='lite', value=yml_dict['comp']['history-variant']),
        CfgParam(name=ConfigMapUri.TRANSACTIONS_SOURCE, default='local', value=yml_dict['transactions']['source']),
        CfgParam(name=ConfigMapUri.SYMBOLS_STANDARD, default='yahoo', value=yml_dict['transactions']['symbols-standard']),
        CfgParam(name=ConfigMapUri.LOG_LEVEL, default='NOTSET', value=yml_dict['cli-exec']['log-level'].upper()),
        CfgParam(name=ConfigMapUri.QUIET, default=False, value=yml_dict['cli-exec']['quiet'])
    ]
    params_obj = CfgParams(conf)
    conf.clear()
    if params_obj.get(ConfigMapUri.TRANSACTIONS_SOURCE) == 'local':
        conf = [
            CfgParam(name=ConfigMapUri.TRANSACTIONS_DIRECTORY, value=yml_dict['directories']['transactions-dir'])
        ]
    elif params_obj.get(ConfigMapUri.TRANSACTIONS_SOURCE) == 'cloud':
        conf = [
            CfgParam(name=ConfigMapUri.TRANSACTIONS_SHEET, value=yml_dict['transactions']['shareable-address'])
        ]
    params_obj.add(conf)
    conf.clear()
    if params_obj.get(ConfigMapUri.SYMBOLS_STANDARD) == 'custom':
        conf = [
            CfgParam(name=ConfigMapUri.SYMBOLS_MAP_SOURCE, value=yml_dict['symbols-map']['source'])
        ]
    params_obj.add(conf)
    conf.clear()
    if params_obj.get(ConfigMapUri.SYMBOLS_STANDARD) == 'custom' and params_obj.get(ConfigMapUri.SYMBOLS_MAP_SOURCE) == 'local':
        conf = [
            CfgParam(name=ConfigMapUri.SYMBOLS_MAP_DIRECTORY, value=yml_dict['directories']['symbols-map-dir'])
        ]
    elif params_obj.get(ConfigMapUri.SYMBOLS_STANDARD) == 'custom' and params_obj.get(ConfigMapUri.SYMBOLS_MAP_SOURCE) == 'cloud':
        conf = [
            CfgParam(name=ConfigMapUri.SYMBOLS_MAP_SHEET, value=yml_dict['symbols-map']['shareable-address'])
        ]
    params_obj.add(conf)
    conf.clear()
    # These blocks are optional, so configs written before them keep working.
    imaginary = parse_imaginary_portfolios(yml_dict.get('imaginary-portfolios'))
    conf = [
        CfgParam(name=ConfigMapUri.POSITIONS, value=parse_positions(yml_dict.get('positions'))),
        CfgParam(name=ConfigMapUri.IMAGINARY_PORTFOLIOS, default=[], value=imaginary),
        CfgParam(name=ConfigMapUri.PROJECTION,
                 value=parse_projection_cfg(yml_dict.get('projection'),
                                            ['portfolio'] + [p.name for p in imaginary],
                                            date.today().year))
    ]
    params_obj.add(conf)
    conf.clear()
    return CfgManager(params_obj)

class Directories:

    def __init__(self, base_dir: str, log_dir: Optional[str],
                 local_trans_dir: Optional[str]=None,
                 local_map_dir: Optional[str]=None) -> None:
        self.log_dir = log_dir if log_dir else 'log/'
        self.base_dir = base_dir
        self.local_trans_dir = local_trans_dir if local_trans_dir else base_dir
        self.local_map_dir = local_map_dir if local_map_dir else base_dir
        self.sheets_dir = self.base_dir + 'sheets/'
        self.market_data_dir = self.sheets_dir + 'market/'
        self.history_dir = self.market_data_dir + 'history/'
        self.history_lite_dir = self.history_dir + 'lite/'
        self.history_full_dir = self.history_dir + 'full/'
        self.generated_dir = self.base_dir + 'generated/'
        self.gen_portfolio_file = self.generated_dir + 'portfolio.csv'
        self.gen_entries_file = self.generated_dir + 'entries.md'
        self.gen_total_file = self.generated_dir + 'total.md'
        self.gen_sheets_urls_file = self.generated_dir + 'sheets_urls.md'
        self.plots_dir = self.generated_dir + 'plots/'
        self.plots_stocks_dir = self.plots_dir + 'stocks/'
        self.gen_plots_history = self.plots_stocks_dir + 'history.png'
        self.gen_plots_stats = self.plots_dir + 'gen_stats.png'
        self.gen_projection_csv = self.generated_dir + 'projection.csv'
        self.gen_projection_md = self.generated_dir + 'projection.md'
        self.gen_plots_projection = self.plots_dir + 'projection.png'
        self.imaginary_dir = self.base_dir + 'imaginary/'
