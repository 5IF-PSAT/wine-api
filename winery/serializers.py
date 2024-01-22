from rest_framework import serializers
from winery.models import Winery


class WinerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Winery
        fields = ['id', 'winery_id', 'winery_name', 'website']
        read_only_fields = ('id', 'winery_id',)

    def create(self, validated_data):
        return Winery.objects.create_winery(**validated_data)

    def update(self, instance, validated_data):
        instance = Winery.objects.update_winery(instance, **validated_data)
        return instance


class SecondWinerySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    winery_id = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)
    winery_name = serializers.CharField(max_length=255, required=False)
    website = serializers.CharField(max_length=255, required=False)


class FilterWinerySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    winery_id = serializers.IntegerField(required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)
    winery_name = serializers.CharField(max_length=255, required=False)
    website = serializers.CharField(max_length=255, required=False)