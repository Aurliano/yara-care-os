"""Device API views."""

import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from domains.device.api.serializers import (
    AssignDeviceSerializer,
    DeviceAssignmentSerializer,
    DeviceCommandCreateSerializer,
    DeviceCommandFailSerializer,
    DeviceCommandResultSerializer,
    DeviceCommandSerializer,
    DeviceCreateSerializer,
    DeviceSerializer,
    PairingCreateSerializer,
    PairingSerializer,
    CompartmentSerializer,
)
from domains.device.exceptions import (
    DeviceCommandNotFoundError,
    DeviceError,
    DeviceNotFoundError,
    InvalidCommandStateError,
    InvalidDeviceStateError,
    PairingNotFoundError,
)
from domains.device.services.assignments import assign_device, get_assignments, return_device
from domains.device.services.commands import (
    cancel_command,
    complete_command,
    create_device_command,
    deliver_command,
    fail_command,
    get_command,
    get_command_status,
    get_commands,
    start_command_execution,
)
from domains.device.services.compartments import get_compartments
from domains.device.services.devices import create_device, get_device, get_device_state
from domains.device.services.pairing import create_pairing, get_pairings, revoke_pairing


def _device_error_response(exc: DeviceError) -> Response:
    if isinstance(exc, (InvalidDeviceStateError, InvalidCommandStateError)):
        code = status.HTTP_409_CONFLICT
    elif isinstance(exc, (DeviceNotFoundError, DeviceCommandNotFoundError, PairingNotFoundError)):
        code = status.HTTP_404_NOT_FOUND
    else:
        code = status.HTTP_400_BAD_REQUEST
    return Response({"detail": str(exc)}, status=code)


class DeviceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = DeviceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            device = create_device(**serializer.validated_data)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED)


class DeviceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        try:
            device = get_device(device_id)
        except DeviceNotFoundError as exc:
            return _device_error_response(exc)
        return Response(DeviceSerializer(device).data)


class DeviceStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        try:
            return Response(get_device_state(device_id))
        except DeviceNotFoundError as exc:
            return _device_error_response(exc)


class DeviceAssignmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        assignments = get_assignments(device_id=device_id)
        return Response(DeviceAssignmentSerializer(assignments, many=True).data)

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        serializer = AssignDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = assign_device(device_id=device_id, **serializer.validated_data)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class DeviceReturnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        try:
            assignment = return_device(device_id=device_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceAssignmentSerializer(assignment).data)


class DevicePairingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        pairings = get_pairings(device_id=device_id)
        return Response(PairingSerializer(pairings, many=True).data)

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        serializer = PairingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pairing = create_pairing(
                hub_device_id=device_id,
                peripheral_device_id=serializer.validated_data["peripheral_device_id"],
            )
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(PairingSerializer(pairing).data, status=status.HTTP_201_CREATED)


class PairingRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pairing_id: uuid.UUID) -> Response:
        try:
            pairing = revoke_pairing(pairing_id=pairing_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(PairingSerializer(pairing).data)


class DeviceCompartmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        compartments = get_compartments(device_id=device_id)
        return Response(CompartmentSerializer(compartments, many=True).data)


class DeviceCommandsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        commands = get_commands(device_id=device_id)
        return Response(DeviceCommandSerializer(commands, many=True).data)

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        serializer = DeviceCommandCreateSerializer(data={**request.data, "target_device_id": str(device_id)})
        serializer.is_valid(raise_exception=True)
        try:
            command = create_device_command(**serializer.validated_data)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data, status=status.HTTP_201_CREATED)


class CommandDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, command_id: uuid.UUID) -> Response:
        try:
            command = get_command(command_id)
        except DeviceCommandNotFoundError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, command_id: uuid.UUID) -> Response:
        try:
            return Response(get_command_status(command_id))
        except DeviceCommandNotFoundError as exc:
            return _device_error_response(exc)


class CommandDeliverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        try:
            command = deliver_command(command_id=command_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        try:
            command = start_command_execution(command_id=command_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        serializer = DeviceCommandResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            command = complete_command(command_id=command_id, **serializer.validated_data)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandFailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        serializer = DeviceCommandFailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            command = fail_command(command_id=command_id, **serializer.validated_data)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        try:
            command = cancel_command(command_id=command_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)
