from django.db import models
from wine_api.models import BaseEntity
from wine.managers import WineManager


class Wine(BaseEntity):
    class Meta:
        db_table = "wine"
        ordering = ["id"]

    wine_id = models.IntegerField(db_column="WineID", editable=False, unique=True, serialize=True)
    wine_name = models.CharField(max_length=255, db_column="WineName", serialize=True)
    type = models.CharField(max_length=255, db_column="Type", serialize=True)
    elaborate = models.CharField(max_length=255, db_column="Elaborate", serialize=True)
    abv = models.FloatField(db_column="ABV", serialize=True)
    body = models.CharField(max_length=255, db_column="Body", serialize=True)
    acidity = models.CharField(max_length=255, db_column="Acidity", serialize=True)
    winery = models.ForeignKey("winery.Winery", on_delete=models.SET_NULL, null=True, db_column="WineryID", serialize=True)
    region = models.ForeignKey("region.Region", on_delete=models.SET_NULL, null=True, db_column="RegionID", serialize=True)

    objects = WineManager()

    def __str__(self):
        return self.wine_name
