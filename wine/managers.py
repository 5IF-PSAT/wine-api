from django.db import models
from rest_framework import exceptions
from django.db import connection
import datetime


class WineManager(models.Manager):
    use_in_migrations = True

    def create_wine(self, **data):
        try:
            name = data["wine_name"]
            type = data["type"]
            winery = data["winery"]
            region = data["region"]
        except KeyError:
            raise exceptions.ValidationError("Missing required fields: wine_name, type, winery, region")
        wine = self.create(wine_id=data.get("wine_id", None),  # wine_id is optional
                           wine_name=name, type=type,
                           elaborate=data["elaborate"], abv=data["abv"], body=data["body"],
                           acidity=data["acidity"], winery=winery, region=region,
                           created_at=datetime.datetime.now())
        return wine

    def get_wines(self):
        return self.all()

    def get_wine_by_id(self, id):
        return self.filter(id=id).first()

    def get_wines_by_name(self, wine_name):
        """
        Returns all wines having wine_name in their name
        :param wine_name:
        :return:
        """
        return self.filter(wine_name__icontains=wine_name)

    def update_wine(self, wine, **data):
        wine.wine_name = data.get("wine_name", wine.wine_name)
        wine.type = data.get("type", wine.type)
        wine.elaborate = data.get("elaborate", wine.elaborate)
        wine.abv = data.get("abv", wine.abv)
        wine.body = data.get("body", wine.body)
        wine.acidity = data.get("acidity", wine.acidity)
        wine.winery = data.get("winery", wine.winery)
        wine.region = data.get("region", wine.region)
        wine.updated_at = datetime.datetime.now()
        wine.save()
        return wine

    def delete_wine(self, wine):
        wine.delete()
        return True
