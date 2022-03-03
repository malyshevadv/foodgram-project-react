from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.TextField(max_length=200)
    color = models.CharField(max_length=16)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Ingridient(models.Model):
    name = models.TextField(max_length=200)
    measurement_unit = models.TextField(max_length=50)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    name = models.TextField(max_length=150)
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()

    ingredients = models.ManyToManyField(
        Ingridient,
        through='IngridientAmount',
        related_name='recipes',
        blank=True
    )

    tags = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipes',
        blank=True
    )

    def __str__(self):
        return self.name


class IngridientAmount(models.Model):
    ingridient = models.ForeignKey(
        Ingridient,
        related_name='ingridient_amount',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='ingridient_in_recipe_amount',
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField()

    def __str__(self):
        return "{}_{}".format(self.recipe.__str__(), self.ingridient.__str__())

    class Meta:
        unique_together = (('ingridient', 'recipe'),)


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='is_subscribed',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'
            )
        ]


class Favorites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fav_list',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='fav_list',
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='unique_recipe_in_fav'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_list',
    )
    recipes = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart_list',
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipes'],
                name='unique_recipe_in_cart'
            )
        ]
