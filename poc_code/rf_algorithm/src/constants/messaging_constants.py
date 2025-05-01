# ruff: noqa: N801
"""message_constants.py
    Defines the message ID mappings and enum for message types used in communication.
    Provides both int-to-str and str-to-int mappings as well as a string enum class.
    """
from enum import StrEnum
from types import MappingProxyType

#: Mapping from integer message IDs to their corresponding string message types.
#: Used when decoding received message IDs into human-readable command names.
MSG_INT_STR_MAP: MappingProxyType[int, str] = {
    0x00: "RESERVED_INVALID",
    0x01: "CURRENT_LOCATION",
    0x02: "MOVE_LOCATION",
    0x03: "ENABLE_JAMMER",
    0x04: "DISABLE_JAMMER",
    0x05: "ENABLE_RF_DECEPTION",
    0x06: "DISABLE_RF_DECEPTION",
    0x07: "ENABLE_REGISTRATION",
    0x08: "CONFIRM_REGISTRATION",
    0x09: "GET_LOCATION",
    0x0A: "COMMAND_ACK",
    0x0B: "JAMMER_ENABLED",
    0x0C: "JAMMER_DISABLED",
}

#: Mapping from string message types to their corresponding integer message IDs.
#: Used when encoding string commands into message IDs for transmission.
MSG_STR_INT_MAP: MappingProxyType[str, int] = {
    "RESERVED_INVALID": 0x00,
    "CURRENT_LOCATION": 0x01,
    "MOVE_LOCATION": 0x02,
    "ENABLE_JAMMER": 0x03,
    "DISABLE_JAMMER": 0x04,
    "ENABLE_RF_DECEPTION": 0x05,
    "DISABLE_RF_DECEPTION": 0x06,
    "ENABLE_REGISTRATION": 0x07,
    "CONFIRM_REGISTRATION": 0x08,
    "GET_LOCATION": 0x09,
    "COMMAND_ACK": 0x0A,
    "JAMMER_ENABLED": 0x0B,
    "JAMMER_DISABLED": 0x0C,
}


class MSG_STR_E(StrEnum):
    """
    Enum of valid string message types.

    This provides a type-safe way to refer to string-based command names
    across the system and can be used instead of raw strings for better
    consistency and code completion in IDEs.
    """
    RESERVED_INVALID = "RESERVED_INVALID"
    CURRENT_LOCATION = "CURRENT_LOCATION"
    MOVE_LOCATION = "MOVE_LOCATION"
    ENABLE_JAMMER = "ENABLE_JAMMER"
    DISABLE_JAMMER = "DISABLE_JAMMER"
    ENABLE_RF_DECEPTION = "ENABLE_RF_DECEPTION"
    DISABLE_RF_DECEPTION = "DISABLE_RF_DECEPTION"
    ENABLE_REGISTRATION = "ENABLE_REGISTRATION"
    CONFIRM_REGISTRATION = "CONFIRM_REGISTRATION"
    GET_LOCATION = "GET_LOCATION"
    COMMAND_ACK = "COMMAND_ACK"
    JAMMER_ENABLED = "JAMMER_ENABLED"
    JAMMER_DISABLED = "JAMMER_DISABLED"
