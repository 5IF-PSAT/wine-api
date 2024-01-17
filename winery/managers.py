from django.db import models
from rest_framework import exceptions
from django.db import connection
import datetime


class WineryManager(models.Manager):
    use_in_migrations = True

    def check_if_exists(self, winery):
        if not self.filter(id=winery.id).exists():
            raise exceptions.ValidationError("Winery does not exist")

    def create_winery(self, **data):
        try:
            name = data["winery_name"]
        except KeyError:
            raise exceptions.ValidationError("Missing required fields: winery_name")

        winery = self.create(winery_id=data.get("winery_id", None),  # winery_id is optional
                             winery_name=name, website=data.get("website", ""),
                             created_at=datetime.datetime.now())
        return winery

    def get_wineries(self):
        return self.all()

    def get_winery_by_id(self, id):
        return self.filter(id=id).first()

    def get_wineries_by_name(self, winery_name):
        """
        Returns all wineries having winery_name in their name
        :param winery_name:
        :return:
        """
        return self.filter(winery_name__icontains=winery_name)

    def filter_wineries(self, **data):
        """
        Returns all wineries matching the given filters
        :param data: dict
        :return:
        """
        winery_name = data.get("winery_name", None)
        website = data.get("website", None)

        query = """SELECT id, created_at, updated_at, "WineryName", "Website" FROM winery WHERE """
        # Add parameters not None to list
        params = []
        if winery_name:
            query += "\"WineryName\" LIKE %s AND "
            params.append(f"%{winery_name}%")
        if website:
            query += "\"Website\" LIKE %s AND "
            params.append(f"%{website}%")
        query += "1 = 1"
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            wineries = cursor.fetchall()
        labels = ["id", "created_at", "updated_at", "winery_name", "website"]
        result = [dict(zip(labels, winery)) for winery in wineries]
        return result

    def update_winery(self, winery, **data):
        winery.winery_name = data.get("winery_name", winery.winery_name)
        winery.website = data.get("website", winery.website)
        winery.updated_at = datetime.datetime.now()
        winery.save()
        return winery

    def delete_winery(self, winery):
        winery.delete()
        return True
