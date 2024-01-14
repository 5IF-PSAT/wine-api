from django.db import models
from wine_api.models import BaseEntity
from winery.managers import WineryManager


class Winery(BaseEntity):
    class Meta:
        db_table = "winery"
        ordering = ["id"]

    winery_id = models.IntegerField(db_column="WineryID", editable=False, unique=True, serialize=True)
    winery_name = models.CharField(max_length=255, db_column="WineryName", serialize=True)
    website = models.CharField(max_length=255, db_column="Website", serialize=True)
    objects = WineryManager()

    def __str__(self):
        return self.winery_name
