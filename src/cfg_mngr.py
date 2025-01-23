from pathlib import Path

class CfgManager:
    def __init__(self, platform_cfg: dict = None, market_cfg: dict = None,
                 ex_rate_cfg: dict = None, def_currency: str = 'EUR') -> None:
        self.defCurrency = def_currency
        self.marketCfg = market_cfg
        self.exRateCfg = ex_rate_cfg
        self.platformCfg = platform_cfg

    def get_cfg(self) -> str:
        return f'Default Currency: {self.defCurrency},\n' + \
               f'Market Cfg: {self.marketCfg},\n' + \
               f'Ex Rate Cfg: {self.exRateCfg},\n' + \
               f'Platform Cfg: {self.platformCfg}'

    def update_cfg(self, **kwargs) -> None:
        self.defCurrency = kwargs.get('defCurrency', self.defCurrency)
        self.platformCfg = kwargs.get('platformCfg', self.platformCfg)

class Directories:

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
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

    def __init__(self, sheets_dict: dict, is_urls: bool=False) -> None:
        self.sheets_dict = {}
        self.sheets_dict_raw_refined = {}
        for key, value in sheets_dict.items():
            if isinstance(value, str):
                sheet_id = value
                if is_urls:
                    sheet_id = self.convert_sheet_url_to_id(value)
                self.sheets_dict[key] = self.convert_sheet_id_to_url(sheet_id)
                self.sheets_dict_raw_refined[key] = sheet_id
            elif isinstance(value, dict):
                self.sheets_dict_raw_refined[key] = {}
                for inner_key, inner_value in value.items():
                    if isinstance(inner_value, str):
                        sheet_id = inner_value
                        if is_urls:
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
