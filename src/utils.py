import yaml
import socket
import pathlib
import argparse
from typing import Optional, Union

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Tracker info')
    parser.add_argument('--quiet', '-q', action='store_true', dest='is_quiet',
                        help='Hide detailed output')
    parser.add_argument('--cfg', type=pathlib.Path, dest='cfg_file',
                        default=pathlib.Path('config/cfg.yml'),
                        help='Path to the overall configuration file')
    parser.add_argument('--log-level', type=str, dest='log_level', default='info',
                        help='Log level [DEBUG | INFO | WARNING | ERROR | CRITICAL]')
    return parser.parse_args()

def check_internet(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False

def get_yaml_parameter(yaml_path: pathlib.Path,
                       parameter: Optional[str]=None) -> Union[str, dict]:
    param_val = None
    param_dict = {}
    with open(yaml_path, 'r') as stream:
        try:
            param_dict = yaml.safe_load(stream)
            if parameter:
                param_val = param_dict[parameter]
        except yaml.YAMLError as exc:
            print(exc)
    if not parameter:
        return param_dict
    return param_val
