"""Public Device domain service interface.

Contract mapping (Frozen Device Domain Contract V1.1):

Commands:
- CreateDevice -> create_device
- AssignDevice -> assign_device
- ReturnDevice -> return_device
- CreatePairing -> create_pairing
- RevokePairing -> revoke_pairing
- CreateDeviceCommand -> create_device_command
- DeliverCommand -> deliver_command
- StartCommandExecution -> start_command_execution
- CompleteCommand -> complete_command
- FailCommand -> fail_command
- CancelCommand -> cancel_command

Queries:
- GetDevice -> get_device
- GetDeviceState -> get_device_state
- GetAssignments -> get_assignments
- GetPairings -> get_pairings
- GetCompartments -> get_compartments
- GetCommands -> get_commands
- GetCommandStatus -> get_command_status
"""

from domains.device.services.assignments import assign_device, get_assignments, refurbish_device, return_device
from domains.device.services.commands import (
    cancel_command,
    complete_command,
    create_device_command,
    deliver_command,
    expire_command,
    fail_command,
    get_command,
    get_command_status,
    get_commands,
    start_command_execution,
)
from domains.device.services.compartments import (
    assign_compartment,
    create_compartment,
    get_compartment,
    get_compartments,
    record_compartment_closed,
    record_compartment_opened,
    release_compartment_assignment,
)
from domains.device.services.device_models import register_device_model
from domains.device.services.devices import (
    add_capability_override,
    create_device,
    get_device,
    get_device_state,
    get_effective_capability_state,
    update_device_state,
)
from domains.device.services.pairing import (
    activate_pairing,
    create_pairing,
    disconnect_pairing,
    get_pairing,
    get_pairings,
    revoke_pairing,
)

__all__ = [
    "activate_pairing",
    "add_capability_override",
    "assign_compartment",
    "assign_device",
    "cancel_command",
    "complete_command",
    "create_compartment",
    "create_device",
    "create_device_command",
    "create_pairing",
    "deliver_command",
    "disconnect_pairing",
    "expire_command",
    "fail_command",
    "get_assignments",
    "get_command",
    "get_command_status",
    "get_commands",
    "get_compartment",
    "get_compartments",
    "get_device",
    "get_device_state",
    "get_effective_capability_state",
    "get_pairing",
    "get_pairings",
    "record_compartment_closed",
    "record_compartment_opened",
    "refurbish_device",
    "register_device_model",
    "release_compartment_assignment",
    "return_device",
    "revoke_pairing",
    "start_command_execution",
    "update_device_state",
]
