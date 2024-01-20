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
            name = data["region_name"]
            country = data["country"]
        except KeyError:
            raise exceptions.ValidationError("Missing required fields: region_name, country")

        region = self.create(region_id=data.get("region_id", None),  # region_id is optional
                             region_name=name, country=country,
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

    def filter_regions(self, **data):
        """
        Returns all regions matching the given filters
        :param data: dict
        :return:
        """
        region_name = data.get("region_name", None)
        country = data.get("country", None)
        radius = data.get("radius", None)
        latitude = data.get("latitude", None)
        longitude = data.get("longitude", None)

        if radius and (latitude is None or longitude is None):
            raise exceptions.ValidationError("Missing latitude or longitude")
        if latitude and longitude and radius is None:
            raise exceptions.ValidationError("Missing radius")

        query = """SELECT id, "RegionID", created_at, updated_at, "RegionName",
                    "Country", "Code", "Latitude", "Longitude" FROM region WHERE """
        # Add parameters not None to list
        params = []
        if region_name:
            query += "\"RegionName\" LIKE %s AND "
            params.append(f"%{region_name}%")
        if country:
            query += "\"Country\" LIKE %s AND "
            params.append(f"%{country}%")
        if radius and latitude and longitude:
            # Apply Haversine formula
            query += """(6371 * acos(cos(radians(%s)) * cos(radians("Latitude")) * cos(radians("Longitude") - 
            radians(%s)) + sin(radians(%s)) * sin(radians("Latitude")))) < %s AND """
            params.extend([latitude, longitude, latitude, radius])
        # If no parameters, add 1=1 to query to avoid error
        query += "1=1"

        # # Remove last AND
        # query = query[:-4]
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            regions = cursor.fetchall()
        labels = ["id", "region_id", "created_at", "updated_at",
                  "region_name", "country",
                  "code", "latitude", "longitude"]
        result = [dict(zip(labels, row)) for row in regions]
        return result

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