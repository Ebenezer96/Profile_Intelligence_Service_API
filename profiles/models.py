from uuid6 import uuid7
from django.db import models
from django.utils import timezone
import hashlib
import secrets


def generate_uuid7():
    return uuid7()


class Profile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid7,
        editable=False
    )
    name = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=20)
    gender_probability = models.FloatField()
    age = models.IntegerField()
    age_group = models.CharField(max_length=20)
    country_id = models.CharField(max_length=2)
    country_name = models.CharField(max_length=100)
    country_probability = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gender"]),
            models.Index(fields=["age_group"]),
            models.Index(fields=["country_id"]),
            models.Index(fields=["age"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name


class PlatformUser(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_ANALYST = "analyst"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_ANALYST, "Analyst"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid7,
        editable=False
    )
    github_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150)
    name = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    profile_url = models.URLField(blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_ANALYST
    )
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["github_id"]),
            models.Index(fields=["username"]),
            models.Index(fields=["role"]),
        ]

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.username} ({self.role})"


class RefreshToken(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=generate_uuid7,
        editable=False
    )
    user = models.ForeignKey(
        PlatformUser,
        on_delete=models.CASCADE,
        related_name="refresh_tokens"
    )
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["revoked_at"]),
        ]

    @staticmethod
    def generate_raw_token():
        return secrets.token_urlsafe(64)

    @staticmethod
    def hash_token(raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @property
    def is_valid(self):
        return self.revoked_at is None and self.expires_at > timezone.now()

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at"])