from typing import Literal, TypedDict


class MulticastConfig(TypedDict):
    group: str
    # Format "<START_PORT><Delimiting colon><END_PORT>" .e.g. "8000:8080"
    mc_port_range: str


class ControllerConfig(TypedDict):
    id: str
    mc_port: int


class DroneConfigT(TypedDict):
    id: str

class DronesConfig(TypedDict):
    drones: list[DroneConfigT]


class SensorsConfig(TypedDict):
    max_range: int
    unit_of_measurement: Literal["m", "mi", "ft"]


class SystemConfig(TypedDict):
    timeout_s: int
    signing_key: str


class FieldConfig(TypedDict):
    x: float
    y: float
    z: float


class SysConfig(TypedDict):
    multicast: MulticastConfig
    controller: ControllerConfig
    drones: DronesConfig
    sensors: SensorsConfig
    system: SystemConfig
    field: FieldConfig
