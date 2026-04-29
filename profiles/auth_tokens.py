import jwt

from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from .models import RefreshToken


ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7


def create_access_token(user):
    now = timezone.now()

    payload = {
        "type": "access",
        "user_id": str(user.id),
        "github_id": user.github_id,
        "username": user.username,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_MINUTES)).timestamp()),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user):
    raw_token = RefreshToken.generate_raw_token()
    token_hash = RefreshToken.hash_token(raw_token)

    RefreshToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=timezone.now() + timedelta(days=REFRESH_TOKEN_DAYS),
    )

    return raw_token


def decode_access_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        if payload.get("type") != "access":
            return None

        return payload

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None


def rotate_refresh_token(raw_token):
    token_hash = RefreshToken.hash_token(raw_token)

    try:
        stored_token = RefreshToken.objects.select_related("user").get(
            token_hash=token_hash
        )
    except RefreshToken.DoesNotExist:
        return None

    if not stored_token.is_valid:
        return None

    stored_token.revoke()

    user = stored_token.user

    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "user": user,
    }