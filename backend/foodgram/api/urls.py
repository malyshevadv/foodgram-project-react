from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavoritesViewSet, IngridientViewSet, RecipeViewSet,
                    ShoppingCartViewSet, SubscriptionViewSet, TagViewSet)

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngridientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

router.register(
    r'recipes\/(?P<recipe_id>\d+)\/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart'
)
router.register(
    r'recipes\/(?P<recipe_id>\d+)\/favorite',
    FavoritesViewSet,
    basename='favorite'
)
router.register(
    r'users\/(?P<user_id>\d+)\/subscribe',
    SubscriptionViewSet,
    basename='subscribe'
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
