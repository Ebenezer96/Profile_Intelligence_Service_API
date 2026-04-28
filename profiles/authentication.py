from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .auth_tokens import decode_access_token
from .models import PlatformUser


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()
        except ValueError:
            raise AuthenticationFailed("Invalid Authorization header")

        if prefix.lower() != "bearer":
            raise AuthenticationFailed("Invalid token prefix")

        payload = decode_access_token(token)

        if not payload:
            raise AuthenticationFailed("Invalid or expired token")

        user_id = payload.get("user_id")

        try:
            user = PlatformUser.objects.get(id=user_id)
        except PlatformUser.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return (user, None)