from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from optimizer.models import OptimizationJob

User = get_user_model()


def compute_dashboard_stats() -> dict:
    now = timezone.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    jobs = OptimizationJob.objects.all()

    status_counts = {
        row["status"]: row["count"]
        for row in jobs.values("status").annotate(count=Count("job_id"))
    }
    mode_counts = {
        row["mode"]: row["count"]
        for row in jobs.values("mode").annotate(count=Count("job_id"))
    }

    completed_jobs = jobs.filter(status="completed")
    total_before = 0
    total_after = 0
    total_successful = 0
    total_errors = 0
    for job in completed_jobs.only("stats"):
        total_before += job.stats.get("total_before", 0)
        total_after += job.stats.get("total_after", 0)
        total_successful += job.stats.get("successful", 0)
        total_errors += job.stats.get("errors", 0)

    reduction_percent = 0
    if total_before > 0:
        reduction_percent = round((1 - total_after / total_before) * 100, 1)

    # Provenance des inscriptions (captée une fois, à l'inscription — cf.
    # décision produit : pas de tracking par requête).
    country_counts = {
        row["signup_country"]: row["count"]
        for row in User.objects.exclude(signup_country="")
        .values("signup_country").annotate(count=Count("id")).order_by("-count")[:10]
    }
    referrer_counts = {
        row["signup_referrer_domain"]: row["count"]
        for row in User.objects.exclude(signup_referrer_domain="")
        .values("signup_referrer_domain").annotate(count=Count("id")).order_by("-count")[:10]
    }
    utm_source_counts = {
        row["signup_utm_source"]: row["count"]
        for row in User.objects.exclude(signup_utm_source="")
        .values("signup_utm_source").annotate(count=Count("id")).order_by("-count")[:10]
    }

    return {
        "total_users": User.objects.count(),
        "new_users_7d": User.objects.filter(date_joined__gte=last_7_days).count(),
        "new_users_30d": User.objects.filter(date_joined__gte=last_30_days).count(),

        "total_jobs": jobs.count(),
        "jobs_7d": jobs.filter(created_at__gte=last_7_days).count(),
        "status_counts": status_counts,
        "mode_counts": mode_counts,

        "total_files_processed": total_successful,
        "total_files_errors": total_errors,
        "total_bytes_before": total_before,
        "total_bytes_after": total_after,
        "bytes_saved": total_before - total_after,
        "reduction_percent": reduction_percent,

        "country_counts": country_counts,
        "referrer_counts": referrer_counts,
        "utm_source_counts": utm_source_counts,
    }
