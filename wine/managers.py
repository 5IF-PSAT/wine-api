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

    def get_wine_by_wine_id(self, wine_id):
        return self.filter(wine_id=wine_id).first()

    def get_wines_by_name(self, wine_name):
        """
        Returns all wines having wine_name in their name
        :param wine_name:
        :return:
        """
        return self.filter(wine_name__icontains=wine_name)

    def filter_wines(self, **data):
        """
        Returns all wines matching the given filters
        :param data: dict
        :return:
        """
        wine_name = data.get("wine_name", None)
        type = data.get("type", None)
        elaborate = data.get("elaborate", None)
        abv = data.get("abv", None)
        body = data.get("body", None)
        acidity = data.get("acidity", None)
        winery_id = data.get("winery_id", None)
        region_id = data.get("region_id", None)

        query = """SELECT id, created_at, updated_at, "WineName",
                    "Type", "Elaborate", "ABV", "Body", "Acidity",
                  "RegionID", "WineryID" FROM wine WHERE """
        # Add parameters not None to list
        params = []
        if wine_name:
            query += "\"WineName\" LIKE %s AND "
            params.append(f"%{wine_name}%")
        if type:
            query += "\"Type\" = %s AND "
            params.append(type)
        if elaborate:
            query += "\"Elaborate\" LIKE %s AND "
            params.append(f"%{elaborate}%")
        if abv:
            query += "\"ABV\" = %s AND "
            params.append(abv)
        if body:
            query += "\"Body\" = %s AND "
            params.append(body)
        if acidity:
            query += "\"Acidity\" = %s AND "
            params.append(acidity)
        if winery_id:
            query += "\"WineryID\" = %s AND "
            params.append(winery_id)
        if region_id:
            query += "\"RegionID\" = %s AND "
            params.append(region_id)
        query += "1=1"
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            wines = cursor.fetchall()
        labels = ['id', 'created_at', 'updated_at', 'wine_name',
                  'type', 'elaborate', 'abv', 'body', 'acidity',
                  'region_id', 'winery_id']
        result = [dict(zip(labels, row)) for row in wines]
        return result

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
