from django_filters import FilterSet
from django_filters.filters import CharFilter

from recipe.models import Ingredient


class IngredientFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = {
            'name': ['iexact', 'istartswith', 'icontains'],
        }
