import shutil
from pathlib import Path

from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from optimizer.models import OptimizationJob
from reviews.models import Review

from .serializers import AdminJobDetailSerializer, AdminJobSerializer, AdminReviewSerializer
from .services import compute_dashboard_stats


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(compute_dashboard_stats())


class AdminJobListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminJobSerializer

    def get_queryset(self):
        qs = OptimizationJob.objects.select_related("user").order_by("-created_at")
        params = self.request.query_params

        status_filter = params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        mode_filter = params.get("mode")
        if mode_filter:
            qs = qs.filter(mode=mode_filter)

        q = params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(user__email__icontains=q) | Q(job_id__icontains=q))

        return qs


class AdminJobDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminJobDetailSerializer
    queryset = OptimizationJob.objects.select_related("user")
    lookup_field = "job_id"

    def perform_destroy(self, instance):
        output_dir = Path(instance.output_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        instance.delete()


class AdminReviewListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminReviewSerializer

    def get_queryset(self):
        qs = Review.objects.select_related("user").order_by("-created_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AdminReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminReviewSerializer
    queryset = Review.objects.select_related("user")
