from django.urls import path

from accounts.admin_views import AdminUserDetailView, AdminUserListCreateView

from . import api_views

urlpatterns = [
    path("stats", api_views.AdminStatsView.as_view()),
    path("jobs", api_views.AdminJobListView.as_view()),
    path("jobs/<uuid:job_id>", api_views.AdminJobDetailView.as_view()),
    path("users", AdminUserListCreateView.as_view()),
    path("users/<int:pk>", AdminUserDetailView.as_view()),
]
