# Generated by Django 3.2.16 on 2023-01-31 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incoming', '0006_alter_changelog_action_on_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='changelog',
            name='sent',
            field=models.BooleanField(default=False, verbose_name='Отправлено'),
        ),
    ]
