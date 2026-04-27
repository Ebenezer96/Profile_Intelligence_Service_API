from django.db import models
import uuid
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    ANALYST = "analyst", "Analyst"


class AppUser(models.Model):
    github_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.ANALYST,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        "accounts.AppUser",
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )

    token = models.CharField(max_length=255, unique=True)

    is_revoked = models.BooleanField(default=False)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.user.username} - {self.token[:8]}"