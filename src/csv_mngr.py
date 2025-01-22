import csv
import pathlib
from typing import Any, Iterable

class CsvMngr:
    def __init__(self, file_path: pathlib.Path,
                 headers: list[str]) -> None:
        self.file_path = file_path
        self.headers = headers

    def read(self) -> list:
        with open(self.file_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            ret = [dict(zip(self.headers, row)) for row in rows]
            ret.pop(0)
            return ret

    def write(self, data: Iterable[Iterable[Any]]):
        with open(self.file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)
            writer.writerows(data)

def write_markdown_table(path: pathlib.Path, title: str,
                         col1_title: str, col2_title: str,
                         writable_dict: dict) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode='w', newline='') as file:
        file.write(f'# {title}\n\n')
        file.write(f'| {col1_title} | {col2_title} |\n')
        file.write('|--------|-------|\n')
        for key, value in writable_dict.items():
            file.write(f'| {key} | {value} |\n')

def write_markdown_urls(path: pathlib.Path, title: str,
                        writable_dict: dict) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode='w', newline='') as file:
        file.write(f'# {title}\n\n')
        for key, value in writable_dict.items():
            file.write(f'* [{key}]({value})\n')

def write_csv_lazy(path: pathlib.Path, data_dict: dict, key: str) -> None:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode='w', newline='') as file:
        writer = csv.writer(file)
        headers = [f'{key}'] + list(next(iter(data_dict.values())).keys())
        writer.writerow(headers)
        for symbol, data in data_dict.items():
            row = [symbol] + list(data.values())
            writer.writerow(row)
