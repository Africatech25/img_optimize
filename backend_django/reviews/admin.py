from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "rating", "status", "created_at"]
    list_filter = ["status", "rating"]
    search_fields = ["user__email", "text"]
