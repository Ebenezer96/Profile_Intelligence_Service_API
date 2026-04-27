import secrets
from datetime import timedelta

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone

from .models import RefreshToken


ACCESS_TOKEN_EXPIRY_SECONDS = 15 * 60
REFRESH_TOKEN_EXPIRY_DAYS = 7

signer = TimestampSigner()


def create_access_token(user):
    payload = f"{user.id}:{user.role}"
    return signer.sign(payload)


def verify_access_token(token):
    try:
        payload = signer.unsign(token, max_age=ACCESS_TOKEN_EXPIRY_SECONDS)
    except SignatureExpired:
        return None
    except BadSignature:
        return None

    user_id, role = payload.split(":", 1)

    return {
        "user_id": user_id,
        "role": role,
    }


def create_refresh_token(user):
    raw_token = secrets.token_urlsafe(48)

    refresh_token = RefreshToken.objects.create(
        user=user,
        token=raw_token,
        expires_at=timezone.now() + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
    )

    return refresh_token.token


def verify_refresh_token(token):
    refresh_token = RefreshToken.objects.filter(
        token=token,
        is_revoked=False,
    ).select_related("user").first()

    if not refresh_token:
        return None

    if refresh_token.is_expired():
        refresh_token.is_revoked = True
        refresh_token.save(update_fields=["is_revoked"])
        return None

    if not refresh_token.user.is_active:
        return None

    return refresh_token.user


def revoke_refresh_token(token):
    RefreshToken.objects.filter(token=token).update(is_revoked=True)