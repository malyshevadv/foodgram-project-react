from django.contrib.auth import get_user_model
from rest_framework import serializers, status, validators

from recipe.models import (Favorites, Ingridient, IngridientAmount, Recipe,
                           ShoppingCart, Subscription, Tag)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_subscribed', 'password'
        ]
        read_only_fields = ['id', 'is_subscribed']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        request = self.context['request']
        user = request.user
        if (not user.is_authenticated):
            return False
        return (
            Subscription.objects.filter(user=user, following=obj).count() > 0
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TokenSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=254)
    password = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngridientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingridient
        fields = '__all__'


class IngridientAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngridientAmount
        fields = ('ingridient', 'recipe', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )
    tags = TagSerializer(read_only=True, many=True)
    ingredients = IngridientSerializer(read_only=True, many=True)
    ingridient_in_recipe_amount = IngridientAmountSerializer(many=True)

    is_favorited = serializers.BooleanField(default=False, required=False)
    is_in_shopping_cart = serializers.BooleanField(
        default=False,
        required=False
    )

    class Meta:
        model = Recipe
        fields = (
            'author', 'name',
            'image', 'text',
            'cooking_time', 'tags',
            'ingredients', 'id', 'amount',
            'is_favorited', 'is_in_shopping_cart')


class SubscriptionSerializer(serializers.ModelSerializer):
    following = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username',
    )
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )

    def validate_following(self, value):
        request = self.context['request']
        if request.user == value:
            raise serializers.ValidationError(
                'Вы не можете подписаться сами на себя.',
                status.HTTP_400_BAD_REQUEST
            )
        return value

    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'following'],
                message='Вы уже подписаны на этого автора.'
            )
        ]


class FavoritesSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Favorites
        fields = '__all__'
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=['user', 'recipes'],
                message='Вы уже добавили этот рецепт в избранное.'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipes'],
                message='Вы уже добавили этот рецепт в корзину.'
            )
        ]
