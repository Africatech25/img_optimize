from rest_framework import serializers

from accounts.serializers import clean_free_text

from .models import Review


def display_name_for(user):
    return user.display_name or user.email.split("@")[0]


class PublicReviewSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["display_name", "rating", "text", "created_at"]

    def get_display_name(self, obj):
        return display_name_for(obj.user)


class MyReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "text", "status", "created_at", "updated_at"]


class ReviewWriteSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    text = serializers.CharField(max_length=500)

    class Meta:
        model = Review
        fields = ["rating", "text"]

    def validate_text(self, value):
        value = clean_free_text(value)
        if not value:
            raise serializers.ValidationError("Le texte de l'avis ne peut pas être vide.")
        return value
