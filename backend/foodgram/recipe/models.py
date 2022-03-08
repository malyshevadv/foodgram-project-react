from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.TextField(max_length=200, unique=True)
    color = models.CharField(max_length=16, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']


class Ingredient(models.Model):
    name = models.TextField(max_length=200)
    measurement_unit = models.TextField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_recipes')
    name = models.TextField(max_length=200)
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        related_name='ingredient_amount_set'
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        blank=True,
    )

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient_amount',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingredient_in_recipe_amount',
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField()

    def __str__(self):
        return "{}_{}_{}".format(
            self.recipe.__str__(),
            self.ingredient.__str__(),
            self.amount)

    class Meta:
        unique_together = (('ingredient', 'recipe'),)


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
    )
    to_follow = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_subscribed',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'to_follow'],
                name='unique_follow'
            )
        ]

    @property
    def object_field():
        return "to_follow"


class Favorites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fav_list',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='fav_list'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_fav'
            )
        ]

    @property
    def object_field():
        return "recipe"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_list',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart_list'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_cart'
            )
        ]

    @property
    def object_field():
        return "recipe"
