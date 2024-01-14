from django.db import models
from rest_framework import exceptions
from django.db import connection
import datetime


class RegionManager(models.Manager):
    use_in_migrations = True

    def check_if_exists(self, region):
        if not self.filter(id=region.id).exists():
            raise exceptions.ValidationError("Region does not exist")

    def create_region(self, **data):
        try:
            region_id = data["region_id"]
            name = data["region_name"]
            country = data["country"]
        except KeyError:
            raise exceptions.ValidationError("Missing required fields: region_id, region_name, country")
        if self.filter(region_id=region_id).exists():
            raise exceptions.ValidationError("Region already exists")

        region = self.create(region_id=region_id, region_name=name, country=country,
                             code=data["code"], latitude=data["latitude"], longitude=data["longitude"],
                             created_at=datetime.datetime.now())
        return region

    def get_regions(self):
        return self.all()

    def get_region_by_id(self, id):
        return self.filter(id=id).first()

    def get_regions_by_name(self, region_name):
        """
        Returns all regions having region_name in their name
        :param region_name:
        :return:
        """
        return self.filter(region_name__icontains=region_name)

    def update_region(self, region, **data):
        region.region_name = data.get("region_name", region.region_name)
        region.country = data.get("country", region.country)
        region.code = data.get("code", region.code)
        region.latitude = data.get("latitude", region.latitude)
        region.longitude = data.get("longitude", region.longitude)
        region.updated_at = datetime.datetime.now()
        region.save()
        return region

    def delete_region(self, region):
        region.delete()
        return True