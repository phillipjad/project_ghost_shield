from enum import StrEnum
from types import MappingProxyType


ctrl_send_reg_msg="C_REG_MSG"

MSG_INT_STR_MAP: MappingProxyType = {
    0x00: "RESERVED_INVALID",
    0x01: "CURRENT_LOCATION",
    0x02: "MOVE_LOCATION",
    0x03: "ENABLE_JAMMER",
    0x04: "DISABLE_JAMMER",
    0x05: "ENABLE_RF_DECEPTION",
    0x06: "DISABLE_RF_DECEPTION",
    0x07: "CONTROLLER_ENABLE_REGISTRATION",
    0x08: "DRONE_CONFIRM_REGISTRATION"
}

MSG_STR_INT_MAP: MappingProxyType = reversed(MSG_INT_STR_MAP)

MSG_STR_E: StrEnum = StrEnum(
    "MSG_STR_E",
    {
        "RESERVED_INVALID": "RESERVED_INVALID",
        "CURRENT_LOCATION": "CURRENT_LOCATION",
        "MOVE_LOCATION": "MOVE_LOCATION"

    }
)
print(MSG_STR_E.RESERVED_INVALID)