from typing import Literal, TypedDict

class MulticastConfig(TypedDict):
    group: str

class ControllerConfig(TypedDict):
    mc_port: int

class DronesConfig(TypedDict):
    num_drones: int
    mc_port: int

class SensorsConfig(TypedDict):
    max_range: int
    unit_of_measurement: Literal['m', 'mi', 'ft']

class SystemConfig(TypedDict):
    timeout: int

class SysConfig(TypedDict):
    multicast: MulticastConfig
    controller: ControllerConfig
    drones: DronesConfig
    sensors: SensorsConfig
    system: SystemConfig