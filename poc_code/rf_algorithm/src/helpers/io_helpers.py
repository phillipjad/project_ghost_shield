import json
import os

from utils.typings.helper_types import SysConfig, MulticastConfig, ControllerConfig, DronesConfig, SensorsConfig, SystemConfig


def load_config(path: str) -> dict[str, str | int | dict]:
    with open(os.path.abspath(path), 'r') as config:
        return json.load(config)

def load_system_config(path: str) -> tuple[MulticastConfig, ControllerConfig, DronesConfig, SensorsConfig, SystemConfig]:
    sys_con: SysConfig = load_config(path)
    return (sys_con['multicast'], sys_con['controller'], sys_con['drones'], sys_con['sensors'], sys_con['system'])