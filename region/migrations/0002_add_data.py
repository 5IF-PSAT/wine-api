from django.db import migrations
import pandas as pd
from wine_api.settings import BASE_DIR


def fill_region_data(apps, schema_editor):
    Region = apps.get_model('region', 'Region')

    # Read dataframe from parquet file
    regions_df = pd.read_parquet(f'{BASE_DIR}/db_data/regions.parquet')

    # Rename columns to match model fields
    regions_df.rename(columns={'RegionID': 'region_id', 'RegionName': 'region_name', 'Country': 'country',
                               'Code': 'code', 'Latitude': 'latitude', 'Longitude': 'longitude'}, inplace=True)

    # Convert dataframe to list of dictionaries
    regions_list = regions_df.to_dict('records')

    # Bulk create regions
    Region.objects.bulk_create([Region(**region) for region in regions_list])


class Migration(migrations.Migration):
    dependencies = [
        ('region', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_region_data),
    ]
