import json
from pathlib import Path

from django.core.management.base import BaseCommand
from profiles.models import Profile


class Command(BaseCommand):
    help = "Seed database with profiles from a JSON file"

    def handle(self, *args, **options):
        file_path = Path("seed_profiles.json")

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f"JSON file not found at: {file_path}")
            )
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                data = data["profiles"]
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR("Invalid JSON file"))
            return

        seeded_count = 0
        updated_count = 0

        for item in data:
            _, created = Profile.objects.update_or_create(
                name=item["name"].strip().lower(),
                defaults={
                    "gender": item["gender"],
                    "gender_probability": item["gender_probability"],
                    "age": item["age"],
                    "age_group": item["age_group"],
                    "country_id": item["country_id"],
                    "country_name": item["country_name"],
                    "country_probability": item["country_probability"],
                },
            )

            if created:
                seeded_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding complete. Created: {seeded_count}, Updated: {updated_count}"
            )
        )