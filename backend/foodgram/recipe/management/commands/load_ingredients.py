import json
import os

from api.serializers import IngredientSerializer
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Load ingridients'

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'data/', 'ingredients.json')

        with open(path, 'r') as file:
            data = json.load(file)

            for obj in data:
                serializer = IngredientSerializer(data=obj)

                if serializer.is_valid():
                    serializer.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            'Successfully added {}'.format(
                                serializer.data
                            )
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            'An error occurred while loading: {}'.format(
                                serializer.errors
                            )
                        )
                    )
