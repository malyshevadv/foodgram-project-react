import csv

from django.http import HttpResponse
from django_filters import rest_framework as filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipe.models import (Favorites, Ingredient, Recipe, ShoppingCart,
                           Subscription, Tag)
from .filters import IngredientFilter
from .permissions import IsAdmin, IsAuthenticated, IsAuthor, ReadOnly
from .serializers import (FavoritesSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionListToDisplaySerializer,
                          SubscriptionSerializer, TagSerializer)
from .viewsets import URLParamNOPayloadViewSet


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shop_cart(request):
    """Метод для скачивания списка покупок"""

    # Собираем все ингредиенты со всех рецептов в корзине
    shop_list = []
    shop_cart_list = request.user.cart_list.all()
    for obj in shop_cart_list:
        for ing_a in obj.recipe.ingredient_in_recipe_amount.all():
            shop_list.append((ing_a.ingredient.id, ing_a.amount))

    # Суммируем по каждому ингредиенту
    ingredient_list = {x: 0 for x, _ in shop_list}
    for ing, amount in shop_list:
        ingredient_list[ing] += amount

    # Готовим заголовок ответа
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shoppinglist.csv"'

    csv_writer = csv.writer(response)

    # Пишем нужную информацию в файл
    for ing_id, amount in ingredient_list.items():
        ingredient = Ingredient.objects.get(id=ing_id)
        csv_writer.writerow(
            [ingredient.name, amount, ingredient.measurement_unit]
        )

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscriptions(request):
    """Список подписок пользователя.

    Возвращает список подписок
    """
    user = request.user
    recipes_limit = int(request.query_params.get('recipes_limit'))

    subscription_list = []
    for sub in user.subscriber.all():
        subscription_list.append(sub.to_follow)

    paginator = PageNumberPagination()
    paginator.paginate_queryset(subscription_list, request)

    serializer = SubscriptionListToDisplaySerializer(
        instance=subscription_list,
        many=True,
        context={'limit': recipes_limit}
    )

    return paginator.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]
    filter_backends = [SearchFilter]
    search_fields = ('name', )
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]
    search_fields = ('@name', )
    pagination_class = None
    filter_backends = [filters.DjangoFilterBackend, ]
    filterset_class = IngredientFilter
    filterset_fields = ('name', )


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [
        IsAuthenticated & (IsAuthor | IsAdmin) | ReadOnly
    ]
    pagination_class = PageNumberPagination
    search_fields = ('name', )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user

        show_favorite = self.request.query_params.get('is_favorited')
        show_shop = self.request.query_params.get('is_in_shopping_cart')
        show_by_author = self.request.query_params.get('author')
        show_by_tag = self.request.GET.getlist('tags')

        if show_favorite is not None:
            return queryset.filter(fav_list__user=user)

        if show_shop is not None:
            return queryset.filter(cart_list__user=user)

        if show_by_author is not None:
            return queryset.filter(author=show_by_author)

        if show_by_tag:
            return queryset.filter(tags__slug__in=show_by_tag).distinct()

        return super().get_queryset()


class SubscriptionViewSet(URLParamNOPayloadViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    permission_classes = [
        IsAuthenticated | IsAdmin | ReadOnly
    ]
    pagination_class = PageNumberPagination

    def create(self, *args, **kwargs):
        """Метод переопределен: POST without payload,
         получаем данные запроса, передаем в специальный метод
        """
        obj_to_act_on = kwargs.get('user_id')
        param_name = 'to_follow'
        user = self.request.user.id

        return self.create_special(param_name, obj_to_act_on, user)

    @action(methods=['delete'], detail=False)
    def delete(self, request, user_id=None):
        return self.delete_special(
            request.user.subscriber.filter(to_follow=user_id)
        )


class ShoppingCartViewSet(URLParamNOPayloadViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    permission_classes = [
        IsAuthenticated | IsAdmin | ReadOnly
    ]
    pagination_class = None

    def create(self, *args, **kwargs):
        """Метод переопределен: POST without payload,
         получаем данные запроса, передаем в специальный метод
        """
        obj_to_act_on = kwargs.get('recipe_id')
        param_name = 'recipe'
        user = self.request.user.id

        return self.create_special(param_name, obj_to_act_on, user)

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id=None):
        return self.delete_special(
            request.user.cart_list.filter(recipe=recipe_id)
        )


class FavoritesViewSet(URLParamNOPayloadViewSet):
    serializer_class = FavoritesSerializer
    queryset = Favorites.objects.all()
    permission_classes = [
        IsAuthenticated | IsAdmin | ReadOnly
    ]
    pagination_class = None

    def create(self, *args, **kwargs):
        """Метод переопределен: POST without payload,
         получаем данные запроса, передаем в специальный метод
        """
        obj_to_act_on = kwargs.get('recipe_id')
        param_name = 'recipe'
        user = self.request.user.id

        return self.create_special(param_name, obj_to_act_on, user)

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id=None):
        return self.delete_special(
            request.user.fav_list.filter(recipe=recipe_id)
        )
