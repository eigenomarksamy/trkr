from os import PathLike
from typing import Optional, Any
from src.utils import get_yaml_parameter

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

    def get_param(self, key: str) -> Any:
        return self.params.get(key)

def create_cfg(yml_file: PathLike) -> CfgManager:
    yml_dict = get_yaml_parameter(yml_file)
    conf = [
        CfgParam(name='market-origin', default='yahoo', value=yml_dict['market-data-origin']),
        CfgParam(name='def-currency', default='EUR', value=yml_dict['comp']['default-currency']),
        CfgParam(name='gen-dir', value=yml_dict['directories']['generation-dir']),
        CfgParam(name='log-dir', value=yml_dict['directories']['log-dir']),
        CfgParam(name='history-var', default='lite', value=yml_dict['comp']['history-variant']),
        CfgParam(name='trans-src', default='local', value=yml_dict['transactions']['source']),
        CfgParam(name='sym-std', default='yahoo', value=yml_dict['transactions']['symbols-standard'])
    ]
    params_obj = CfgParams(conf)
    if params_obj.get('trans-src') == 'local':
        conf = [
            CfgParam(name='trans-dir', value=yml_dict['directories']['transactions-dir'])
        ]
    elif params_obj.get('trans-src') == 'cloud':
        conf = [
            CfgParam(name='trans-sheet', value=yml_dict['transactions']['shareable-address'])
        ]
    params_obj.add(conf)
    if params_obj.get('sym-std') == 'custom':
        conf = [
            CfgParam(name='sym-map-src', value=yml_dict['symbols-map']['source'])
        ]
    params_obj.add(conf)
    if params_obj.get('sym-map-src') == 'local':
        conf = [
            CfgParam(name='sym-map-dir', value=yml_dict['directories']['symbols-map-dir'])
        ]
    elif params_obj.get('sym-map-src') == 'cloud':
        conf = [
            CfgParam(name='sym-map-sheet', value=yml_dict['symbols-map']['shareable-address'])
        ]
    params_obj.add(conf)
    return CfgManager(params_obj)

class ConfigManager:
    def __init__(self, platform_cfg: dict = None,
                 market_cfg: dict = None,
                 ex_rate_cfg: dict = None,
                 def_currency: str = 'EUR',
                 symbols_standard: str = 'custom',
                 history_variant: str = 'lite',
                 use_sheet_of_sheets: bool = False,
                 use_local_transactions: bool = False,
                 market_data_origin: str = 'yahoo',
                 generation_dir: PathLike = 'data/gen',
                 log_dir: PathLike = 'log/') -> None:
        self.defCurrency = def_currency
        self.marketCfg = market_cfg
        self.exRateCfg = ex_rate_cfg
        self.platformCfg = platform_cfg
        self.symbols_standard = symbols_standard
        self.history_variant = history_variant
        self.use_sheet_of_sheets = use_sheet_of_sheets
        self.use_local_transactions = use_local_transactions
        self.market_data_origin = market_data_origin
        self.generation_dir = generation_dir
        self.log_dir = log_dir

    def get_cfg(self) -> str:
        return f'Default Currency: {self.defCurrency}, ' + \
               f'Market Cfg: {self.marketCfg}, ' + \
               f'Ex Rate Cfg: {self.exRateCfg}, ' + \
               f'Platform Cfg: {self.platformCfg}, ' + \
               f'Symbols Standard: {self.symbols_standard}, ' + \
               f'History Variant: {self.history_variant}, ' + \
               f'Use Sheet of Sheets: {self.use_sheet_of_sheets}, ' + \
               f'Use Local Transactions: {self.use_local_transactions}, ' + \
               f'Market Data Origin: {self.market_data_origin}, ' + \
               f'Generation Dir: {self.generation_dir}, ' + \
               f'Log Dir: {self.log_dir}'

    def update_cfg(self, **kwargs) -> None:
        self.defCurrency = kwargs.get('defCurrency', self.defCurrency)
        self.defCurrency = kwargs.get('def_currency', self.defCurrency)
        self.platformCfg = kwargs.get('platformCfg', self.platformCfg)
        self.platformCfg = kwargs.get('platform_cfg', self.platformCfg)
        self.marketCfg = kwargs.get('marketCfg', self.marketCfg)
        self.marketCfg = kwargs.get('market_cfg', self.marketCfg)
        self.exRateCfg = kwargs.get('exRateCfg', self.exRateCfg)
        self.exRateCfg = kwargs.get('ex_rate_cfg', self.exRateCfg)
        self.symbols_standard = kwargs.get('symbols_standard', self.symbols_standard)
        self.history_variant = kwargs.get('history_variant', self.history_variant)
        self.use_sheet_of_sheets = kwargs.get('use_sheet_of_sheets', self.use_sheet_of_sheets)
        self.use_local_transactions = kwargs.get('use_local_transactions', self.use_local_transactions)
        self.market_data_origin = kwargs.get('market_data_origin', self.market_data_origin)
        self.generation_dir = kwargs.get('generation_dir', self.generation_dir)
        self.log_dir = kwargs.get('log_dir', self.log_dir)

    def get_param(self, param_name: str) -> Any:
        return getattr(self, param_name, None)

def build_config_manager(settings_conf_yml: PathLike) -> ConfigManager:
    return ConfigManager(def_currency=get_yaml_parameter(settings_conf_yml, "default-currency").upper(),
                         generation_dir=get_yaml_parameter(settings_conf_yml, 'generation-dir'),
                         history_variant=get_yaml_parameter(settings_conf_yml, 'history-variant').lower(),
                         market_data_origin=get_yaml_parameter(settings_conf_yml, 'market-data-origin').lower(),
                         use_local_transactions=get_yaml_parameter(settings_conf_yml, 'use-local-transactions'),
                         symbols_standard=get_yaml_parameter(settings_conf_yml, 'symbols-standard').lower(),
                         log_dir=get_yaml_parameter(settings_conf_yml, 'log-dir'))

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

class Sheets:

    def __init__(self, sheets_dict: dict) -> None:
        self.sheets_dict = {}
        self.sheets_dict_raw_refined = {}
        for key, value in sheets_dict.items():
            if isinstance(value, str):
                sheet_id = value
                if 'https://docs.google.com/spreadsheets/d/' in sheet_id:
                    sheet_id = self.convert_sheet_url_to_id(value)
                self.sheets_dict[key] = self.convert_sheet_id_to_url(sheet_id)
                self.sheets_dict_raw_refined[key] = sheet_id
            elif isinstance(value, dict):
                self.sheets_dict_raw_refined[key] = {}
                for inner_key, inner_value in value.items():
                    if isinstance(inner_value, str):
                        sheet_id = inner_value
                        if 'https://docs.google.com/spreadsheets/d/' in sheet_id:
                            sheet_id = self.convert_sheet_url_to_id(inner_value)
                        self.sheets_dict[f'{key}:{inner_key}'] = self.convert_sheet_id_to_url(sheet_id)
                        self.sheets_dict_raw_refined[key][inner_key] = sheet_id

    @staticmethod
    def convert_sheet_id_to_url(sheet_id: str) -> str:
        return f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing'

    @staticmethod
    def convert_sheet_url_to_id(url: str) -> str:
        return url.split('/d/')[1].split('/')[0]

    def get_sheets_links(self) -> dict:
        return self.sheets_dict

    def get_sheets_ids(self) -> dict:
        return self.sheets_dict_raw_refined
