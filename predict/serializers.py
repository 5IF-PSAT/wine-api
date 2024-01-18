from rest_framework import serializers


class PredictSerializer(serializers.Serializer):
    timestamp = serializers.ListField(child=serializers.DateField())
    predict_field = serializers.CharField()
    predict_value = serializers.ListField(child=serializers.FloatField())


class RatingSerializer(serializers.Serializer):
    wine_id = serializers.IntegerField()
    batch_vintage = serializers.IntegerField()
    rating_year = serializers.IntegerField()
    predict_rating = serializers.FloatField()
