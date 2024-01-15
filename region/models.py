from django.db import models
from wine_api.models import BaseEntity
from region.managers import RegionManager


class Region(BaseEntity):
    class Meta:
        db_table = "region"
        ordering = ["id"]

    region_id = models.IntegerField(db_column="RegionID", null=True)
    region_name = models.CharField(max_length=255, db_column="RegionName", serialize=True)
    country = models.CharField(max_length=255, db_column="Country", serialize=True)
    code = models.CharField(max_length=255, db_column="Code", serialize=True)
    latitude = models.FloatField(db_column="Latitude", serialize=True)
    longitude = models.FloatField(db_column="Longitude", serialize=True)

    objects = RegionManager()

    def __str__(self):
        return self.region_name
