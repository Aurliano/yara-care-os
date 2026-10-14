"""Custom JWT serializer using phone as the username field."""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from common.phone import normalize_phone


class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "phone"

    def validate(self, attrs):
        if "phone" in attrs:
            attrs["phone"] = normalize_phone(attrs["phone"])
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["phone"] = user.phone
        token["full_name"] = user.full_name
        return token
