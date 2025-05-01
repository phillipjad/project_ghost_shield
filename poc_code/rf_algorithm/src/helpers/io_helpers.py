"""
IO helpers for loading configuration files.

This module provides functions to load system configuration files from a JSON file
and parsing it into the appropriate structures for the RF algorithm controller and drone processes.
"""
import json
import os

from utils.typings.helper_types import (
    ControllerConfig,
    DronesConfig,
    FieldConfig,
    MulticastConfig,
    SensorsConfig,
    SysConfig,
    SystemConfig,
)


def load_config(path: str) -> dict[str, str | int | dict]:
    """
    Load a raw JSON configuration file and return it as a flat dictionary.

    Args:
        path (str): Relative or absolute path to the JSON config file.

    Returns:
        dict[str, str | int | dict]: Parsed JSON content as a dictionary.
    """
    with open(os.path.abspath(path)) as config:
        return json.load(config)

def load_system_config(
    path: str,
) -> tuple[
    MulticastConfig,
    ControllerConfig,
    DronesConfig,
    SensorsConfig,
    SystemConfig,
    FieldConfig,
]:
    """
    Load and unpack a full system configuration from a JSON file.

    Args:
        path (str): Path to the system configuration JSON file.

    Returns:
        tuple: A tuple of config components in this order:
            - MulticastConfig: Multicast socket settings
            - ControllerConfig: Controller node information
            - DronesConfig: Configuration list for all drone nodes
            - SensorsConfig: Sensor node definitions
            - SystemConfig: Global system behavior settings
            - FieldConfig: Field/environment geometry
    """
    sys_con: SysConfig = load_config(path)
    return (
        sys_con["multicast"],
        sys_con["controller"],
        sys_con["drones"],
        sys_con["sensors"],
        sys_con["system"],
        sys_con["field"],
    )
