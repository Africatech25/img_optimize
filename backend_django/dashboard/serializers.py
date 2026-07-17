from rest_framework import serializers

from optimizer.models import OptimizationJob
from reviews.models import Review


class AdminJobSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = OptimizationJob
        fields = [
            "job_id", "mode", "status", "user_email",
            "total_files", "processed_files", "total_images", "total_videos",
            "stats", "created_at",
        ]


class AdminJobDetailSerializer(AdminJobSerializer):
    class Meta(AdminJobSerializer.Meta):
        fields = AdminJobSerializer.Meta.fields + ["progress", "output_dir"]


class AdminReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_email", "display_name", "rating", "text", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "user_email", "display_name", "rating", "text", "created_at", "updated_at"]
