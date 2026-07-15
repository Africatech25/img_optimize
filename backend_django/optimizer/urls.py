from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health_check),
    path("formats", views.get_formats),
    path("video/formats", views.get_video_formats),
    path("optimize", views.start_optimization),
    path("progress/<uuid:job_id>", views.stream_progress),
    path("job/<uuid:job_id>", views.get_job_status),
    path("download/<uuid:job_id>", views.download_file),
    path("download/<uuid:job_id>/<str:filename>", views.download_single_file),
    path("download-zip/<uuid:job_id>", views.download_zip_only),
    path("cleanup/<uuid:job_id>", views.cleanup_job),
]
