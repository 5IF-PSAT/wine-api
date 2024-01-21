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

    def get_wine_by_id(self, id):
        return self.filter(id=id).first()

    def get_wine_by_wine_id(self, wine_id):
        return self.filter(wine_id=wine_id).first()

    def get_wines(self, **data):
        """
        Returns all wines given page and page_size
        :param data:
        :return:
        """
        page = data.get("page", 1)
        page_size = data.get("page_size", 10)
        if page < 1:
            raise exceptions.ValidationError("Page must be greater than 0")
        if page_size < 1:
            raise exceptions.ValidationError("Page size must be greater than 0")
        offset = (page - 1) * page_size
        query = """
            SELECT wine.id, wine."WineID", wine.created_at, wine.updated_at, wine."WineName",
            wine."Type", wine."Elaborate", wine."ABV", wine."Body", wine."Acidity",
            region."RegionID", region."RegionName", winery."WineryID", winery."WineryName" 
            FROM wine JOIN winery ON wine."WineryID" = winery.id
            JOIN region ON wine."RegionID" = region.id
            ORDER BY wine.id ASC
            LIMIT %s OFFSET %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [page_size, offset])
            wines = cursor.fetchall()
        labels = ['id', 'wine_id', 'created_at', 'updated_at', 'wine_name',
                  'type', 'elaborate', 'abv', 'body', 'acidity',
                  'region', 'region_name', 'winery', 'winery_name']
        result = [dict(zip(labels, row)) for row in wines]
        return result


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

        query = """SELECT wine.id, wine."WineID", wine.created_at, wine.updated_at, wine."WineName",
                    wine."Type", wine."Elaborate", wine."ABV", wine."Body", wine."Acidity",
                  region."RegionID", region."RegionName", winery."WineryID", winery."WineryName" 
                  FROM wine JOIN winery ON wine."WineryID" = winery.id
                  JOIN region ON wine."RegionID" = region.id
                  WHERE """
        # Add parameters not None to list
        params = []
        if wine_name:
            query += "wine.\"WineName\" LIKE %s AND "
            params.append(f"%{wine_name}%")
        if type:
            query += "wine.\"Type\" = %s AND "
            params.append(type)
        if elaborate:
            query += "wine.\"Elaborate\" LIKE %s AND "
            params.append(f"%{elaborate}%")
        if abv:
            query += "wine.\"ABV\" = %s AND "
            params.append(abv)
        if body:
            query += "wine.\"Body\" = %s AND "
            params.append(body)
        if acidity:
            query += "wine.\"Acidity\" = %s AND "
            params.append(acidity)
        if winery_id:
            query += "wine.\"WineryID\" = %s AND "
            params.append(winery_id)
        if region_id:
            query += "wine.\"RegionID\" = %s AND "
            params.append(region_id)
        query += "1=1"
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            wines = cursor.fetchall()
        labels = ['id', 'wine_id', 'created_at', 'updated_at', 'wine_name',
                  'type', 'elaborate', 'abv', 'body', 'acidity',
                  'region_id', 'region_name', 'winery_id', 'winery_name']
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
