import base64
import re

from django.core.files.base import ContentFile
from recipes.models import (
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    Tag,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import CustomUser as User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source='name')

    class Meta:
        model = Tag
        fields = ('id', 'tag_name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    # ingredient_name = serializers.CharField(source='name')

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measure',
        )


class IngredientM2MSerializer(serializers.ModelSerializer):
    ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'name',
            'amount',
        )
        read_only_fields = ('ingredient',)


class RecipeSerializer(serializers.ModelSerializer):
    # tags = TagSerializer(required=False)
    ingredients = IngredientM2MSerializer(
        many=True,
        source='ingredient_used',
    )
    image = Base64ImageField(
        required=False,
        allow_null=True,
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'name', 'cooking_time', 'ingredients', 'description',
            'pub_date', 'author', 'tags', 'image',
        )
        read_only_fields = ('author',)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredient_used')
        recipes = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            current_ingredient = Ingredient.get('ingredient')
            amount = ingredient.get('amount')
            recipes.ingredients.add(
                current_ingredient,
                through_defaults={
                    'amount': amount,
                }
            )

        return recipes

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredient_used')
            lst = []
            for ingredient in ingredients_data:
                current_ingredient, status = ingredient.objects.get_or_create(
                    **ingredient
                    )
                lst.append(current_ingredient)
            instance.ingredients.set(lst)

        instance.save()
        return instance


class RecipeIngredientsListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id',
    )
    name = serializers.CharField(
        source='ingredient.name',
    )
    amount = serializers.ReadOnlyField()

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'name',
            'amount',
            # 'ingredient',
        )


class RecipeListSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientsListSerializer(
        source='ingredients_used',
        many=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'cooking_time',
            'pub_date',
            'author',
            'tags',
            'ingredients',
        )


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
    )

    class Meta:
        model = Follow
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
            )
        ]

    def validate(self, data):
        if self.context['request'].user == data['following']:
            raise serializers.ValidationError('Нельзя подписываться на себя!')
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
        )


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=254,
        required=True,
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def validate(self, data):
        username = data['username']
        email = data['email']
        email_exists = User.objects.filter(email=email).exists()
        username_exists = User.objects.filter(username=username).exists()
        if username.lower() == 'me':
            raise serializers.ValidationError(
                f'Имя пользователя "{username}" недоступно.',
            )
        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError('Некорректный формат логина')
        if username_exists and not email_exists:
            raise serializers.ValidationError(
                'Пользователь зарегистрирован с другой почтой'
            )
        if email_exists and not username_exists:
            raise serializers.ValidationError(
                'Пользователь зарегистрирован с другим логином'
            )
        return data


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username',)


class ProfileEditSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)
