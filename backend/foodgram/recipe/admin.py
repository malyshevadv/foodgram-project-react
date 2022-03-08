from django import forms
from django.contrib import admin
from django.db import models

from .models import Ingredient, Recipe, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

    list_display = ('id', 'name', 'author',
                    'image', 'text', 'cooking_time',
                    'in_favorites')
    list_filter = ('name', 'author')
    filter_horizontal = ('tags',)
    inlines = [IngredientInline, ]

    def in_favorites(self, obj):
        return obj.fav_list.all().count()
