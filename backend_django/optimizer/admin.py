from django.contrib import admin

from .models import OptimizationJob


@admin.register(OptimizationJob)
class OptimizationJobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "status", "total_files", "processed_files", "created_at")
    list_filter = ("status",)
    readonly_fields = [f.name for f in OptimizationJob._meta.fields]
