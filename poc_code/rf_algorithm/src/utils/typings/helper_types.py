from typing import Literal, TypeAlias, TypedDict


class MulticastConfig(TypedDict):
    group: str
    # Format "<START_PORT><Delimiting colon><END_PORT>" .e.g. "8000:8080"
    mc_port_range: str


class ControllerConfig(TypedDict):
    id: str
    mc_port: int
    ip: str
    port: int


class DroneConfigT(TypedDict):
    id: str
    ip: str
    port: int


DronesConfig: TypeAlias = list[DroneConfigT]


class SensorsConfig(TypedDict):
    max_range: int
    unit_of_measurement: Literal["m", "mi", "ft"]


class SystemConfig(TypedDict):
    operation_ceiling: int
    timeout_s: int
    signing_key: str
    public_key: str


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
