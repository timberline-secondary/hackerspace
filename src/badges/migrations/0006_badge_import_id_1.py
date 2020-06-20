# Generated by Django 2.2.12 on 2020-05-28 05:49

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    # Adding a unique, non-nullable field over the next three migrations per:
    # https://docs.djangoproject.com/en/3.0/howto/writing-migrations/#migrations-that-add-unique-fields

    dependencies = [
        ('badges', '0005_badge_initialdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='badge',
            name='import_id',
            field=models.UUIDField(default=uuid.uuid4, help_text='Only edit this if you want to link to a badge in another system so that when importing from that other system, it will update this badge too. Otherwise do not edit this or it will break existing links!', null=True),
        ),
    ]