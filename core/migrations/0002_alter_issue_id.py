# Generated by Django 3.2.19 on 2025-06-04 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='id',
            field=models.CharField(editable=False, max_length=15, primary_key=True, serialize=False),
        ),
    ]
