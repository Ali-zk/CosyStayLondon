from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Property
import random
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Generates 10 dummy properties for testing purposes.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        try:
            owner = User.objects.filter(is_superuser=True).first()
            if not owner:
                owner = User.objects.first()
            if not owner:
                self.stdout.write(self.style.ERROR('No user found to assign properties to. Please create a user first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error retrieving user: {e}'))
            return

        locations = ["Tehran", "Isfahan", "Shiraz", "Mashhad", "Tabriz", "Kish", "Rasht", "Yazd", "Kerman", "Gilan"]
        descriptions = [
            "A cozy and modern apartment perfect for a relaxing getaway.",
            "Spacious villa with a beautiful garden and pool.",
            "Downtown loft with stunning city views.",
            "Charming traditional house close to historical sites.",
            "Riverside cottage ideal for nature lovers.",
            "Luxurious penthouse with all amenities.",
            "Family-friendly home in a quiet neighborhood.",
            "Stylish studio apt, great for solo travelers.",
            "Rustic cabin in the mountains, perfect for adventure.",
            "Beachfront property with amazing ocean views."
        ]

        for i in range(1, 11):
            title = f"Property {i}: {random.choice(['Apartment', 'Villa', 'House', 'Studio'])} in {random.choice(locations)}"
            description = random.choice(descriptions)
            price_per_night = round(random.uniform(50.00, 500.00), 2)
            location = random.choice(locations)
            address = f"{random.randint(1, 100)} {random.choice(['Main St', 'Oak Ave', 'Pine Ln'])}"
            number_of_beds = random.randint(1, 5)
            number_of_baths = random.choice([1.0, 1.5, 2.0, 2.5, 3.0])
            area_sqft = random.randint(500, 3000)
            available_from = date.today() + timedelta(days=random.randint(0, 30))
            available_to = available_from + timedelta(days=random.randint(30, 365))
            is_available = random.choice([True, False])

            Property.objects.create(
                owner=owner,
                title=title,
                description=description,
                price_per_night=price_per_night,
                location=location,
                address=address,
                number_of_beds=number_of_beds,
                number_of_baths=number_of_baths,
                area_sqft=area_sqft,
                available_from=available_from,
                available_to=available_to,
                is_available=is_available,
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created property: "{title}"'))

        self.stdout.write(self.style.SUCCESS('Finished generating 10 properties.'))