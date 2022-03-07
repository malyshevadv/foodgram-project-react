import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from recipe.models import (Favorites, Ingredient, IngredientAmount, Recipe,
                           ShoppingCart, Subscription, Tag)
from rest_framework import serializers, status

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор собственного класса пользователя"""
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
        depth = 1

    def get_is_subscribed(self, obj):
        """Получение специального поля:
        подписан ли текущий пользователь
        на запрашиваемого пользователя
        """

        if hasattr(self.context, 'user'):
            user = self.context['request'].user
        else:
            user = None

        if (user is None or not user.is_authenticated):
            return False
        return (user.subscriber.filter(to_follow=obj).count() > 0)

    def create(self, validated_data):
        """Переопределение создания пользователя
        для хеширования пароля
        """

        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега"""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента"""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор промежуточного класса
    для сохранения инфомрации о количестве ингредиента в рецепте
    """
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


# From  gist.github.com/yprez/7704036
class Base64ImageField(serializers.ImageField):
    """Сериализатор для дешифрации изображения из base64"""

    def to_internal_value(self, data):
        if ((isinstance(data, str) or isinstance(data, bytes))
                and data.startswith('data:image') and (';base64,' in data)):
            # base64 encoded image - decode
            format, imgstr = data.split(';base64,')  # format ~= data:image/X,
            ext = format.split('/')[-1]  # guess file extension

            try:
                decoded_file = base64.b64decode(imgstr)
            except TypeError:
                self.fail('invalid_image')

            data = ContentFile(decoded_file, name=imgstr[12] + '.' + ext)

        return super(Base64ImageField, self).to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта"""
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientAmountSerializer(
        many=True,
        source='ingredient_in_recipe_amount'
    )
    image = Base64ImageField()
    name = serializers.CharField(max_length=200)
    cooking_time = serializers.IntegerField(min_value=1)

    is_favorited = serializers.IntegerField(
        min_value=0,
        max_value=1,
        default=0,
        required=False,
        read_only=True
    )
    is_in_shopping_cart = serializers.IntegerField(
        min_value=0,
        max_value=1,
        default=0,
        required=False,
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time')
        read_only_fields = ['id', 'author',
                            'is_favorited', 'is_in_shopping_cart']

    def create(self, validated_data):
        """Переопределенный класс создания:
        вложенные сериализаторы требуют обработки
        """

        tags_list = validated_data.pop('tags')
        ingredient_list = validated_data.pop('ingredient_in_recipe_amount')
        instance = super().create(validated_data)

        for tag in tags_list:
            instance.tags.add(tag)
        for ing in ingredient_list:
            ing_am = IngredientAmount(
                recipe=instance,
                ingredient=Ingredient.objects.get(
                    id=ing.get('ingredient').get('id')
                ),
                amount=ing.get('amount')
            )
            ing_am.save()
        return instance

    def update(self, instance, validated_data):
        """Переопределенный класс обновления:
        вложенные сериализаторы требуют отдельного обновления
        """

        tags_list = validated_data.pop('tags')
        ingredient_list = validated_data.pop('ingredient_in_recipe_amount')
        instance = super().update(instance, validated_data)

        existing_tags = instance.tags.all()
        for tag in existing_tags:
            if tag not in tags_list:
                instance.tags.remove(tag)
        for tag in tags_list:
            if tag not in existing_tags:
                instance.tags.add(tag)

        existing_ing = instance.ingredients.all()
        for ing in existing_ing:
            if ing not in ingredient_list:
                IngredientAmount.objects.get(
                    recipe=instance,
                    ingredient=ing
                ).delete()
        for ing in ingredient_list:
            ing_am, _ = IngredientAmount.objects.get_or_create(
                recipe=instance,
                ingredient=Ingredient.objects.get(
                    id=ing.get('ingredient').get('id')
                ),
                amount=ing.get('amount')
            )
        return instance

    def to_representation(self, instance):
        """Переопределенный класс отображения:
        вложенные сериализаторы требуют обработки для вывода
        """

        response = super().to_representation(instance)
        tag_list = []
        for tag in instance.tags.all():
            tag_list.append(TagSerializer(tag).data)
        response['tags'] = tag_list

        response['image'] = instance.image.url

        user = self.context['request'].user

        if (not user.is_authenticated):
            response['is_favorited'] = False
            response['is_in_shopping_cart'] = False
        else:
            response['is_favorited'] = user.fav_list.filter(
                recipe=instance).count() > 0
            response['is_in_shopping_cart'] = user.cart_list.filter(
                recipe=instance).count() > 0

        return response


class RecipeShortenedToDisplaySerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта для отображения"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionListToDisplaySerializer(UserSerializer):
    """Сериализатор списка подписок"""
    recipes_count = serializers.IntegerField(
        default=0,
        read_only=True
    )
    recipes = RecipeShortenedToDisplaySerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        ]

    def to_representation(self, instance):
        """Переопределенный класс отображения:
        вложенные сериализаторы требуют обработки для вывода
        """
        lim = self.context.get('limit')

        response = super().to_representation(instance)
        response['articles_count'] = instance.user_recipes.all().count()

        recipe_list = []

        if lim is not None:
            recipe_set = instance.user_recipes.all()[:lim]
        else:
            recipe_set = instance.user_recipes.all()
        for recipe in recipe_set:
            recipe_list.append(RecipeShortenedToDisplaySerializer(recipe).data)
        response['recipes'] = recipe_list

        return response


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки"""
    class Meta:
        model = Subscription
        fields = ('user', 'to_follow')

    def validate(self, data):
        if (data['user'] == data['to_follow']):
            raise serializers.ValidationError(
                'Вы не можете подписаться сами на себя.',
                status.HTTP_400_BAD_REQUEST
            )
        if (data['user'].subscriber.filter(
                to_follow=data['to_follow']).count() > 0):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.',
                status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        """Переопределенный класс отображения"""

        response = super().to_representation(instance)
        response['to_follow'] = SubscriptionListToDisplaySerializer(
            instance.to_follow
        ).data

        return response


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор избранного"""
    class Meta:
        model = Favorites
        fields = '__all__'

    def validate(self, data):
        """Переопределен для проверки на уникальность"""
        if (data['user'].fav_list.filter(
                recipe=data['recipe']).count() > 0):
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт в избранное.',
                status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        """Переопределенный класс отображения"""
        return RecipeShortenedToDisplaySerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины"""
    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def validate(self, data):
        """Переопределен для проверки на уникальность"""
        if (data['user'].cart_list.filter(
                recipe=data['recipe']).count() > 0):
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт в корзину.',
                status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        """Переопределенный класс отображения"""
        return RecipeShortenedToDisplaySerializer(instance.recipe).data
