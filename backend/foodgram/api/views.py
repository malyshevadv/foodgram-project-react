from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from recipe.models import (Favorites, Ingridient, Recipe, ShoppingCart,
                           Subscription, Tag)

from .permissions import IsAdmin, IsAuthenticated, IsAuthor, ReadOnly
from .serializers import (FavoritesSerializer, IngridientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]
    filter_backends = [SearchFilter]
    search_fields = ('name', )


class IngridientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngridientSerializer
    queryset = Ingridient.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]
    search_fields = ('name', )


class RecipeViewSet(ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = [
        IsAuthenticated & (IsAuthor | IsAdmin) | ReadOnly
    ]
    pagination_class = PageNumberPagination
    search_fields = ('name', )


class ShoppingCartViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]

    @api_view(['GET'])
    def download(self, *args, **kwargs):
        # TO DO: download as TXT
        file = 'temp'
        response = HttpResponse(file, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=file.csv'
        return response


class FavoritesViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = FavoritesSerializer
    queryset = Favorites.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]
    pagination_class = PageNumberPagination


class SubscriptionViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    permission_classes = [
        (IsAuthenticated & IsAdmin) | ReadOnly
    ]
    pagination_class = PageNumberPagination
