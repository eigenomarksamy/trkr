import argparse
import pathlib
import socket
import traceback
from typing import Optional, Union

import yaml


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Tracker info')
    # Both default to None, so the config's cli-exec block applies unless they are given.
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        default=None,
        dest='is_quiet',
        help='Hide detailed output (overrides cli-exec: quiet)',
    )
    parser.add_argument(
        '--cfg',
        type=pathlib.Path,
        dest='cfg_file',
        default=pathlib.Path('config/cfg.yml'),
        help='Path to the overall configuration file',
    )
    parser.add_argument(
        '--log-level',
        type=str.upper,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NOTSET'],
        dest='log_level',
        default=None,
        help='Log level, NOTSET for no log file (overrides cli-exec: log-level)',
    )
    return parser.parse_args()


def check_internet(host='8.8.8.8', port=53, timeout=3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError as ex:
        print(ex)
        return False


def get_yaml_parameter(
    yaml_path: pathlib.Path, parameter: Optional[str] = None
) -> Union[str, dict]:
    param_val = None
    param_dict = {}
    with open(yaml_path, 'r', encoding='utf-8-sig') as stream:
        try:
            param_dict = yaml.safe_load(stream)
            if parameter:
                param_val = param_dict[parameter]
        except yaml.YAMLError as exc:
            print(exc)
    if not parameter:
        return param_dict
    return param_val


def get_exit_status(error: Exception) -> tuple[int, str]:
    """The exit code and name for an error raised as Exception('<code>').

    Anything else is a crash: its traceback is printed and the exit code is 1.
    """
    if type(error) is Exception:
        try:
            code = int(str(error))
        except ValueError:
            pass
        else:
            return code, get_exception(code)
    traceback.print_exception(error)
    return 1, 'UnexpectedError'


def get_exception(e_num: int) -> str:
    e_map = {
        400: 'InvalidInputData',
        503: 'ServiceNotAvailable',
        299: 'DeprecatedAPI',
        417: 'UnsupportedConfiguration',
        422: 'InvalidConfiguration',
    }
    return e_map.get(e_num, 'NotMapped')
