from django.core.management.base import BaseCommand
from assets.models import Asset


class Command(BaseCommand):
    help = 'Generuje slugi dla istniejących assetów'

    def handle(self, *args, **options):
        assets = Asset.objects.filter(slug__isnull=True)
        count = 0
        
        for asset in assets:
            asset.slug = asset.generate_unique_slug()
            asset.save()
            count += 1
            self.stdout.write(f'Wygenerowano slug "{asset.slug}" dla assetu "{asset.title}"')
        
        self.stdout.write(
            self.style.SUCCESS(f'Pomyślnie wygenerowano {count} slugów')
        ) 