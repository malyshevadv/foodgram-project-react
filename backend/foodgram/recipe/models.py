from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='имя',
    )
    color = models.CharField(
        max_length=16,
        unique=True,
        verbose_name='цвет',
    )
    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.TextField(
        max_length=200,
        verbose_name='имя',
    )
    measurement_unit = models.TextField(
        max_length=50,
        verbose_name='единица измерения',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_recipes',
        verbose_name='автор',
    )
    name = models.TextField(
        max_length=200,
        verbose_name='имя',
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True,
        verbose_name='изображение',
    )
    text = models.TextField(
        verbose_name='текст',)
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1), ],
        verbose_name='время приготовления',
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        related_name='ingredient_amount_set',
        verbose_name='ингредиенты',
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        blank=True,
        verbose_name='теги',
    )

    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creation_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_amount',
        on_delete=models.CASCADE,
        verbose_name='ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_in_recipe_amount',
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1), ],
        verbose_name='количество',
    )

    class Meta:
        unique_together = (('ingredient', 'recipe'),)
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количества ингредиентов'

    def __str__(self):
        return "{}_{}_{}".format(
            self.recipe.__str__(),
            self.ingredient.__str__(),
            self.amount)


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='подписчик',
    )
    to_follow = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_subscribed',
        verbose_name='автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'to_follow'],
                name='unique_follow'
            )
        ]


class Favorites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fav_list',
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='fav_list',
        verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_fav'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_list',
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart_list',
        verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_cart'
            )
        ]
