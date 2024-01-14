from rest_framework import serializers
from region.models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
        read_only_fields = ('id',)

    def create(self, validated_data):
        return Region.objects.create_region(**validated_data)

    def update(self, instance, validated_data):
        instance = Region.objects.update_region(instance, **validated_data)
        return instance
