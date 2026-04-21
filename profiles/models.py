from uuid6 import uuid7
from django.db import models


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