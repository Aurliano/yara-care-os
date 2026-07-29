"""Custom JWT serializer using phone as the username field."""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "phone"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["phone"] = user.phone
        token["full_name"] = user.full_name
        return token
