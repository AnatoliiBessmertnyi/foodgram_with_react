# Generated by Django 4.2.5 on 2023-09-13 10:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_remove_recipe_tags_delete_tagrecipe_recipe_tags'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='tags',
        ),
        migrations.CreateModel(
            name='TagRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.tag')),
            ],
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.ManyToManyField(through='recipes.TagRecipe', to='recipes.tag'),
        ),
    ]
