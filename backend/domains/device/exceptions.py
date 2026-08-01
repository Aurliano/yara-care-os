"""Device domain exceptions."""


class DeviceError(Exception):
    """Base exception for Device domain errors."""


class DeviceNotFoundError(DeviceError):
    """Raised when a device cannot be found."""


class DeviceModelNotFoundError(DeviceError):
    """Raised when a device model cannot be found."""


class DeviceCommandNotFoundError(DeviceError):
    """Raised when a device command cannot be found."""


class InvalidDeviceStateError(DeviceError):
    """Raised when an operation conflicts with current device state."""


class InvalidCommandStateError(DeviceError):
    """Raised when a command transition is not allowed."""


class CapabilityNotFoundError(DeviceError):
    """Raised when a capability is not defined on the device model."""


class InvalidCapabilityOverrideError(DeviceError):
    """Raised when a capability override is invalid."""


class AssignmentNotFoundError(DeviceError):
    """Raised when a device assignment cannot be found."""


class PairingNotFoundError(DeviceError):
    """Raised when a pairing cannot be found."""


class CompartmentNotFoundError(DeviceError):
    """Raised when a compartment cannot be found."""


class EntitlementDeniedError(DeviceError):
    """Raised when licensing entitlement blocks an operation."""


class CompartmentAssignmentError(DeviceError):
    """Raised when compartment assignment rules are violated."""
