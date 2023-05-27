# Generated by Django 3.2.17 on 2023-05-25 11:32

from django.db import migrations
import utilities.models


class Migration(migrations.Migration):

    dependencies = [
        ('siteconfig', '0019_siteconfig_enable_google_signin'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfig',
            name='custom_javascript',
            field=utilities.models.RestrictedFileField(blank=True, help_text='WARNING: This custom JavaScript file can be used to completely override how the front end of your deck functions.             This feature also has the potential of making your deck unusable. Use at your own risk.', null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='custom_stylesheet',
            field=utilities.models.RestrictedFileField(blank=True, help_text='WARNING: This CSS stylesheet can be used to completely override the look and layout of your deck.             This feature also has the potential of making your deck unusable. Use at your own risk.', null=True, upload_to=''),
        ),
    ]