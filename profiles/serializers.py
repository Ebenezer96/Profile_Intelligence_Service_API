from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "gender",
            "gender_probability",
            "age",
            "age_group",
            "country_id",
            "country_name",
            "country_probability",
            "created_at",
        ]


class ProfileQuerySerializer(serializers.Serializer):
    gender = serializers.ChoiceField(
        choices=["male", "female"],
        required=False
    )
    age_group = serializers.ChoiceField(
        choices=["child", "teenager", "adult", "senior"],
        required=False
    )
    country_id = serializers.CharField(required=False)
    min_age = serializers.IntegerField(required=False)
    max_age = serializers.IntegerField(required=False)
    min_gender_probability = serializers.FloatField(required=False)
    min_country_probability = serializers.FloatField(required=False)
    sort_by = serializers.ChoiceField(
        choices=["age", "created_at", "gender_probability"],
        required=False
    )
    order = serializers.ChoiceField(
        choices=["asc", "desc"],
        required=False
    )
    page = serializers.IntegerField(required=False, default=1)
    limit = serializers.IntegerField(required=False, default=10)

    def validate_country_id(self, value):
        value = value.strip().upper()
        if len(value) != 2:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate_page(self, value):
        if value < 1:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate_limit(self, value):
        if value < 1 or value > 50:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate_min_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate_max_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate_min_gender_probability(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate_min_country_probability(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError("Invalid query parameters")
        return value

    def validate(self, attrs):
        min_age = attrs.get("min_age")
        max_age = attrs.get("max_age")

        if min_age is not None and max_age is not None and min_age > max_age:
            raise serializers.ValidationError(
                {"message": "Invalid query parameters"}
            )

        return attrs
    