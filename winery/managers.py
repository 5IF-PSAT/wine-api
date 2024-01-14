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
            winery_id = data["winery_id"]
            name = data["winery_name"]
        except KeyError:
            raise exceptions.ValidationError("Missing required fields: winery_id, winery_name")

        if self.filter(winery_id=winery_id).exists():
            raise exceptions.ValidationError("Winery already exists")

        winery = self.create(winery_id=winery_id, winery_name=name, website=data.get("website", ""),
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

    def update_winery(self, winery, **data):
        winery.winery_name = data.get("winery_name", winery.winery_name)
        winery.website = data.get("website", winery.website)
        winery.updated_at = datetime.datetime.now()
        winery.save()
        return winery

    def delete_winery(self, winery):
        winery.delete()
        return True
