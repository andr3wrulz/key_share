# Generated by Django 2.2.4 on 2019-08-04 16:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('key_share_app', '0003_auto_20190803_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='key',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_keys', to=settings.AUTH_USER_MODEL),
        ),
    ]
