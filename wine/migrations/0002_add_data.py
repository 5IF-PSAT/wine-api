from django.db import migrations
import pandas as pd


def fill_wine_data(apps, schema_editor):
    Winery = apps.get_model('winery', 'Winery')
    Region = apps.get_model('region', 'Region')
    Wine = apps.get_model('wine', 'Wine')

    # Read dataframe from parquet file
    wines_df = pd.read_csv('./db_data/wines.csv')

    # Rename columns to match model fields
    wines_df.rename(columns={'WineID': 'wine_id', 'WineName': 'wine_name', 'Type': 'type',
                             'Elaborate': 'elaborate', 'ABV': 'abv', 'Body': 'body',
                             'Acidity': 'acidity', 'WineryID': 'winery_id', 'RegionID': 'region_id'}, inplace=True)

    # Convert dataframe to list of dictionaries
    wines = wines_df.to_dict('records')

    # Get all wineries and regions
    wineries = Winery.objects.all()
    regions = Region.objects.all()

    # Create a dictionary of wineries and regions
    wineries_dict = {}
    regions_dict = {}

    for winery in wineries:
        wineries_dict[winery.winery_id] = winery
    for region in regions:
        regions_dict[region.region_id] = region

    # Create a list of wines to be created
    wines_to_create = []

    for wine in wines:
        # Get winery and region objects from the dictionary
        winery = wineries_dict[wine['winery_id']]
        region = regions_dict[wine['region_id']]

        # Create a wine object
        wine_obj = Wine(wine_id=wine['wine_id'], wine_name=wine['wine_name'], type=wine['type'],
                        elaborate=wine['elaborate'], abv=wine['abv'], body=wine['body'],
                        acidity=wine['acidity'], winery=winery, region=region)

        # Add wine object to the list
        wines_to_create.append(wine_obj)

    # Bulk create wines
    Wine.objects.bulk_create(wines_to_create)


class Migration(migrations.Migration):
    dependencies = [
        ('wine', '0001_initial'),
        ('region', '0002_add_data'),
        ('winery', '0002_add_data'),
    ]

    operations = [
        migrations.RunPython(fill_wine_data),
    ]
