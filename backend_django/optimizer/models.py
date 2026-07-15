import uuid

from django.db import models


class OptimizationJob(models.Model):
    """Job d'optimisation/traitement (images et/ou vidéos), équivalent Django
    de la classe OptimizationJob en mémoire du backend FastAPI."""

    STATUS_CHOICES = [
        ("pending", "pending"),
        ("processing", "processing"),
        ("completed", "completed"),
        ("error", "error"),
    ]

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    total_files = models.IntegerField(default=0)
    processed_files = models.IntegerField(default=0)
    total_images = models.IntegerField(default=0)
    total_videos = models.IntegerField(default=0)

    progress = models.JSONField(default=list)
    stats = models.JSONField(default=dict)

    output_dir = models.CharField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)

    def add_progress(self, message: dict):
        self.progress.append(message)
        if message.get("type") in ("image_processed", "video_processed"):
            self.processed_files += 1
        if message.get("type") == "image_processed":
            self.stats["images"] = self.stats.get("images", 0) + 1
        if message.get("type") == "video_processed":
            self.stats["videos"] = self.stats.get("videos", 0) + 1
        self.save(update_fields=["progress", "processed_files", "stats"])

    def to_dict(self):
        stats = {
            "total_before": 0,
            "total_after": 0,
            "successful": 0,
            "errors": 0,
            "images": 0,
            "videos": 0,
            **self.stats,
        }
        reduction = 0
        if stats["total_before"] > 0:
            reduction = (1 - stats["total_after"] / stats["total_before"]) * 100

        return {
            "job_id": str(self.job_id),
            "status": self.status,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "total_images": self.total_images,
            "total_videos": self.total_videos,
            "stats": {**stats, "reduction_percent": round(reduction, 1)},
        }
