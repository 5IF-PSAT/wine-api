from rest_framework import serializers
from region.models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'region_name', 'country', 'code', 'latitude', 'longitude']
        read_only_fields = ('id',)

    def create(self, validated_data):
        return Region.objects.create_region(**validated_data)

    def update(self, instance, validated_data):
        instance = Region.objects.update_region(instance, **validated_data)
        return instance


class FilterRegionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)
    region_name = serializers.CharField(max_length=255, required=False)
    country = serializers.CharField(max_length=255, required=False)
    code = serializers.CharField(max_length=255, required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)