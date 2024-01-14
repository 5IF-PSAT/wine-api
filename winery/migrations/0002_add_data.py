from django.db import migrations
import pandas as pd


def fill_winery_data(apps, schema_editor):
    Winery = apps.get_model('winery', 'Winery')

    # Read pandas dataframe from csv file
    wineries_df = pd.read_csv('./db_data/wineries.csv')

    # Rename columns to match model fields
    wineries_df = wineries_df.rename(columns={'WineryID': 'winery_id', 'WineryName': 'winery_name', 'Website': 'website'})

    # Convert dataframe to list of dictionaries
    wineries_data = wineries_df.to_dict('records')

    # Bulk create wineries
    Winery.objects.bulk_create([Winery(**winery) for winery in wineries_data])


class Migration(migrations.Migration):
    dependencies = [
        ('winery', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_winery_data),
    ]
