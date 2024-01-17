from rest_framework import serializers
from wine.models import Wine
from winery.models import Winery
from region.models import Region


class WineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wine
        fields = ['id', 'wine_name', 'type', 'elaborate', 'abv',
                  'body', 'acidity', 'winery', 'region']
        read_only_fields = ('id',)

    def create(self, validated_data):
        Winery.objects.check_if_exists(validated_data["winery"])
        Region.objects.check_if_exists(validated_data["region"])
        return Wine.objects.create_wine(**validated_data)

    def update(self, instance, validated_data):
        instance = Wine.objects.update_wine(instance, **validated_data)
        return instance


class FilterWineSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)
    wine_name = serializers.CharField(max_length=255, required=False)
    type = serializers.CharField(max_length=255, required=False)
    elaborate = serializers.CharField(max_length=255, required=False)
    abv = serializers.FloatField(required=False)
    body = serializers.CharField(max_length=255, required=False)
    acidity = serializers.CharField(max_length=255, required=False)
    region_id = serializers.IntegerField(required=False)
    winery_id = serializers.IntegerField(required=False)