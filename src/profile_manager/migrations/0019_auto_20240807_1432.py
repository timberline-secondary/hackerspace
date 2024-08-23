# Generated by Django 3.2.25 on 2024-08-07 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile_manager', '0018_auto_20240107_1115'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='grad_year',
        ),
        migrations.AddField(
            model_name='profile',
            name='custom_profile_field',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]