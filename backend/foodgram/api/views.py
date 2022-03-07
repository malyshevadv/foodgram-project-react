import csv

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from recipe.models import (Favorites, Ingredient, Recipe, ShoppingCart,
                           Subscription, Tag)

from .permissions import IsAdmin, IsAuthenticated, IsAuthor, ReadOnly
from .serializers import (FavoritesSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionListToDisplaySerializer,
                          SubscriptionSerializer,
                          TagSerializer)


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

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')

        if name is not None:
            return queryset.filter(name__icontains=name.lower())

        return super().get_queryset()


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


class SubscriptionViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    permission_classes = [
        IsAuthenticated | IsAdmin | ReadOnly
    ]
    pagination_class = PageNumberPagination

    def create(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        прописываем поля на основе данных запроса,
        а именно пользователя-подписчика, отправляющего запрос
         и ID пользователя-автора из адресной строки
        """
        obj_to_act_on = kwargs.get('user_id')
        user = self.request.user.id

        serializer = self.get_serializer(data=self.request.data,
                                         context={
                                             'to_follow': obj_to_act_on,
                                             'user': user})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def get_serializer(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        передаем корректный контекст для сериалайзера
        """
        serializer_class = self.get_serializer_class()

        draft_request_data = self.request.data.copy()
        draft_request_data['to_follow'] = kwargs['context'].get('to_follow')
        draft_request_data['user'] = kwargs['context'].get('user')

        kwargs['context'] = self.get_serializer_context()
        kwargs['data'] = draft_request_data
        return serializer_class(*args, **kwargs)

    @action(methods=['delete'], detail=False)
    def delete(self, request, user_id=None):

        to_delete = request.user.subscriber.filter(to_follow=user_id)
        if to_delete.count() == 1:
            to_delete.first().delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        elif to_delete.count() == 0:
            return Response(
                'Ошибка удаления объекта: не найдено.',
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                'Ошибка удаления объекта: что-то пошло не так.',
                status=status.HTTP_400_BAD_REQUEST
            )


class ShoppingCartViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    permission_classes = [
        IsAuthenticated | IsAdmin | ReadOnly
    ]
    pagination_class = None

    def create(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        прописываем поля на основе данных запроса,
        а именно пользователя, отправляющего запрос
        и ID рецепта в адресной строке
        """

        obj_to_act_on = kwargs.get('recipe_id')
        user = self.request.user.id

        serializer = self.get_serializer(data=self.request.data,
                                         context={
                                             'recipe': obj_to_act_on,
                                             'user': user})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def get_serializer(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        передаем корректный контекст для сериалайзера
        """
        # leave this intact
        serializer_class = self.get_serializer_class()

        # Intercept the request and add required data to the request.data
        draft_request_data = self.request.data.copy()
        draft_request_data['recipe'] = kwargs['context'].get('recipe')
        draft_request_data['user'] = kwargs['context'].get('user')

        kwargs['context'] = self.get_serializer_context()
        kwargs['data'] = draft_request_data
        return serializer_class(*args, **kwargs)

    @action(methods=['delete'], detail=True)
    def delete(self, request, recipe_id=None):

        to_delete = request.user.cart_list.filter(recipe=recipe_id)
        if to_delete.count() == 1:
            to_delete.first().delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        elif to_delete.count() == 0:
            return Response(
                'Ошибка удаления объекта: не найдено.',
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                'Ошибка удаления объекта: что-то пошло не так.',
                status=status.HTTP_400_BAD_REQUEST
            )


class FavoritesViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = FavoritesSerializer
    queryset = Favorites.objects.all()
    permission_classes = [
        IsAuthenticated | IsAdmin | ReadOnly
    ]
    pagination_class = PageNumberPagination
    pagination_class = None

    def create(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        прописываем поля на основе данных запроса,
        а именно пользователя, отправляющего запрос
        и ID рецепта в адресной строке
        """
        obj_to_act_on = kwargs.get('recipe_id')
        user = self.request.user.id

        serializer = self.get_serializer(data=self.request.data,
                                         context={
                                             'recipe': obj_to_act_on,
                                             'user': user})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def get_serializer(self, *args, **kwargs):
        """Метод переопределен:
        POST without payload,
        передаем корректный контекст для сериалайзера
        """
        serializer_class = self.get_serializer_class()

        draft_request_data = self.request.data.copy()
        draft_request_data['recipe'] = kwargs['context'].get('recipe')
        draft_request_data['user'] = kwargs['context'].get('user')

        kwargs['context'] = self.get_serializer_context()
        # kwargs['data'] immutable - поэтому заменяем
        kwargs['data'] = draft_request_data
        return serializer_class(*args, **kwargs)

    @action(methods=['delete'], detail=False)
    def delete(self, request, recipe_id=None):

        to_delete = request.user.fav_list.filter(recipe=recipe_id)
        if to_delete.count() == 1:
            to_delete.first().delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        elif to_delete.count() == 0:
            return Response(
                'Ошибка удаления объекта: не найдено.',
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                'Ошибка удаления объекта: что-то пошло не так.',
                status=status.HTTP_400_BAD_REQUEST
            )
