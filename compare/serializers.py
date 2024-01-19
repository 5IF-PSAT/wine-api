from rest_framework import serializers


class WineField(serializers.DictField):
    id = serializers.IntegerField()
    wine_id = serializers.IntegerField()
    vintage = serializers.IntegerField()
    distance = serializers.FloatField()
    wine_name = serializers.CharField()
    type = serializers.CharField()
    elaborate = serializers.CharField()
    abv = serializers.FloatField()
    body = serializers.CharField()
    acidity = serializers.CharField()
    winery = serializers.CharField()
    region = serializers.CharField()


class WineCompareSerializer(serializers.Serializer):
    ref_wine_id = serializers.IntegerField()
    ref_vintage = serializers.IntegerField()
    nb_wines = serializers.IntegerField()
    list_wines = serializers.ListField(
        child=WineField()
    )
