from os import PathLike
from typing import Optional, Any
from src.utils import get_yaml_parameter

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
