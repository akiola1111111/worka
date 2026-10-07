from django.core.management.base import BaseCommand
from django.utils.text import slugify
from services.models import ServiceCategory

CATEGORIES = [
    ("Plumber", "🔧"), ("Electrician", "💡"), ("Seamstress / Tailor", "🧵"),
    ("Painter", "🎨"), ("Carpenter", "🪚"), ("Mason / Builder", "🧱"),
    ("AC & Refrigeration Technician", "❄️"), ("Mechanic", "🚗"),
    ("Welder / Fabricator", "🔥"), ("Hairdresser / Barber", "💇"),
    ("Cleaner", "🧹"), ("Gardener / Landscaper", "🌿"),
    ("Generator Repair Technician", "🔌"), ("Tiler", "🧩"), ("Roofer", "🏠"),
    ("Satellite / TV Installer", "📡"), ("CCTV Installer", "📷"),
    ("Furniture Maker", "🛋️"), ("Event Decorator", "🎉"), ("Photographer", "📸"),
]


class Command(BaseCommand):
    help = "Seed common Ghana trade/service categories"

    def handle(self, *args, **options):
        created = 0
        for name, icon in CATEGORIES:
            _, was_created = ServiceCategory.objects.get_or_create(
                name=name, defaults={"slug": slugify(name), "icon": icon}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Seeded categories ({created} new)."))
