import os
import requests

def get_google_sheet(spreadsheet_id: str, outDir: str,
                     outFile: str) -> os.PathLike:
    os.makedirs(outDir, exist_ok = True)
    url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv'
    response = requests.get(url)
    if response.status_code == 200:
        filepath = os.path.join(outDir, outFile)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    else:
        print(f'Error downloading Google Sheet: {response.status_code}')
        raise Exception(f'Error downloading Google Sheet: {response.status_code}')

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
