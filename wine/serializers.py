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
