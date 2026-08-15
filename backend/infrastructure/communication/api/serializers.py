"""Serializers for communication join APIs."""

from rest_framework import serializers


class StartCallSerializer(serializers.Serializer):
    elder_id = serializers.UUIDField()
    channel = serializers.CharField(max_length=16)
    recipient_contact_id = serializers.UUIDField()


class EndCallSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()


class LoginUrlSerializer(serializers.Serializer):
    elder_id = serializers.UUIDField()
