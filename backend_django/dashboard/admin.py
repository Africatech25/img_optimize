from django.contrib import admin
from django.urls import path

from .views import stats_view

_original_get_urls = admin.site.get_urls


def _get_urls():
    custom_urls = [
        path("dashboard/", admin.site.admin_view(stats_view), name="dashboard"),
    ]
    return custom_urls + _original_get_urls()


admin.site.get_urls = _get_urls
