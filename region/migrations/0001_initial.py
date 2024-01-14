# Generated by Django 3.2.22 on 2024-01-14 11:01

from django.db import migrations, models
import region.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, serialize=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, serialize=True)),
                ('region_id', models.IntegerField(db_column='RegionID', editable=False, unique=True, serialize=True)),
                ('region_name', models.CharField(db_column='RegionName', max_length=255, serialize=True)),
                ('country', models.CharField(db_column='Country', max_length=255, serialize=True)),
                ('code', models.CharField(db_column='Code', max_length=255, serialize=True)),
                ('latitude', models.FloatField(db_column='Latitude', serialize=True)),
                ('longitude', models.FloatField(db_column='Longitude', serialize=True)),
            ],
            options={
                'db_table': 'region',
                'ordering': ['id'],
            },
            managers=[
                ('objects', region.managers.RegionManager()),
            ],
        ),
    ]
