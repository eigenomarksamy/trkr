import os
import re

import requests

# A link copied from the browser's address bar, to a sheet or to one of its tabs (gid).
SHEET_LINK = re.compile(
    r'https://docs\.google\.com/spreadsheets/(?:u/\d+/)?d/([\w-]+)'
    r'(?:/(?:edit|view|htmlview)?)?(?:\?[^#]*)?(?:#.*)?'
)
TAB_ID = re.compile(r'[?&#]gid=(\d+)')


def sheet_export_url(address: str) -> str:
    """The CSV export URL for a sheet ID, or for a browser link to a sheet or one of its tabs.

    Any other https address, such as an export or publish-to-web link, is used as it is.
    """
    if not Sheets.is_url(address):
        return f'https://docs.google.com/spreadsheets/d/{address}/export?format=csv'
    link = SHEET_LINK.fullmatch(address)
    if not link:
        return address
    url = f'https://docs.google.com/spreadsheets/d/{link.group(1)}/export?format=csv'
    tab = TAB_ID.search(address)
    return f'{url}&gid={tab.group(1)}' if tab else url


def get_google_sheet(spreadsheet_id: str, outDir: str, outFile: str) -> os.PathLike:
    os.makedirs(outDir, exist_ok=True)
    url = sheet_export_url(spreadsheet_id)
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
    def __init__(self, sheets_dict: dict) -> None:
        self.sheets_dict = {}
        self.sheets_dict_raw_refined = {}
        for key, value in sheets_dict.items():
            if isinstance(value, str):
                sheet_id = value
                if self.is_url(sheet_id):
                    sheet_id = self.convert_sheet_url_to_id(value)
                self.sheets_dict[key] = self.convert_sheet_id_to_url(sheet_id)
                self.sheets_dict_raw_refined[key] = sheet_id
            elif isinstance(value, dict):
                self.sheets_dict_raw_refined[key] = {}
                for inner_key, inner_value in value.items():
                    if isinstance(inner_value, str):
                        sheet_id = inner_value
                        if self.is_url(sheet_id):
                            sheet_id = self.convert_sheet_url_to_id(inner_value)
                        self.sheets_dict[f'{key}:{inner_key}'] = self.convert_sheet_id_to_url(
                            sheet_id
                        )
                        self.sheets_dict_raw_refined[key][inner_key] = sheet_id

    @staticmethod
    def convert_sheet_id_to_url(sheet_id: str) -> str:
        return f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing'

    @staticmethod
    def convert_sheet_url_to_id(url: str) -> str:
        return url.split('/d/')[1].split('/')[0]

    @staticmethod
    def is_url(text: str) -> bool:
        if 'https://' in text:
            return True
        return False

    def get_sheets_links(self) -> dict:
        return self.sheets_dict

    def get_sheets_ids(self) -> dict:
        return self.sheets_dict_raw_refined
