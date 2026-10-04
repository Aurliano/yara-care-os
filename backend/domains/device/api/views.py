"""Device API views."""

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.device.api.serializers import (
    AssignDeviceSerializer,
    DeviceAssignmentSerializer,
    DeviceCommandCreateSerializer,
    DeviceCommandFailSerializer,
    DeviceCommandResultSerializer,
    DeviceCommandSerializer,
    DeviceCreateSerializer,
    DeviceSerializer,
    ElderAssignedDeviceSerializer,
    PairingCreateSerializer,
    PairingSerializer,
    CompartmentSerializer,
)
from domains.device.exceptions import (
    AssignmentNotFoundError,
    CapabilityNotFoundError,
    CompartmentNotFoundError,
    DeviceCommandNotFoundError,
    DeviceError,
    DeviceModelNotFoundError,
    DeviceNotFoundError,
    InvalidCommandStateError,
    InvalidDeviceStateError,
    PairingNotFoundError,
)
from domains.device.services.assignments import (
    assign_device,
    get_assignments,
    list_elder_assigned_devices,
    return_device,
)
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
from domains.device.enums import AssignmentStatus
from domains.device.models import Device, DeviceAssignment, DeviceCommand, Pairing
from domains.device.services.compartments import get_compartments
from domains.device.services.devices import create_device, get_device, get_device_state
from domains.device.services.pairing import create_pairing, get_pairings, revoke_pairing
from domains.identity_access.api.permissions import HasElderAccess
from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can, user_is_associated_with_elder


def _device_error_response(exc: DeviceError) -> Response:
    return domain_error_response(
        exc,
        base_type=DeviceError,
        not_found=(
            DeviceNotFoundError,
            DeviceCommandNotFoundError,
            PairingNotFoundError,
            CompartmentNotFoundError,
            AssignmentNotFoundError,
            DeviceModelNotFoundError,
            CapabilityNotFoundError,
        ),
        conflict=(InvalidDeviceStateError, InvalidCommandStateError),
    )


def _get_elder_for_device(device_id: uuid.UUID) -> Elder | None:
    assignment = (
        DeviceAssignment.objects.filter(
            device_id=device_id,
            status=AssignmentStatus.ASSIGNED,
        )
        .select_related("elder")
        .first()
    )
    if assignment:
        return assignment.elder
    latest = (
        DeviceAssignment.objects.filter(device_id=device_id)
        .select_related("elder")
        .order_by("-assigned_at")
        .first()
    )
    return latest.elder if latest else None


def _check_device_access(user, device_id: uuid.UUID) -> tuple[Device | None, Elder | None, Response | None]:
    try:
        device = get_device(device_id)
    except DeviceNotFoundError as exc:
        return None, None, _device_error_response(exc)

    elder = _get_elder_for_device(device_id)
    if elder is None or not user_is_associated_with_elder(user, elder):
        return None, None, Response(
            {"detail": "You do not have access to this device's elder."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return device, elder, None


def _check_command_access(user, command_id: uuid.UUID) -> tuple[DeviceCommand | None, Response | None]:
    try:
        command = get_command(command_id)
    except DeviceCommandNotFoundError as exc:
        return None, _device_error_response(exc)

    elder = _get_elder_for_device(command.target_device_id)
    if elder is None or not user_is_associated_with_elder(user, elder):
        return None, Response(
            {"detail": "You do not have access to this device command."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return command, None


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


class ElderDeviceListView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        devices = list_elder_assigned_devices(elder_id=elder_id)
        return Response(ElderAssignedDeviceSerializer(devices, many=True).data)


class DeviceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        return Response(DeviceSerializer(device).data)


class DeviceStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        try:
            return Response(get_device_state(device_id))
        except DeviceNotFoundError as exc:
            return _device_error_response(exc)


class DeviceAssignmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        assignments = get_assignments(device_id=device_id)
        return Response(DeviceAssignmentSerializer(assignments, many=True).data)

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        serializer = AssignDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_elder = get_object_or_404(Elder, id=serializer.validated_data["elder_id"])
        if not user_is_associated_with_elder(request.user, target_elder):
            return Response(
                {"detail": "You do not have access to the target elder."},
                status=status.HTTP_403_FORBIDDEN,
            )
        current_elder = _get_elder_for_device(device_id)
        if current_elder and not user_is_associated_with_elder(request.user, current_elder):
            return Response(
                {"detail": "You do not have access to this device."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            assignment = assign_device(device_id=device_id, **serializer.validated_data)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class DeviceReturnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        try:
            assignment = return_device(device_id=device_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceAssignmentSerializer(assignment).data)


class DevicePairingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        pairings = get_pairings(device_id=device_id)
        return Response(PairingSerializer(pairings, many=True).data)

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
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
        pairing = get_object_or_404(Pairing, id=pairing_id)
        elder = _get_elder_for_device(pairing.hub_device_id)
        if elder is None or not user_is_associated_with_elder(request.user, elder):
            return Response(
                {"detail": "You do not have access to this pairing."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            revoked = revoke_pairing(pairing_id=pairing_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(PairingSerializer(revoked).data)


class DeviceCompartmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        compartments = get_compartments(device_id=device_id)
        return Response(CompartmentSerializer(compartments, many=True).data)


class DeviceCommandsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
        commands = get_commands(device_id=device_id)
        return Response(DeviceCommandSerializer(commands, many=True).data)

    def post(self, request: Request, device_id: uuid.UUID) -> Response:
        device, elder, err = _check_device_access(request.user, device_id)
        if err:
            return err
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
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
        return Response(DeviceCommandSerializer(command).data)


class CommandStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, command_id: uuid.UUID) -> Response:
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
        try:
            return Response(get_command_status(command_id))
        except DeviceCommandNotFoundError as exc:
            return _device_error_response(exc)


class CommandDeliverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
        try:
            command = deliver_command(command_id=command_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
        try:
            command = start_command_execution(command_id=command_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)


class CommandCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
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
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
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
        command, err = _check_command_access(request.user, command_id)
        if err:
            return err
        try:
            command = cancel_command(command_id=command_id)
        except DeviceError as exc:
            return _device_error_response(exc)
        return Response(DeviceCommandSerializer(command).data)

