from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from optimizer.models import OptimizationJob

from .services import compute_dashboard_stats


@staff_member_required
def stats_view(request):
    context = {
        **compute_dashboard_stats(),
        "recent_jobs": OptimizationJob.objects.select_related("user").order_by("-created_at")[:20],
    }
    return render(request, "dashboard/stats.html", context)
