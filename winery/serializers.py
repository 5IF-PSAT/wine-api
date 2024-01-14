from rest_framework import serializers
from winery.models import Winery


class WinerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Winery
        fields = '__all__'
        read_only_fields = ('id',)

    def create(self, validated_data):
        return Winery.objects.create_winery(**validated_data)

    def update(self, instance, validated_data):
        instance = Winery.objects.update_winery(instance, **validated_data)
        return instance
