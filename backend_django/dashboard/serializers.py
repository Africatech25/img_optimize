from rest_framework import serializers

from optimizer.models import OptimizationJob


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
